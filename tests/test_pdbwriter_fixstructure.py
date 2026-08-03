"""Testes adversariais da política PDBFixer em ``pdbwriter``."""

from pathlib import Path

import pytest
from click.testing import CliRunner

import mstbx.core.Build.PDBWriter as pdbwriter_module
from mstbx.core.Build.PDBWriter import PDBWriter
from mstbx.commands.pdbwriter import pdbwriter


class FakeChain:
    """Cadeia mínima para simular topologia OpenMM."""

    def __init__(self, chain_id, residues):
        self.id = chain_id
        self._residues = residues

    def residues(self):
        return list(self._residues)


class FakeTopology:
    """Topologia mínima usada pelo fake PDBFixer."""

    def __init__(self):
        self._chains = [FakeChain("A", [object(), object(), object()])]
        self._atoms = [object(), object(), object()]

    def chains(self):
        return list(self._chains)

    def atoms(self):
        return list(self._atoms)


class FakeFixerNoSeqres:
    """PDBFixer falso sem SEQRES."""

    def __init__(self, filename=None, pdbid=None):
        self.topology = FakeTopology()
        self.sequences = []
        self.nonstandardResidues = []

    def findNonstandardResidues(self):
        return None

    def replaceNonstandardResidues(self):
        return None

    def removeHeterogens(self, keepWater=False):
        return None


class FakeFixerWithGaps(FakeFixerNoSeqres):
    """PDBFixer falso com gaps terminal e interno."""

    def __init__(self, filename=None, pdbid=None):
        super().__init__(filename=filename, pdbid=pdbid)
        self.sequences = ["AAA"]
        self.missingResidues = {}
        self.missingAtoms = {"A": ["CA"]}
        self.missingTerminals = {}
        self.positions = []

    def findMissingResidues(self):
        self.missingResidues = {
            (0, 0): ["GLY"],
            (0, 1): ["SER"],
            (0, 3): ["ALA"],
        }

    def findMissingAtoms(self):
        return None

    def addMissingAtoms(self):
        return None


class FakePDBFile:
    """Escritor mínimo para capturar saída do PDBFixer."""

    @staticmethod
    def writeFile(topology, positions, handle, keepIds=True):
        handle.write("HEADER FAKE\nEND\n")


def test_fix_structure_rejects_local_pdb_without_seqres(monkeypatch, tmp_path):
    """Sem SEQRES, gaps internos não são reconstruídos silenciosamente."""
    monkeypatch.setattr(pdbwriter_module, "PDBFixer", FakeFixerNoSeqres)
    monkeypatch.setattr(pdbwriter_module, "PDBFile", FakePDBFile)
    pdb = tmp_path / "no_seqres.pdb"
    pdb.write_text("ATOM      1  CA  ALA A   1       0.0   0.0   0.0\nEND\n")

    writer = PDBWriter(str(pdb))

    with pytest.raises(RuntimeError, match="No SEQRES"):
        writer.fix_structure()


def test_fix_structure_keeps_only_internal_missing_residues(monkeypatch, tmp_path):
    """Gaps terminais são descartados e o gap interno permanece."""
    monkeypatch.setattr(pdbwriter_module, "PDBFixer", FakeFixerWithGaps)
    monkeypatch.setattr(pdbwriter_module, "PDBFile", FakePDBFile)
    pdb = tmp_path / "with_seqres.pdb"
    pdb.write_text("HEADER FAKE\nEND\n")

    writer = PDBWriter(str(pdb))

    assert writer.fix_structure()
    assert Path(writer.input_file).read_text() == "HEADER FAKE\nEND\n"
    assert "Internal missing residues kept: 1" in "\n".join(writer.log_messages)


