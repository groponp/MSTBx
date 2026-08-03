"""Testes de integração curta para as combinações de comandos disponíveis."""

from pathlib import Path

from click.testing import CliRunner

from mstbx.cli import cli


class FakeProtocol:
    """Chef fake que registra as etapas NAMD/SMD/metadinâmica."""

    calls = []

    def __init__(self, *args, **kwargs):
        self.calls.append(("init", kwargs))

    def __getattr__(self, name):
        def method(*args, **kwargs):
            self.calls.append((name, kwargs))
        return method


def _inputs(tmp_path):
    psf = tmp_path / "system.psf"
    pdb = tmp_path / "system.pdb"
    psf.write_text("       2 !NATOM\n")
    pdb.write_text("END\n")
    return psf, pdb


def test_md_inputs_namd_solution_and_membrane_dispatch(tmp_path, monkeypatch):
    """Both NAMD environments dispatch their complete protocol sequence."""
    psf, pdb = _inputs(tmp_path)
    import mstbx.commands.md_inputs as command

    FakeProtocol.calls = []
    monkeypatch.setattr(command, "MDProtocolSol", FakeProtocol)
    monkeypatch.setattr(command, "MDProtocolMemb", FakeProtocol)
    monkeypatch.setattr(command.os, "system", lambda command: 0)
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    # --runs-dir only applies to --engine gromacs; NAMD always writes into
    # 01build/02nvt/... under the current directory.
    solution = runner.invoke(
        cli,
        ["md-inputs", "--env", "solution", "--psf", str(psf), "--pdb", str(pdb)],
    )
    membrane = runner.invoke(
        cli,
        ["md-inputs", "--env", "membrane", "--psf", str(psf), "--pdb", str(pdb)],
    )

    assert solution.exit_code == 0, solution.output
    assert membrane.exit_code == 0, membrane.output
    names = [name for name, _ in FakeProtocol.calls]
    assert names.count("nvt") == 2
    assert names.count("runner_script") == 2
    assert names.count("npt1") == 1
    assert names.count("npt2") == 1


def test_smd_and_metadynamics_dispatch_all_writers(tmp_path, monkeypatch):
    """SMD and WTMetaD invoke their protocol-specific writers in order."""
    psf, pdb = _inputs(tmp_path)
    import mstbx.commands.smd_inputs as smd_command
    import mstbx.commands.metad_inputs as meta_command

    FakeProtocol.calls = []
    monkeypatch.setattr(smd_command, "MDProtocolSol", FakeProtocol)
    monkeypatch.setattr(smd_command, "SMDProtocolSol", FakeProtocol)
    monkeypatch.setattr(meta_command, "MDProtocolSol", FakeProtocol)
    monkeypatch.setattr(meta_command, "WTMetaDProtocolSol", FakeProtocol)
    monkeypatch.setattr(smd_command.os, "system", lambda command: 0)
    monkeypatch.setattr(meta_command.os, "system", lambda command: 0)

    runner = CliRunner()
    smd = runner.invoke(
        cli,
        ["smd-inputs", "--psf", str(psf), "--pdb", str(pdb), "--selpull", "name CA",
         "--selanchor", "name N", "--target-center", "5", "--velocity", "10", "--colvar-input", str(tmp_path)],
    )
    meta = runner.invoke(
        cli,
        ["metad-inputs", "--psf", str(psf), "--pdb", str(pdb), "--sel1", "name CA", "--sel2", "name N"],
    )

    assert smd.exit_code == 0, smd.output
    assert meta.exit_code == 0, meta.output
    names = [name for name, _ in FakeProtocol.calls]
    assert "smd" in names and "wtmetad" in names
    assert "runner_script" in names


