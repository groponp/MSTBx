"""Testes adversariais para grupos de índice GROMACS."""

import pytest

from mstbx.core.Gromacs.Index import GromacsIndex, IndexGroup, PROTEIN_SELECTION
from mstbx.core.Gromacs.Restraints import DEFAULT_SELECTION


class FakeAtoms:
    """Coleção mínima compatível com a validação de índice."""

    def __init__(self, indices, resnames=None):
        self.indices = indices
        self.resnames = resnames or ["UNK"] * len(indices)

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, item):
        if isinstance(item, list):
            return FakeAtoms(item, [self.resnames[i] for i in item])
        return self.indices[item]


class FakeUniverse:
    """Universo mínimo para testar cobertura/overlap sem MDAnalysis."""

    def __init__(self, atom_count):
        self.atoms = FakeAtoms(list(range(atom_count)), ["PRO", "SOL", "LIG"][:atom_count])


def test_index_validation_rejects_missing_atoms():
    """Nenhum átomo pode ficar fora dos grupos de termostato."""
    selected = [(IndexGroup("A", "index 0"), FakeAtoms([0]))]

    with pytest.raises(ValueError, match="outside tc-grps"):
        GromacsIndex._validate_coverage(FakeUniverse(3), selected)


def test_index_validation_rejects_overlapping_atoms():
    """Grupos sobrepostos quebram a definição de ``tc-grps``."""
    selected = [
        (IndexGroup("A", "index 0 1"), FakeAtoms([0, 1])),
        (IndexGroup("B", "index 1 2"), FakeAtoms([1, 2])),
    ]

    with pytest.raises(ValueError, match="overlap"):
        GromacsIndex._validate_coverage(FakeUniverse(3), selected)


def test_charmm_lysine_terminal_alias_is_in_protein_selection(tmp_path):
    """LSN/LYSN states are not MDAnalysis protein residues by default."""
    import MDAnalysis as mda

    pdb = tmp_path / "lsn.pdb"
    pdb.write_text(
        "ATOM      1  N   LSN A   1       1.000   2.000   3.000  1.00 20.00           N  \n"
        "ATOM      2  CA  LSN A   1       2.000   2.000   3.000  1.00 20.00           C  \nEND\n"
    )
    universe = mda.Universe(pdb)

    assert len(universe.select_atoms("protein")) == 0
    assert len(universe.select_atoms(PROTEIN_SELECTION)) == 2
    assert len(universe.select_atoms(DEFAULT_SELECTION)) == 2
