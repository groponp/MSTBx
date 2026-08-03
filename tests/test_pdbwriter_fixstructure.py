"""Testes adversariais da política PDBFixer em ``pdbwriter``."""

from pathlib import Path

import pytest

import mstbx.core.Build.PDBWriter as pdbwriter_module
from mstbx.core.Build.PDBWriter import PDBWriter


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
