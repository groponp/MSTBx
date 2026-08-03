"""Matriz de combinações válidas e inválidas do comando ``pdbwriter``."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from mstbx.commands.pdbwriter import pdbwriter


def _pdb(path: Path) -> None:
    path.write_text(
        "ATOM      1  CA  ALA A   1       1.000   2.000   3.000  1.00 20.00           C  \n"
        "ATOM      2  SG  CYS A   2       4.000   5.000   6.000  1.00 20.00           S  \n"
        "HETATM    3  C1  LIG B   3       7.000   8.000   9.000  1.00 20.00           C  \n"
        "END\n"
    )


class FakeWriter:
    """Writer fake usado para verificar a ordem da interface Click."""

    calls = []

    def __init__(self, input_file, psf_file=None, pdb_id=None):
        self.input_file = input_file
        self.calls.append(("init", input_file, psf_file, pdb_id))

    def fix_structure(self, **kwargs):
        self.calls.append(("fix_structure", kwargs))
        return True

    def protonate(self, **kwargs):
        self.calls.append(("protonate", kwargs))

    def find_ssbonds(self, **kwargs):
        self.calls.append(("ssbond", kwargs))

    def edit_structure(self, **kwargs):
        self.calls.append(("edit", kwargs))

    def select_atoms(self, selection):
        self.calls.append(("select", selection))

    def write_ext_crd(self, output):
        self.calls.append(("crd", str(output)))
        Path(output).write_text("* EXT\n")

    def write_final_pdb(self, output):
        self.calls.append(("pdb", str(output)))
        Path(output).write_text("END\n")


@pytest.mark.parametrize(
    "options, expected",
    [
        (["--select-atoms", "protein", "--ssbond"], ["select", "ssbond"]),
        (["--rename-chain", "A:B", "--renumber", "10", "--segid", "PROB"], ["edit", "edit"]),
        (["--pH", "7.4", "--ff-out", "CHARMM"], ["protonate"]),
        (["--fix-structure", "--fix-keep-hetatoms", "--fix-add-hydrogens"], ["fix_structure"]),
        (["--select-atoms", "protein or resname LIG", "--ssbond", "--segid", "PROB,PROL"], ["select", "ssbond", "edit"]),
    ],
)
def test_pdbwriter_valid_operation_combinations(tmp_path, monkeypatch, options, expected):
    """Valid option combinations execute in a deterministic operation order."""
    source = tmp_path / "input.pdb"
    _pdb(source)
    FakeWriter.calls = []
    import mstbx.commands.pdbwriter as command

    monkeypatch.setattr(command, "PDBWriter", FakeWriter)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        pdbwriter,
        ["--input", str(source), "--output", "out.pdb", *options],
    )

    assert result.exit_code == 0, result.output
    operations = [call[0] for call in FakeWriter.calls]
    assert [name for name in expected if name in operations] == expected
    assert operations[-1] == "pdb"


def test_pdbwriter_crd_combination_writes_only_crd(tmp_path, monkeypatch):
    """A .crd output with --write-ext-crd does not create an implicit PDB."""
    source = tmp_path / "input.pdb"
    _pdb(source)
    FakeWriter.calls = []
    import mstbx.commands.pdbwriter as command

    monkeypatch.setattr(command, "PDBWriter", FakeWriter)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        pdbwriter,
        ["--input", str(source), "--output", "system.crd", "--write-ext-crd"],
    )

    assert result.exit_code == 0, result.output
    assert (tmp_path / "system.crd").exists()
    assert not (tmp_path / "system.pdb").exists()
    assert [call[0] for call in FakeWriter.calls][-1] == "crd"


@pytest.mark.parametrize(
    "args, message",
    [
        (["--mol", "input.pdb"], "ONLY be used"),
        (["--input", "input.pdb"], "--output must be provided"),
        (["--fix-structure"], "must be provided"),
    ],
)
def test_pdbwriter_invalid_operation_combinations_fail_without_traceback(tmp_path, args, message):
    """Invalid combinations stop at the CLI boundary with a useful message."""
    source = tmp_path / "input.pdb"
    _pdb(source)
    normalized = [str(source) if value == "input.pdb" else value for value in args]
    result = CliRunner().invoke(pdbwriter, normalized)

    assert result.exit_code != 0
    assert message in result.output
    assert "Traceback" not in result.output


@pytest.mark.parametrize(
    "extra_args, message",
    [
        (["--ff-out", "CHARMM"], "--ff-out"),
        (["--fix-add-hydrogens"], "--fix-add-hydrogens"),
        (["--fix-keep-hetatoms"], "--fix-keep-hetatoms"),
        (["--ligand-pH", "7.0"], "--ligand-pH"),
    ],
)
def test_pdbwriter_rejects_flags_that_would_be_silently_ignored(tmp_path, monkeypatch, extra_args, message):
    """A flag whose only consumer is a code path the user did not request must
    fail loudly instead of downloading/writing a file that looks processed but
    is not (the exact bug: --pdb-id --ff-out CHARMM without --pH used to just
    download the raw PDB and print a success message)."""
    def fake_download(url, destination):
        Path(destination).write_text("ATOM\nEND\n")

    import mstbx.commands.pdbwriter as command
    monkeypatch.setattr(command.urllib.request, "urlretrieve", fake_download)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(
        pdbwriter, ["--pdb-id", "1AKI", "--output", "out.pdb", *extra_args]
    )

    assert result.exit_code != 0
    assert message in result.output
    assert "Traceback" not in result.output
    assert not (tmp_path / "out.pdb").exists()


def test_pdbwriter_rejects_processing_flags_combined_with_cgenff_prep(tmp_path):
    """--prepare-cgenff-inputs is a self-contained branch; flags that only
    matter to the normal repair/protonation/edit path must be rejected there
    instead of being silently skipped."""
    source = tmp_path / "input.pdb"
    _pdb(source)

    result = CliRunner().invoke(
        pdbwriter,
        ["--prepare-cgenff-inputs", "--input", str(source), "--fix-structure",
         "--output", str(tmp_path / "out")],
    )

    assert result.exit_code != 0
    assert "--fix-structure" in result.output
    assert "--prepare-cgenff-inputs" in result.output
    assert "Traceback" not in result.output


def test_pdbwriter_ph_with_ff_out_is_accepted(tmp_path, monkeypatch):
    """The documented, correct combination (--pH plus --ff-out) still runs."""
    def fake_download(url, destination):
        Path(destination).write_text("ATOM\nEND\n")

    FakeWriter.calls = []
    import mstbx.commands.pdbwriter as command
    monkeypatch.setattr(command.urllib.request, "urlretrieve", fake_download)
    monkeypatch.setattr(command, "PDBWriter", FakeWriter)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(
        pdbwriter,
        ["--pdb-id", "1AKI", "--pH", "7.4", "--ff-out", "CHARMM", "--output", "out.pdb"],
    )

    assert result.exit_code == 0, result.output
    assert ("protonate", {"pH": 7.4, "ff": "CHARMM"}) in FakeWriter.calls


def test_pdbwriter_prepare_cgenff_cli_combination(tmp_path, monkeypatch):
    """The CGenFF preparation branch forwards all ligand selectors."""
    source = tmp_path / "input.pdb"
    _pdb(source)
    observed = {}
    import mstbx.commands.pdbwriter as command

    class FakePreparer:
        def __init__(self, config):
            observed.update(vars(config))

        def prepare(self):
            return {"protein": Path("protein_prepared.pdb"), "ligand_mol2": Path("ligand.mol2")}

    monkeypatch.setattr(command, "CGenFFInputPreparer", FakePreparer)
    result = CliRunner().invoke(
        pdbwriter,
        ["--prepare-cgenff-inputs", "--input", str(source), "--ligand-pH", "7.2",
         "--pdb-ligand-resname", "LIG", "--pdb-ligand-chain", "B", "--output", str(tmp_path / "out")],
    )

    assert result.exit_code == 0, result.output
    assert observed["ligand_pH"] == 7.2
    assert observed["pdb_ligand_resname"] == "LIG"
    assert observed["pdb_ligand_chain"] == "B"
