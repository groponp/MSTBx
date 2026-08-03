"""Preparação de entradas manuais para CGenFF Web."""

from __future__ import annotations

import json
import shutil
import subprocess
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class CGenFFInputConfig:
    """Configuração para preparar proteína e ligando.

    Parameters
    ----------
    output_dir
        Diretório de saída.
    protein
        PDB local. Alternativo a ``pdb_id``.
    pdb_id
        Identificador RCSB PDB para download.
    select_chains
        Cadeias de proteína separadas por vírgula.
    ligand
        Ligando externo em PDB.
    pdb_ligand_resname
        Resname do ligando no PDB de origem.
    pdb_ligand_chain
        Cadeia do ligando.
    pdb_ligand_resid
        Resid do ligando.
    ligand_pH
        pH usado pelo Open Babel.
    overwrite
        Permite sobrescrever arquivos existentes.
    """

    output_dir: Path
    protein: Path | None = None
    pdb_id: str | None = None
    select_chains: str = ""
    ligand: Path | None = None
    pdb_ligand_resname: str | None = None
    pdb_ligand_chain: str | None = None
    pdb_ligand_resid: str | None = None
    ligand_pH: float = 7.4
    overwrite: bool = False


class CGenFFInputPreparer:
    """Prepara arquivos que o usuário enviará manualmente ao CGenFF Web."""

    def __init__(self, config: CGenFFInputConfig):
        """Inicializa o preparador."""
        self.config = config

    def prepare(self) -> dict[str, Path]:
        """Gera ``protein_prepared.pdb``, ``ligand_pose.pdb`` e MOL2."""
        self._validate()
        if self.config.output_dir.exists() and self.config.overwrite:
            shutil.rmtree(self.config.output_dir)
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        pdb = self._source_pdb()
        protein = self.config.output_dir / "protein_prepared.pdb"
        ligand_pose = self.config.output_dir / "ligand_pose.pdb"
        mol2 = self.config.output_dir / "ligand_for_cgenff.mol2"
        self._write_protein(pdb, protein)
        if self.config.ligand:
            shutil.copy2(self.config.ligand, ligand_pose)
        else:
            self._write_ligand(pdb, ligand_pose)
        self._mol2_from_ligand(ligand_pose, mol2)
        self._write_log(pdb, protein, ligand_pose, mol2)
        return {"protein": protein, "ligand_pdb": ligand_pose, "ligand_mol2": mol2}

    def _validate(self) -> None:
        if bool(self.config.protein) == bool(self.config.pdb_id):
            raise ValueError("Use exactly one source: --input or --pdb-id.")
        if not self.config.ligand and not self.config.pdb_ligand_resname:
            raise ValueError("Use --ligand or provide --pdb-ligand-resname.")

    def _source_pdb(self) -> Path:
        """Retorna o PDB local ou baixado."""
        if self.config.protein:
            return self.config.protein
        assert self.config.pdb_id
        pdb = self.config.output_dir / f"{self.config.pdb_id.lower()}.pdb"
        urllib.request.urlretrieve(f"https://files.rcsb.org/download/{self.config.pdb_id.upper()}.pdb", pdb)
        return pdb

    def _write_protein(self, pdb: Path, output: Path) -> None:
        """Escreve somente linhas ``ATOM`` das cadeias selecionadas."""
        chains = {c.strip() for c in self.config.select_chains.split(",") if c.strip()}
        lines = []
        for line in pdb.read_text().splitlines():
            if line.startswith("ATOM") and (not chains or line[21].strip() in chains):
                lines.append(line.rstrip())
        output.write_text("\n".join(lines) + "\nEND\n")

    def _write_ligand(self, pdb: Path, output: Path) -> None:
        """Extrai o ligando do PDB de origem."""
        lines = []
        for line in pdb.read_text().splitlines():
            ok = line.startswith("HETATM") and line[17:20].strip() == self.config.pdb_ligand_resname
            ok &= self.config.pdb_ligand_chain is None or line[21].strip() == self.config.pdb_ligand_chain
            ok &= self.config.pdb_ligand_resid is None or line[22:26].strip() == self.config.pdb_ligand_resid
            if ok:
                lines.append(line[:17] + "LIG" + line[20:])
        if not lines:
            raise ValueError(f"Could not find ligand {self.config.pdb_ligand_resname} in {pdb}.")
        output.write_text("\n".join(lines) + "\nEND\n")

    def _mol2_from_ligand(self, ligand_pdb: Path, mol2: Path) -> None:
        """Gera MOL2 por Open Babel usando cargas Gasteiger."""
        subprocess.run(
            ["obabel", "-ipdb", str(ligand_pdb), "-omol2", "-O", str(mol2), "--partialcharge", "gasteiger", "-p", str(self.config.ligand_pH)],
            check=True,
        )

    def _write_log(self, pdb: Path, protein: Path, ligand_pose: Path, mol2: Path) -> None:
        """Escreve log JSON reprodutível."""
        data = asdict(self.config)
        data.update({"source_pdb": str(pdb), "protein_prepared": str(protein), "ligand_pose": str(ligand_pose), "ligand_mol2": str(mol2)})
        (self.config.output_dir / "cgenff_inputs_log.json").write_text(json.dumps(data, default=str, indent=2) + "\n")