def test_mkdocking_and_colabfold_dispatch_without_external_container(tmp_path, monkeypatch):
    """Docking and ColabFold commands pass inputs to their service objects."""
    protein = tmp_path / "protein.pdb"
    ligand = tmp_path / "ligand.pdb"
    fasta = tmp_path / "input.fasta"
    protein.write_text("END\n")
    ligand.write_text("END\n")
    fasta.write_text(">test\nAAAA\n")
    import mstbx.commands.mkdocking_cmplx as dock_command
    import mstbx.commands.colabfold as fold_command

    class FakeBuilder:
        seen = None

        def __init__(self, protein_pdb, output_name):
            self.seen = (protein_pdb, output_name)
            FakeBuilder.seen = self.seen

        def build(self, ligand_input, ligand_pH, is_pdbqt):
            FakeBuilder.seen += (ligand_input, ligand_pH, is_pdbqt)
            return True

    class FakeContainer:
        calls = []

        def __init__(self, **kwargs):
            self.calls.append(("init", kwargs))

        def run(self, **kwargs):
            self.calls.append(("run", kwargs))
            return True

        def cleanup(self):
            self.calls.append(("cleanup", {}))

    monkeypatch.setattr(dock_command, "ComplexBuilder", FakeBuilder)
    monkeypatch.setattr(fold_command, "ApptainerManager", FakeContainer)
    result = CliRunner().invoke(
        cli,
        ["mkdocking-cmplx", "--protein", str(protein), "--ligand-pdb", str(ligand), "--output", "complex.pdb"],
    )
    fold = CliRunner().invoke(cli, ["colabfold", "--input-dir", str(tmp_path), "--output-dir", str(tmp_path / "out")])

    assert result.exit_code == 0, result.output
    assert fold.exit_code == 0, fold.output
    assert FakeBuilder.seen[-1] is False
    assert any(name == "run" for name, _ in FakeContainer.calls)


def test_mkdocking_rejects_ambiguous_or_missing_ligand_source(tmp_path):
    """Docking requires exactly one ligand source."""
    protein = tmp_path / "protein.pdb"
    ligand = tmp_path / "ligand.pdb"
    dock = tmp_path / "pose.pdbqt"
    for path in [protein, ligand, dock]:
        path.write_text("END\n")

    runner = CliRunner()
    missing = runner.invoke(cli, ["mkdocking-cmplx", "--protein", str(protein), "--output", "complex.pdb"])
    both = runner.invoke(
        cli,
        ["mkdocking-cmplx", "--protein", str(protein), "--dock", str(dock), "--ligand-pdb", str(ligand), "--output", "complex.pdb"],
    )

    assert missing.exit_code != 0
    assert "Either --dock or --ligand-pdb" in missing.output
    assert both.exit_code != 0
    assert "only one ligand source" in both.output


def test_resetpsf_and_md_translate_generate_external_scripts(tmp_path, monkeypatch):
    """VMD-backed commands create and clean their temporary TCL scripts."""
    psf, pdb = _inputs(tmp_path)
    coor = tmp_path / "system.coor"
    xsc = tmp_path / "system.xsc"
    toppar = tmp_path / "toppar"
    coor.write_text("coordinates\n")
    xsc.write_text("cellBasisVector1 1 0 0\n")
    toppar.mkdir()
    import mstbx.commands.resetpsf as reset_command
    import mstbx.commands.md_translate as translate_command

    def fake_vmd(command, **kwargs):
        if command[0] == "vmd":
            Path("reset.psf").write_text("       2 !NATOM\n")
            Path("reset.pdb").write_text("END\n")
        return object()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(reset_command.subprocess, "run", fake_vmd)
    reset = CliRunner().invoke(cli, ["resetpsf", "--psf", str(psf), "--pdb", str(pdb)])

    monkeypatch.setattr(translate_command.os, "system", lambda command: 0)
    translate = CliRunner().invoke(
        cli,
        ["md-translate", "--psf", str(psf), "--coor", str(coor), "--xsc", str(xsc), "--toppar-dir", str(toppar)],
    )

    assert reset.exit_code == 0, reset.output
    assert translate.exit_code == 0, translate.output
    assert (tmp_path / "reset.psf").exists()
    assert (tmp_path / "translated_gmx").is_dir()
    assert not (tmp_path / "resetpsf_run.tcl").exists()
    assert not (tmp_path / "translate.tcl").exists()


