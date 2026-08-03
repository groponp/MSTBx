"""Restrições posicionais GROMACS a partir de seleções MDAnalysis."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from mstbx.core.Gromacs.Index import PROTEIN_SELECTION

DEFAULT_FORCE = round(5.0 * 4.184 * 100)
DEFAULT_SELECTION = f"name N CA C O and {PROTEIN_SELECTION} or resname LIG and not name H*"
SOLVENT_IONS = {"SOL", "TIP3", "TIP3P", "WAT", "HOH", "NA", "CL", "K", "MG", "CA", "SOD", "CLA", "ZN"}


@dataclass
class RestraintConfig:
    """Configuração de restraints GROMACS.

    Parameters
    ----------
    runs_dir
        Diretório raiz do sistema.
    selection
        Seleção MDAnalysis para restringir.
    force
        Constante em kJ mol-1 nm-2.
    """

    runs_dir: Path
    selection: str = DEFAULT_SELECTION
    force: int = DEFAULT_FORCE


class GromacsRestraints:
    """Aplica restraints no sistema GROMACS."""

    def __init__(self, config: RestraintConfig):
        """Inicializa o aplicador."""
        self.config = config
        self.build = config.runs_dir / "01build"

    def apply_all(self) -> tuple[int, int]:
        """Aplica restraints e atualiza topologias.

        Returns
        -------
        tuple[int, int]
            Número de átomos de proteína e ligando restringidos.
        """
        return self._apply()

    def _apply(self) -> tuple[int, int]:
        import MDAnalysis as mda

        universe = mda.Universe(str(self.build / "ionized.gro"))
        selected = universe.select_atoms(self.config.selection)
        if not len(selected):
            raise ValueError(f"Empty restraint selection: {self.config.selection}")
        protein = selected.select_atoms(PROTEIN_SELECTION)
        ligand = selected.select_atoms(f"not {PROTEIN_SELECTION} and not resname SOL TIP3 TIP3P WAT HOH NA CL K MG CA SOD CLA ZN")
        protein_ids = self._local_ids(protein, universe.select_atoms(PROTEIN_SELECTION))
        ligand_ref = self._ligand_reference(universe, ligand)
        ligand_ids = self._local_ids(ligand, ligand_ref)
        if protein_ids:
            posre = self.build / "posre_backbone.itp"
            posre.write_text(self._block(protein_ids, "POSRES"))
            shutil.copy2(posre, self.config.runs_dir / "restraints/posre_backbone.itp")
            self._replace_posre(self._protein_topology(), "posre_backbone.itp")
        if ligand_ids:
            itp = self._ligand_topology()
            itp.write_text(self._without_block(itp.read_text(), "POSRES_LIGAND") + "\n\n" + self._block(ligand_ids, "POSRES_LIGAND"))
            shutil.copy2(itp, self.config.runs_dir / "toppar/ligand.itp")
        return len(protein_ids), len(ligand_ids)

    @staticmethod
    def _local_ids(atoms, reference) -> list[int]:
        """Converte índices globais em índices locais de molécula."""
        if not len(atoms):
            return []
        first, last = min(a.index for a in reference), max(a.index for a in reference)
        if any(a.index < first or a.index > last for a in atoms):
            raise ValueError("The restraint selection crosses topology molecule boundaries.")
        return [a.index - first + 1 for a in atoms]

    @staticmethod
    def _ligand_reference(universe, ligand_atoms):
        """Seleciona a molécula de referência para o ligando."""
        resnames = {res.resname for res in ligand_atoms.residues if res.resname not in SOLVENT_IONS}
        if not resnames:
            return ligand_atoms[:0]
        if len(resnames) > 1:
            raise ValueError(f"More than one ligand resname selected: {sorted(resnames)}")
        return universe.select_atoms(f"resname {next(iter(resnames))}")

    def _block(self, atoms: list[int], define: str) -> str:
        """Monta bloco ``[ position_restraints ]``."""
        lines = [f"#ifdef {define}", "[ position_restraints ]", "; atom type fx fy fz"]
        lines += [f"{i:6d} 1 {self.config.force:7d} {self.config.force:7d} {self.config.force:7d}" for i in atoms]
        return "\n".join(lines + ["#endif", ""])

    @staticmethod
    def _without_block(text: str, define: str) -> str:
        """Remove bloco ``#ifdef`` existente."""
        out, skip = [], False
        for line in text.splitlines():
            if line.strip() == f"#ifdef {define}":
                skip = True
                continue
            if skip and line.strip() == "#endif":
                skip = False
                continue
            if not skip:
                out.append(line)
        return "\n".join(out).rstrip()

    def _replace_posre(self, topology: Path, include: str) -> None:
        """Troca o primeiro include de ``posre`` no arquivo informado."""
        lines, done = [], False
        for line in topology.read_text().splitlines():
            if not done and line.strip().startswith("#include") and "posre" in line.lower():
                lines.append(f'#include "{include}"')
                done = True
            else:
                lines.append(line)
        if not done:
            raise ValueError(f"Could not find a posre include in {topology}")
        topology.write_text("\n".join(lines) + "\n")

    def _protein_topology(self) -> Path:
        """Encontra topologia com include de restraints da proteína."""
        for path in [*self.build.glob("topol_Protein*.itp"), *self.build.glob("topol_*.itp"), self.build / "topol.top"]:
            if path.exists() and "posre" in path.read_text().lower():
                return path
        raise ValueError(f"Could not find a protein topology with posre include in {self.build}")

    def _ligand_topology(self) -> Path:
        """Encontra ITP de ligando incluído em ``topol.top``."""
        for line in (self.build / "topol.top").read_text().splitlines():
            if line.strip().startswith("#include") and '"' in line:
                name = Path(line.split('"')[1]).name
                path = self.build / name
                if path.exists() and path.suffix == ".itp" and not path.name.startswith(("topol_", "posre")):
                    return path
        raise ValueError(f"Could not find a ligand ITP in {self.build / 'topol.top'}")
