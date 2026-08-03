"""Construção de sistemas GROMACS no layout MSTBx.

O módulo mantém a lógica de montagem separada da interface de linha de
comando. As mensagens ao usuário são emitidas pelo comando ``click``.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from mstbx.core.Gromacs.Ligand import (
    cgenff_resi_name,
    molecule_type,
    normalize_mol2_name,
    set_ligand_resname,
    write_ligand_pdb,
)


DEFAULT_FORCEFIELD_DIR = Path(__file__).resolve().parent / "data" / "charmm36-feb2026_cgenff-5.0.ff"
DEFAULT_CGENFF_CONVERTER = Path(__file__).resolve().parent / "cgenff_charmm2gmx_py3.py"


@dataclass
class GromacsBuildConfig:
    """Configuração para construir um sistema GROMACS.

    Parameters
    ----------
    protein
        Arquivo PDB da proteína preparada.
    forcefield_dir
        Diretório ``*.ff`` do campo de força CHARMM/CGenFF. Quando omitido,
        usa a versão empacotada no MSTBx.
    output_dir
        Diretório raiz do sistema.
    ligand_mol2, ligand_str
        Arquivos do ligando. Ambos devem ser informados juntos.
    ligand_resname
        Nome de resíduo final para o ligando.
    box_distance
        Distância soluto-borda em nm.
    gmx
        Executável GROMACS.
    cgenff_converter
        Conversor ``cgenff_charmm2gmx_py3.py``. Quando omitido, usa a versão
        empacotada no MSTBx.
    pdb2gmx_ter
        Ativa seleção interativa de NTER/CTER em ``pdb2gmx``.
    pdb2gmx_selection
        Texto enviado ao ``stdin`` do ``pdb2gmx``.
    pdb2gmx_protonation
        Ativa seleção de estados HIS/ASP/GLU/LYS/ARG.
    overwrite
        Remove o diretório de saída antes de construir.
    """

    protein: Path
    output_dir: Path
    forcefield_dir: Path = DEFAULT_FORCEFIELD_DIR
    ligand_mol2: Path | None = None
    ligand_str: Path | None = None
    ligand_resname: str = "LIG"
    box_distance: float = 1.8
    gmx: str = "gmx"
    cgenff_converter: Path = DEFAULT_CGENFF_CONVERTER
    pdb2gmx_ter: bool = False
    pdb2gmx_selection: str | None = None
    pdb2gmx_protonation: bool = False
    overwrite: bool = False


class GromacsBuilder:
    """Monta um sistema GROMACS no layout MSTBx."""

    def __init__(self, config: GromacsBuildConfig):
        """Inicializa o construtor.

        Parameters
        ----------
        config
            Configuração validada pelo comando.
        """
        self.config = config
        self.build = config.output_dir / "01build"

    def build_system(self) -> None:
        """Executa a montagem completa de ``01build``."""
        self._validate()
        if self.config.output_dir.exists() and self.config.overwrite:
            shutil.rmtree(self.config.output_dir)
        self._make_tree()
        shutil.copytree(self.config.forcefield_dir, self.build / self.config.forcefield_dir.name)
        shutil.copy2(self.config.protein, self.build / "input.pdb")
        has_ligand = bool(self.config.ligand_mol2)
        if has_ligand:
            self._prepare_ligand()
        self._pdb2gmx()
        boxed_input = "protein.pdb"
        if has_ligand:
            self._insert_ligand_topology()
            self._merge_pdb(self.build / "protein.pdb", self.build / "ligand.pdb", self.build / "complex.pdb")
            boxed_input = "complex.pdb"
        self._run([self.config.gmx, "editconf", "-f", boxed_input, "-o", "box.pdb", "-d", str(self.config.box_distance), "-bt", "cubic"])
        self._run([self.config.gmx, "solvate", "-cp", "box.pdb", "-cs", "spc216.gro", "-o", "solv.pdb", "-p", "topol.top"])
        (self.build / "ions.mdp").write_text("integrator=steep\nemtol=1000\nnsteps=500\ncoulombtype=PME\n")
        self._run([self.config.gmx, "grompp", "-f", "ions.mdp", "-c", "solv.pdb", "-p", "topol.top", "-o", "ions.tpr", "-maxwarn", "2"])
        self._run([self.config.gmx, "genion", "-s", "ions.tpr", "-p", "topol.top", "-o", "ionized.gro", "-neutral", "-conc", "0.15"], "SOL\n")

    def _validate(self) -> None:
        paths = [self.config.protein, self.config.forcefield_dir, self.config.ligand_mol2, self.config.ligand_str]
        missing = [str(path) for path in paths if path is not None and not path.exists()]
        if missing:
            raise FileNotFoundError(", ".join(missing))
        if bool(self.config.ligand_mol2) != bool(self.config.ligand_str):
            raise ValueError("Use ligand MOL2 and STR together, or omit both for a protein-only system.")

    def _make_tree(self) -> None:
        for stage in ["01build", "02nvt", "03npt", "04md", "restraints", "toppar"]:
            (self.config.output_dir / stage).mkdir(parents=True, exist_ok=True)

    def _prepare_ligand(self) -> None:
        assert self.config.ligand_mol2 and self.config.ligand_str
        shutil.copy2(self.config.ligand_mol2, self.build)
        shutil.copy2(self.config.ligand_str, self.build)
        name = cgenff_resi_name(self.build / self.config.ligand_str.name)
        mol2 = self.build / self.config.ligand_mol2.name
        normalize_mol2_name(mol2, name)
        self._run([sys.executable, self.config.cgenff_converter, name, mol2.name, self.config.ligand_str.name, self.config.forcefield_dir.name])
        shutil.copy2(self.build / f"{name}.itp", self.build / "ligand.itp")
        shutil.copy2(self.build / f"{name}.prm", self.build / "ligand.prm")
        set_ligand_resname(self.build / "ligand.itp", self.config.ligand_resname)
        write_ligand_pdb(self.build / f"{name.lower()}_ini.pdb", self.build / "ligand.pdb", self.config.ligand_resname)

    def _pdb2gmx(self) -> None:
        cmd = [self.config.gmx, "pdb2gmx", "-f", "input.pdb", "-water", "tip3p", "-ff", self.config.forcefield_dir.stem, "-o", "protein.pdb", "-p", "topol.top"]
        if self.config.pdb2gmx_ter:
            cmd.append("-ter")
        if self.config.pdb2gmx_protonation:
            cmd += ["-his", "-asp", "-glu", "-lys", "-arg"]
        self._run(cmd, self.config.pdb2gmx_selection)

    def _insert_ligand_topology(self) -> None:
        top = self.build / "topol.top"
        lines = top.read_text().splitlines()
        idx = next(i for i, line in enumerate(lines) if "forcefield.itp" in line)
        lines[idx + 1:idx + 1] = ["", '#include "ligand.prm"', '#include "ligand.itp"']
        lines.append(f"{molecule_type(self.build / 'ligand.itp'):<16s} 1")
        top.write_text("\n".join(lines) + "\n")

    def _run(self, command: list[object], stdin: str | None = None) -> None:
        subprocess.run(command, cwd=self.build, input=stdin, text=True, check=True)

    @staticmethod
    def _merge_pdb(protein: Path, ligand: Path, output: Path) -> None:
        p = [line for line in protein.read_text().splitlines() if line.startswith(("ATOM", "HETATM", "TER"))]
        l = [line for line in ligand.read_text().splitlines() if line.startswith("HETATM")]
        output.write_text("\n".join(p + l) + "\nEND\n")