def test_resetpsf_fails_on_atom_count_mismatch(tmp_path, monkeypatch):
    """A silent atom-count mismatch is exactly the data loss resetpsf exists
    to catch; it must not exit 0."""
    psf, pdb = _inputs(tmp_path)
    import mstbx.commands.resetpsf as reset_command

    def fake_vmd(command, **kwargs):
        Path("reset.psf").write_text("       1 !NATOM\n")  # input had 2
        Path("reset.pdb").write_text("END\n")
        return object()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(reset_command.subprocess, "run", fake_vmd)
    result = CliRunner().invoke(cli, ["resetpsf", "--psf", str(psf), "--pdb", str(pdb)])

    assert result.exit_code != 0
    assert "Error de consistencia" in result.output
    assert "Traceback" not in result.output


def test_resetpsf_fails_when_vmd_errors(tmp_path, monkeypatch):
    psf, pdb = _inputs(tmp_path)
    import mstbx.commands.resetpsf as reset_command
    import subprocess

    def fake_vmd(command, **kwargs):
        raise subprocess.CalledProcessError(1, command, output="boom")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(reset_command.subprocess, "run", fake_vmd)
    result = CliRunner().invoke(cli, ["resetpsf", "--psf", str(psf), "--pdb", str(pdb)])

    assert result.exit_code != 0
    assert "Traceback" not in result.output


def test_md_translate_fails_when_vmd_exits_nonzero(tmp_path, monkeypatch):
    psf, pdb = _inputs(tmp_path)
    coor = tmp_path / "system.coor"
    xsc = tmp_path / "system.xsc"
    toppar = tmp_path / "toppar"
    coor.write_text("coordinates\n")
    xsc.write_text("cellBasisVector1 1 0 0\n")
    toppar.mkdir()
    import mstbx.commands.md_translate as translate_command

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(translate_command.os, "system", lambda command: 256)
    result = CliRunner().invoke(
        cli,
        ["md-translate", "--psf", str(psf), "--coor", str(coor), "--xsc", str(xsc), "--toppar-dir", str(toppar)],
    )

    assert result.exit_code != 0
    assert "Traceback" not in result.output


def test_smd_and_metad_inputs_reject_non_namd_engine(tmp_path):
    """The 'not yet implemented' branches must fail, not just log and exit 0."""
    psf, pdb = _inputs(tmp_path)
    smd = CliRunner().invoke(
        cli,
        ["smd-inputs", "--engine", "gromacs", "--psf", str(psf), "--pdb", str(pdb),
         "--selpull", "name CA", "--selanchor", "name N", "--target-center", "5"],
    )
    metad = CliRunner().invoke(
        cli,
        ["metad-inputs", "--engine", "gromacs", "--psf", str(psf), "--pdb", str(pdb),
         "--sel1", "segid PROA", "--sel2", "segid PROB"],
    )

    assert smd.exit_code != 0
    assert "not yet implemented" in smd.output
    assert "Traceback" not in smd.output
    assert metad.exit_code != 0
    assert "not yet implemented" in metad.output
    assert "Traceback" not in metad.output


def test_colabfold_fails_when_no_fasta_files_found(tmp_path):
    empty_input = tmp_path / "in"
    empty_input.mkdir()
    result = CliRunner().invoke(
        cli,
        ["colabfold", "--input-dir", str(empty_input), "--output-dir", str(tmp_path / "out")],
    )

    assert result.exit_code != 0
    assert "No FASTA files found" in result.output


def test_openmm_mk_inp_dispatches_generator(monkeypatch):
    """OpenMM template mode is testable without importing a GPU platform."""
    import mstbx.commands.openmm_run as command
    called = []
    monkeypatch.setattr(command, "generate_default_inps", lambda: called.append(True))

    result = CliRunner().invoke(cli, ["openmm-run", "--mk-inp"])

    assert result.exit_code == 0, result.output
    assert called == [True]


