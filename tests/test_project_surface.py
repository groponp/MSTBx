"""Project-wide unit, regression, and adversarial coverage.

These tests deliberately avoid launching VMD, GROMACS, NAMD, Apptainer, or
OpenMM simulations. They verify command contracts, generated inputs, pure
conversions, and failure behavior for every currently registered workflow.
"""

from pathlib import Path

import pytest
from click.testing import CliRunner

from mstbx.cli import cli
from mstbx.core.Build.PSFGenMemb import BuildMembrane
from mstbx.core.Build.PSFGenSol import BuildSolution
from mstbx.core.Docking.ComplexBuilder import ComplexBuilder
from mstbx.core.MDProtocols.MDMembProtocol import MDProtocolMemb
from mstbx.core.MDProtocols.MDSolProtocol import MDProtocolSol, SMDProtocolSol, WTMetaDProtocolSol
from mstbx.core.MDProtocols.OpenMMRunner import read_inputs
from mstbx.core.Utils.Apptainer import ApptainerManager
from mstbx.core.Utils.Validator import FormatValidator
from mstbx.commands.resetpsf import get_psf_natoms


def _pdb_line(record="ATOM  ", serial=1, resname="ALA", atom="CA", chain="A", resid=1):
    """Return one valid fixed-width PDB coordinate record."""
    return f"{record}{serial:5d} {atom:^4s} {resname:>3s} {chain}{resid:4d}    {1.0:8.3f}{2.0:8.3f}{3.0:8.3f}{1.00:6.2f}{20.0:6.2f}          C  \n"


def test_every_registered_command_exposes_help():
    """All public CLI workflows are discoverable without external engines."""
    expected = {
        "topopsfgen", "topogmx", "topotleap", "md-inputs", "smd-inputs",
        "metad-inputs", "pdbwriter", "colabfold", "mkdocking-cmplx",
        "md-translate", "resetpsf", "openmm-run",
    }
    assert set(cli.commands) == expected
    runner = CliRunner()
    for name in expected:
        result = runner.invoke(cli, [name, "--help"])
        assert result.exit_code == 0, f"{name}: {result.output}"
        assert "Options:" in result.output or "Commands:" in result.output


def test_format_validator_covers_supported_formats(tmp_path):
    """Regression coverage for PDB, PSF, CRD, and MOL2 validators."""
    pdb = tmp_path / "system.pdb"
    pdb.write_text(_pdb_line())
    psf = tmp_path / "system.psf"
    psf.write_text("PSF\n\n       1 !NATOM\n       1 SEG 1 ALA CA CT1 0.000000 12.0000 0\n       0 !NBOND\n")
    crd = tmp_path / "system.crd"
    crd.write_text("       1  EXT\n" + " " * 99 + "1\n")
    mol2 = tmp_path / "ligand.mol2"
    mol2.write_text(
        "@<TRIPOS>MOLECULE\nLIG\n 1 0 1 0 0\nSMALL\nGASTEIGER\n"
        "@<TRIPOS>ATOM\n"
        "      1 C1 1.0 2.0 3.0 C.3 1 LIG 0.0\n"
        "@<TRIPOS>BOND\n"
    )

    for path in [pdb, psf, crd, mol2]:
        valid, report = FormatValidator.validate(path)
        assert valid, (path, report)


def test_format_validator_rejects_malformed_and_unknown_inputs(tmp_path):
    """Adversarial files fail with a useful report instead of being accepted."""
    bad_pdb = tmp_path / "bad.pdb"
    bad_pdb.write_text("ATOM\n")
    unknown = tmp_path / "system.xyz"
    unknown.write_text("coordinates\n")

    assert FormatValidator.validate(bad_pdb)[0] is False
    valid, report = FormatValidator.validate(unknown)
    assert not valid
    assert "Unsupported file extension" in report
    assert FormatValidator.validate(tmp_path / "missing.pdb")[0] is False


def test_namd_solution_protocol_regression(tmp_path, monkeypatch):
    """NAMD solution inputs preserve the validated 2 fs time conversion."""
    for directory in ["02nvt", "03npt", "04md"]:
        (tmp_path / directory).mkdir()
    monkeypatch.chdir(tmp_path)
    protocol = MDProtocolSol("system.psf", "system.pdb", 310, 1.0, 50.0)

    assert protocol.dcdfreq == 25000
    assert protocol.mdsteps == 500000
    protocol.nvt()
    protocol.npt()
    protocol.md()

    assert "run 1000000" in (tmp_path / "02nvt/nvt.confg").read_text()
    assert "run 2500000" in (tmp_path / "03npt/npt.confg").read_text()
    md_text = (tmp_path / "04md/md.confg").read_text()
    assert "set totaltime   500000" in md_text
    assert "run                     $currenttime" in md_text