def test_protonate_runs_pdb2pqr_with_charmm_nomenclature(monkeypatch, tmp_path):
    """CHARMM protonation invokes PDB2PQR and updates the working PDB."""
    source = tmp_path / "input.pdb"
    source.write_text("HEADER TEST\nEND\n")

    def fake_run(command, check):
        output = Path(command[command.index("--pdb-output") + 1])
        output.write_text("ATOM      1  CA  ALA A   1       1.000   2.000   3.000\nEND\n")
        assert command[:3] == ["pdb2pqr", "--ff", "CHARMM"]
        assert command[command.index("--ffout") + 1] == "CHARMM"
        assert command[command.index("--with-ph") + 1] == "7.4"
        assert "--titration-state-method" in command

    monkeypatch.setattr(pdbwriter_module.shutil, "which", lambda name: name)
    monkeypatch.setattr(pdbwriter_module.subprocess, "run", fake_run)

    writer = PDBWriter(str(source))
    output = writer.protonate(pH=7.4, ff="CHARMM")

    assert output == Path(writer.input_file)
    assert output.read_text().startswith("ATOM")


def test_extended_crd_uses_charmm_residue_indices_and_masses(tmp_path, monkeypatch):
    """Extended CRD follows CHARMM-GUI's sequential index and mass columns."""
    source = tmp_path / "input.pdb"
    source.write_text(
        "ATOM      1  N   ALA A   8       1.000   2.000   3.000  1.00 20.00           N  \n"
        "ATOM      2  CA  ALA A   8       2.000   2.000   3.000  1.00 20.00           C  \n"
        "ATOM      3  CA  GLY A   9       3.000   2.000   3.000  1.00 20.00           C  \n"
        "END\n"
    )
    monkeypatch.chdir(tmp_path)
    output = tmp_path / "system.crd"

    writer = PDBWriter(str(source))
    writer.write_ext_crd(output)
    records = [line.split() for line in output.read_text().splitlines() if line.strip() and not line.startswith("*") and "EXT" not in line]

    assert records[0][0:4] == ["1", "1", "ALA", "N"]
    assert records[1][0:4] == ["2", "1", "ALA", "CA"]
    assert records[2][0:4] == ["3", "2", "GLY", "CA"]
    assert records[0][8] == "8"
    assert float(records[0][9]) > 14.0


def test_pdb_id_alone_downloads_official_structure(tmp_path, monkeypatch):
    """A bare PDB ID is a download operation with a predictable filename."""
    def fake_download(url, destination):
        assert url == "https://files.rcsb.org/download/1AKI.pdb"
        Path(destination).write_text("HEADER 1AKI\nEND\n")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("mstbx.commands.pdbwriter.urllib.request.urlretrieve", fake_download)

    result = CliRunner().invoke(pdbwriter, ["--pdb-id", "1AKI"])

    assert result.exit_code == 0, result.output
    assert (tmp_path / "1aki.pdb").read_text() == "HEADER 1AKI\nEND\n"


def test_pdb_id_download_filters_selected_chains(tmp_path, monkeypatch):
    """Download mode applies comma-separated chain selection."""
    def fake_download(url, destination):
        Path(destination).write_text(
            "HEADER TEST\n"
            "SEQRES   1 A    1  ALA\n"
            "SEQRES   1 B    1  GLY\n"
            "ATOM      1  CA  ALA A   1       1.000   2.000   3.000\n"
            "ATOM      2  CA  GLY B   1       4.000   5.000   6.000\n"
            "ATOM      3  CA  SER C   1       7.000   8.000   9.000\n"
            "END\n"
        )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("mstbx.commands.pdbwriter.urllib.request.urlretrieve", fake_download)

    result = CliRunner().invoke(
        pdbwriter,
        ["--pdb-id", "7A3S", "--select-chains", "B,C", "--output", "7a3s_ab_chains.pdb"],
    )

    assert result.exit_code == 0, result.output
    text = (tmp_path / "7a3s_ab_chains.pdb").read_text()
    assert " CA  ALA A" not in text
    assert " CA  GLY B" in text
    assert " CA  SER C" in text
    assert "SEQRES   1 A" not in text
    assert "SEQRES   1 B" in text