def test_topogmx_forwards_protein_only_and_ligand_combinations(tmp_path, monkeypatch):
    """The topology command builds both supported input modes."""
    protein = tmp_path / "protein.pdb"
    mol2 = tmp_path / "ligand.mol2"
    string = tmp_path / "ligand.str"
    protein.write_text("END\n")
    mol2.write_text("MOL2\n")
    string.write_text("RESI LIG 0.0\n")
    import mstbx.commands.topogmx as command

    seen = []

    class FakeBuilder:
        def __init__(self, config):
            seen.append(config)

        def build_system(self):
            return None

    monkeypatch.setattr(command, "GromacsBuilder", FakeBuilder)
    runner = CliRunner()
    protein_only = runner.invoke(
        cli,
        ["topogmx", "--protein", str(protein), "--output-dir", str(tmp_path / "protein")],
    )
    with_ligand = runner.invoke(
        cli,
        ["topogmx", "--protein", str(protein), "--ligand-mol2", str(mol2), "--ligand-str", str(string),
         "--ligand-resname", "LIG", "--pdb2gmx-protonation", "--output-dir", str(tmp_path / "ligand")],
    )

    assert protein_only.exit_code == 0, protein_only.output
    assert with_ligand.exit_code == 0, with_ligand.output
    assert seen[0].ligand_mol2 is None
    assert seen[1].ligand_mol2 == mol2
    assert seen[1].ligand_str == string
    assert seen[1].pdb2gmx_protonation is True


def test_md_inputs_gromacs_forwards_defaults_and_custom_selections(tmp_path, monkeypatch):
    """The GROMACS branch forwards natural selections and custom restraint force."""
    import mstbx.commands.md_inputs as command

    calls = []

    class FakeProtocol:
        def __init__(self, config):
            calls.append(("protocol", config))

        def write_all(self):
            calls.append(("protocol_write", None))

    class FakeIndex:
        def __init__(self, runs, groups):
            calls.append(("index", runs, groups))

        def write_all(self):
            calls.append(("index_write", None))

    class FakeRestraints:
        def __init__(self, config):
            calls.append(("restraint", config))

        def apply_all(self):
            calls.append(("restraint_apply", None))
            return 10, 5

    class FakeRunner:
        def __init__(self, runs, gmx):
            calls.append(("runner", runs, gmx))

        def write_all(self):
            calls.append(("runner_write", None))

    monkeypatch.setattr(command, "GromacsProtocol", FakeProtocol)
    monkeypatch.setattr(command, "GromacsIndex", FakeIndex)
    monkeypatch.setattr(command, "GromacsRestraints", FakeRestraints)
    monkeypatch.setattr(command, "GromacsRunner", FakeRunner)
    result = CliRunner().invoke(
        cli,
        ["md-inputs", "--engine", "gromacs", "--env", "solution", "--runs-dir", str(tmp_path / "runs"),
         "--select-group-index-1", "protein or resname LIG", "--select-group-index-2", "not (protein or resname LIG)",
         "--select-atoms-to-restraint", "protein and backbone or resname LIG and not name H*", "--force", "2092", "--gmx", "gmx"],
    )

    assert result.exit_code == 0, result.output
    restraint = next(item[1] for item in calls if item[0] == "restraint")
    assert restraint.force == 2092
    groups = next(item[2] for item in calls if item[0] == "index")
    assert groups[0].selection == "protein or resname LIG"
    assert groups[1].selection == "not (protein or resname LIG)"


def test_md_inputs_rejects_gromacs_flags_under_namd(tmp_path):
    """GROMACS-only flags are never read by the NAMD branch; the CLI must
    reject them instead of accepting and silently dropping them."""
    psf = tmp_path / "system.psf"
    pdb = tmp_path / "system.pdb"
    psf.write_text("       2 !NATOM\n")
    pdb.write_text("END\n")

    result = CliRunner().invoke(
        cli,
        ["md-inputs", "--engine", "namd", "--env", "solution", "--psf", str(psf), "--pdb", str(pdb),
         "--force", "2092"],
    )

    assert result.exit_code != 0
    assert "--force" in result.output
    assert "--engine gromacs" in result.output


def test_md_inputs_rejects_namd_flags_under_gromacs(tmp_path):
    """--lparm is only ever copied on the NAMD path; passing it under
    --engine gromacs used to succeed and do nothing."""
    result = CliRunner().invoke(
        cli,
        ["md-inputs", "--engine", "gromacs", "--env", "solution",
         "--runs-dir", str(tmp_path / "runs"), "--dcdfreq", "20.0"],
    )

    assert result.exit_code != 0
    assert "--dcdfreq" in result.output
    assert "--engine namd" in result.output
