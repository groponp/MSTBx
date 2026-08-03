"""Criação de grupos GROMACS usando seleções MDAnalysis."""

from __future__ import annotations

import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


SOLVENT_IONS = "resname SOL TIP3 TIP3P WAT HOH NA CL K CA MG SOD CLA ZN"
SOLUTE = f"not ({SOLVENT_IONS})"


@dataclass
class IndexGroup:
    """Grupo de índice baseado em seleção MDAnalysis.

    Parameters
    ----------
    name
        Nome do grupo em ``index.ndx``.
    selection
        Seleção MDAnalysis.
    """

    name: str
    selection: str


class GromacsIndex:
    """Escreve ``index.ndx`` para os grupos de acoplamento térmico."""

    def __init__(self, runs_dir: Path, replicas: int, groups: list[IndexGroup]):
        """Inicializa o escritor de índice."""
        self.runs_dir = runs_dir
        self.replicas = replicas
        self.groups = groups

    def write_all(self) -> Path:
        """Escreve ``rep1`` e copia o índice para as demais réplicas."""
        source = self.runs_dir / "rep1/01build/index.ndx"
        self.write_index(self.runs_dir / "rep1/01build/ionized.gro", source)
        for rep in range(2, self.replicas + 1):
            shutil.copy2(source, self.runs_dir / f"rep{rep}/01build/index.ndx")
        return source

    def write_index(self, coordinates: Path, output: Path) -> None:
        """Escreve um arquivo de índice.

        Parameters
        ----------
        coordinates
            Coordenadas ``.gro`` do sistema ionizado.
        output
            Arquivo ``index.ndx`` a criar.
        """
        import MDAnalysis as mda

        universe = mda.Universe(str(coordinates))
        selected, blocks = [], []
        for group in self.groups:
            atoms = universe.select_atoms(group.selection)
            if not len(atoms):
                raise ValueError(f"Empty index selection for {group.name}: {group.selection}")
            selected.append((group, atoms))
            blocks.append(self._block(group.name, [int(atom.id) for atom in atoms]))
        self._validate_coverage(universe, selected)
        output.write_text("\n\n".join(blocks) + "\n")

    @staticmethod
    def _block(name: str, atom_ids: list[int]) -> str:
        """Formata um bloco GROMACS ``.ndx``."""
        lines = [f"[ {name} ]"]
        lines += [" ".join(f"{i:5d}" for i in atom_ids[n:n + 15]) for n in range(0, len(atom_ids), 15)]
        return "\n".join(lines)

    @staticmethod
    def _validate_coverage(universe, selected: list[tuple[IndexGroup, object]]) -> None:
        """Garante cobertura completa e sem sobreposição."""
        seen, overlap = set(), set()
        for _, atoms in selected:
            ids = set(atoms.indices)
            overlap |= seen & ids
            seen |= ids
        missing = set(range(len(universe.atoms))) - seen
        if missing:
            atoms = universe.atoms[sorted(missing)]
            counts = ", ".join(f"{k}:{v}" for k, v in sorted(Counter(atoms.resnames).items()))
            raise ValueError(f"{len(atoms)} atoms are outside tc-grps selections. Missing resnames: {counts}")
        if overlap:
            raise ValueError(f"Index selections overlap in {len(overlap)} atoms.")
