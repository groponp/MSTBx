#!/usr/bin/env python3
"""
makecomplex.py ─ pipeline completo

1. Extrae MODEL 1 de un PDBQT con varias poses.
2. Convierte a PDB.
3. Añade H + cargas Gasteiger (pH 7.4) → MOL2.
4. Renombra el residuo en el MOL2 a LIG (UNL → LIG).
5. Normaliza el ligando como un único residuo LIG
   (líneas HETATM, chain L, resname LIG, resid 1).
6. Fusiona con la proteína (chain A) y escribe el complejo final.

Archivos generados:
    pose1.pdbqt
    ligand.pdb
    ligand_wH_charged.mol2
    complex.pdb      (nombre definido con --output)

Requisitos:
    • Open Babel (obabel) en el PATH
    • MDAnalysis ≥ 2.4 → pip install mdanalysis
"""

import argparse
import subprocess
import warnings
from pathlib import Path

import MDAnalysis as mda
from MDAnalysis.core.universe import Merge


def run(cmd: str) -> None:
    """Ejecuta un comando shell y falla si devuelve código ≠ 0."""
    subprocess.run(cmd, shell=True, check=True)


def extract_pose1(src: Path, dst: Path) -> None:
    awk = r"/^MODEL[[:space:]]+1/,/^ENDMDL/ {print}"
    run(f"awk '{awk}' {src} > {dst}")


def pdbqt_to_pdb(src: Path, dst: Path) -> None:
    run(f"obabel -ipdbqt {src} -opdb -O {dst} --log-level 2")


def pdb_to_mol2(src: Path, dst: Path) -> None:
    run(
        f"obabel -ipdb {src} -omol2 -O {dst} "
        f"--partialcharge gasteiger -p 7.4 --log-level 2"
    )

def ensure_chain(u: mda.Universe, chain_id: str) -> None:
    """Asegura que todos los átomos tengan chainID = chain_id."""
    if "chainIDs" not in u.atoms.names:
        u.add_TopologyAttr("chainIDs", [""] * len(u.atoms))
    u.atoms.chainIDs = [chain_id] * len(u.atoms)


def prepare_ligand(u: mda.Universe) -> None:
    """
    Normaliza el ligando para que salga como:
        HETATM ... LIG L   1
    Gestiona record_types, resnames y resids.
    """
    n_atoms = len(u.atoms)
    n_res   = len(u.residues)

    # atributos por átomo: record_types
    if "record_types" not in u.atoms.names:
        u.add_TopologyAttr("record_types", ["HETATM"] * n_atoms)
    u.atoms.record_types = ["HETATM"] * n_atoms

    # atributos por residuo: resnames y resids
    if not hasattr(u.residues, 'resnames'):
        u.add_TopologyAttr("resnames", ["UNL"] * n_res, elements="residues")
    u.residues.resnames = ["UNL"] * n_res
    if not hasattr(u.residues, 'resids'):
        u.add_TopologyAttr("resids", [1] * n_res, elements="residues")
    u.residues.resids = [1] * n_res


def get_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Genera complex.pdb (proteína + ligando) desde un docking."
    )
    ap.add_argument("-d", "--dock",    required=True, help="PDBQT con varias poses")
    ap.add_argument("-p", "--protein", required=True, help="PDB de la proteína")
    ap.add_argument("-o", "--output",  required=True, help="Nombre del PDB final")
    return ap.parse_args()


def main() -> None:
    args = get_args()
    dock      = Path(args.dock).resolve()
    protein   = Path(args.protein).resolve()
    complex_p = Path(args.output).resolve()

    # intermedios
    pose1_qt = Path("pose1.pdbqt")
    lig_pdb  = Path("ligand.pdb")
    lig_mol2 = Path("ligand_wH_charged.mol2")

    print("• Extrayendo MODEL 1 …")
    extract_pose1(dock, pose1_qt)

    print("• PDBQT → PDB …")
    pdbqt_to_pdb(pose1_qt, lig_pdb)

    print("• Añadiendo H y cargas (MOL2) …")
    pdb_to_mol2(lig_pdb, lig_mol2)

    # Fusionar con MDAnalysis
    warnings.filterwarnings(
        "ignore", category=UserWarning, module="MDAnalysis.coordinates.PDB"
    )
    warnings.filterwarnings(
        "ignore", category=UserWarning, module="MDAnalysis.topology.PDBParser"
    )

    u_prot = mda.Universe(protein)
    u_lig  = mda.Universe(lig_mol2)

    # Asignar chain IDs
    ensure_chain(u_prot, "A")
    ensure_chain(u_lig, "L")

    # Normalizar ligando (resname LIG, resid 1, HETATM)
    prepare_ligand(u_lig)

    # Merge
    u_comp = Merge(u_prot.atoms, u_lig.atoms)
    if getattr(u_prot, "dimensions", None) is not None:
        u_comp.dimensions = u_prot.dimensions

    u_comp.atoms.write(complex_p)
    print(f"\n✓ Complejo escrito en: {complex_p} y ligand resname es: UNL")
    print("• Intermedios guardados:")
    for f in (pose1_qt, lig_pdb, lig_mol2):
        print("  ", f)


if __name__ == "__main__":
    main()
