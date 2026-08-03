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
    runner = CliRunner()

    solution = runner.invoke(
        cli,
        ["md-inputs", "--env", "solution", "--psf", str(psf), "--pdb", str(pdb), "--runs-dir", str(tmp_path / "s")],
    )
    membrane = runner.invoke(
        cli,
        ["md-inputs", "--env", "membrane", "--psf", str(psf), "--pdb", str(pdb), "--runs-dir", str(tmp_path / "m")],
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


def test_openmm_mk_inp_dispatches_generator(monkeypatch):
    """OpenMM template mode is testable without importing a GPU platform."""
    import mstbx.commands.openmm_run as command
    called = []
    monkeypatch.setattr(command, "generate_default_inps", lambda: called.append(True))

    result = CliRunner().invoke(cli, ["openmm-run", "--mk-inp"])

    assert result.exit_code == 0, result.output
    assert called == [True]