def test_namd_membrane_protocol_and_special_protocol_times():
    """Membrane, SMD, and metadynamics constructors retain ns semantics."""
    membrane = MDProtocolMemb("system.psf", "system.pdb", 310, 2.0, 20.0)
    smd = SMDProtocolSol("system.psf", "system.pdb", 310, 100, "resname LIG", "protein", 50.0, velocity=5.0)
    metad = WTMetaDProtocolSol("system.psf", "system.pdb", 310, 2.0, biasT=15.0)

    assert membrane.dcdfreq == 10000
    assert membrane.mdsteps == 1000000
    assert smd.mdtime == pytest.approx(10.0)
    assert smd.mdsteps == 5000000
    assert metad.mdsteps == 1000000
    assert metad.biasTemperature == 4340


def test_openmm_input_parser_regression_and_adversarial_values(tmp_path):
    """OpenMM protocol files parse supported values and ignore comments."""
    inputs = tmp_path / "prod.inp"
    inputs.write_text(
        "NSTEP = 5000 # production steps\n"
        "GEN_VEL = yes\n"
        "P_REF = 1.0, 1.0, 0.0\n"
        "P_SCALE = XY\n"
        "REST_ATOM = 'protein and name CA'\n"
        "REST_K = 5.0\n"
    )
    parsed = read_inputs(inputs)

    assert parsed.nstep == 5000
    assert parsed.gen_vel == "yes"
    assert parsed.p_ref == (1.0, 1.0, 0.0)
    assert parsed.p_scale == (True, True, False)
    assert parsed.rest_atom == "protein and name CA"
    assert parsed.rest_k == 5.0


def test_docking_ligand_normalization_is_deterministic(tmp_path):
    """Docking preparation normalizes record type, chain, residue, and resid."""
    import MDAnalysis as mda

    ligand = tmp_path / "ligand.pdb"
    ligand.write_text(_pdb_line(record="HETATM", resname="UNK", atom="C1", chain="X", resid=9))
    universe = mda.Universe(ligand)
    ComplexBuilder(tmp_path / "protein.pdb", tmp_path / "complex.pdb").prepare_ligand(universe)

    assert set(universe.atoms.record_types) == {"HETATM"}
    assert set(universe.residues.resnames) == {"LIG"}
    assert set(universe.residues.resids) == {1}


def test_cli_rejects_invalid_gromacs_environment():
    """Adversarial CLI input cannot silently select unsupported GROMACS modes."""
    result = CliRunner().invoke(
        cli,
        ["md-inputs", "--engine", "gromacs", "--env", "membrane"],
    )
    assert result.exit_code == 0
    assert "supports only" in result.output


def test_psf_generators_preserve_box_defaults_and_user_overrides(tmp_path, monkeypatch):
    """Generated TCL records solution and membrane geometry decisions."""
    monkeypatch.chdir(tmp_path)
    BuildSolution().build("input.psf", "input.pdb", 0.15, "sol", 0)
    solution = (tmp_path / "PSFGenSol.tcl").read_text()
    assert "set p 18.0" in solution
    assert "STRICT CUBIC" in solution

    BuildSolution().build("input.psf", "input.pdb", 0.15, "sol", 0, padding=20.0, pad_z_pos=30.0)
    solution = (tmp_path / "PSFGenSol.tcl").read_text()
    assert "set p 20.0" in solution
    assert "set maxz" in solution

    BuildMembrane().build("input.psf", "input.pdb", 0.15, "mem", 0, 0, 10.0)
    membrane = (tmp_path / "PSFGenMemb.tcl").read_text()
    assert "set padding 25.0" in membrane
    assert "STRICT XY SQUARE" in membrane


def test_resetpsf_parser_and_apptainer_command(tmp_path, monkeypatch):
    """Utility modules handle valid PSF metadata and deterministic commands."""
    psf = tmp_path / "system.psf"
    psf.write_text("PSF\n       42 !NATOM\n")
    assert get_psf_natoms(psf) == 42
    assert get_psf_natoms(tmp_path / "missing.psf") is None

    manager = ApptainerManager("tool.sif")
    commands = []
    monkeypatch.setattr(manager, "ensure_sif", lambda: True)
    monkeypatch.setattr("mstbx.core.Utils.Apptainer.os.system", lambda command: commands.append(command) or 0)
    assert manager.run("tool --help", binds={"/tmp/input": "/input"})
    assert "apptainer run" in commands[0]
    assert "-B /tmp/input:/input" in commands[0]
