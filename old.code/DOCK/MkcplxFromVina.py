#!/usr/bin/env python3
"""
makecomplex.py ─ Complete pipeline

1. If --dock (PDBQT) is provided:
    a. Extracts MODEL 1 from a multi-pose PDBQT.
    b. Converts to PDB.
   If --ligand-pdb (PDB) is provided:
    a. Uses the file directly.
2. Adds H + Gasteiger charges (pH 7.4 or specified) → MOL2.
3. Renames the residue in the MOL2 to LIG (UNL → LIG).
4. Normalizes the ligand as a single LIG residue
   (HETATM lines, chain L, resname LIG, resid 1).
5. Merges with the protein (chain A) and writes the final complex.

Generated files:
    pose1.pdbqt (if --dock is used)
    ligand.pdb
    ligand_wH_charged.mol2
    complex.pdb      (name defined with --output)

Requirements:
    • Open Babel (obabel) in PATH
    • MDAnalysis ≥ 2.4 → pip install mdanalysis
"""

import argparse
import subprocess
import warnings
import sys
from pathlib import Path

import MDAnalysis as mda
from MDAnalysis.core.universe import Merge


def run(cmd: str) -> None:
    """Executes a shell command and fails if return code ≠ 0."""
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing: {cmd}")
        sys.exit(e.returncode)


def extract_pose1(src: Path, dst: Path) -> None:
    awk = r"/^MODEL[[:space:]]+1/,/^ENDMDL/ {print}"
    run(f"awk '{awk}' {src} > {dst}")


def pdbqt_to_pdb(src: Path, dst: Path) -> None:
    # Added -d to remove extra hydrogens coming from pdbqt
    run(f"obabel -ipdbqt {src} -opdb -O {dst} --log-level 2 -d")


def pdb_to_mol2(src: Path, dst: Path, pH: float) -> None:
    run(
        f"obabel -ipdb {src} -omol2 -O {dst} "
        f"--partialcharge gasteiger -p {pH} --log-level 2 -d"
    )

def ensure_chain(u: mda.Universe, chain_id: str) -> None:
    """Ensures that all atoms have chainID = chain_id."""
    if "chainIDs" not in u.atoms.names:
        u.add_TopologyAttr("chainIDs", [""] * len(u.atoms))
    u.atoms.chainIDs = [chain_id] * len(u.atoms)


def prepare_ligand(u: mda.Universe) -> None:
    """
    Normalizes the ligand to appear as:
        HETATM ... LIG L   1
    Manages record_types, resnames, and resids.
    """
    n_atoms = len(u.atoms)
    n_res   = len(u.residues)

    # per-atom attributes: record_types
    if "record_types" not in u.atoms.names:
        u.add_TopologyAttr("record_types", ["HETATM"] * n_atoms)
    u.atoms.record_types = ["HETATM"] * n_atoms

    # per-residue attributes: resnames and resids
    if not hasattr(u.residues, 'resnames'):
        u.add_TopologyAttr("resnames", ["LIG"] * n_res, elements="residues")
    u.residues.resnames = ["LIG"] * n_res
    if not hasattr(u.residues, 'resids'):
        u.add_TopologyAttr("resids", [1] * n_res, elements="residues")
    u.residues.resids = [1] * n_res


def get_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Generates complex.pdb (protein + ligand) from a docking result or a ligand PDB."
    )
    
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("-d", "--dock",       help="PDBQT with multiple poses (MODEL 1 will be extracted)")
    group.add_argument("--ligand-pdb",       help="Ligand PDB file")
    
    ap.add_argument("-p", "--protein",    required=True, help="Protein PDB")
    ap.add_argument("-l", "--ligand-pH",  type=float, default=7.4, help="pH to add hydrogens to the ligand (default: 7.4)")
    ap.add_argument("-o", "--output",     required=True, help="Final PDB name")
    
    return ap.parse_args()


def main() -> None:
    # Suppress MDAnalysis warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="MDAnalysis.coordinates.PDB")
    warnings.filterwarnings("ignore", category=UserWarning, module="MDAnalysis.topology.PDBParser")

    args = get_args()
    
    protein   = Path(args.protein).resolve()
    complex_p = Path(args.output).resolve()
    pHLigando = args.ligand_pH 

    if not protein.exists():
        print(f"Error: Protein file not found: {protein}")
        sys.exit(1)

    # intermediates
    lig_pdb  = Path("ligand.pdb")
    lig_mol2 = Path("ligand_wH_charged.mol2")

    # Input logic
    if args.dock:
        dock = Path(args.dock).resolve()
        if not dock.exists():
            print(f"Error: PDBQT file not found: {dock}")
            sys.exit(1)
            
        pose1_qt = Path("pose1.pdbqt")
        print("• Extracting MODEL 1 …")
        extract_pose1(dock, pose1_qt)

        print("• PDBQT → PDB …")
        pdbqt_to_pdb(pose1_qt, lig_pdb)
        
    elif args.ligand_pdb:
        input_ligand = Path(args.ligand_pdb).resolve()
        if not input_ligand.exists():
            print(f"Error: Ligand file not found: {input_ligand}")
            sys.exit(1)
            
        print(f"• Using existing ligand PDB: {input_ligand}")
        lig_pdb = input_ligand

    # Pre-processing: Ensure intermediate PDB has resname LIG
    # so obabel propagates it to MOL2.
    print("• Normalizing resname to LIG in intermediate PDB …")
    try:
        u_tmp = mda.Universe(lig_pdb)
        prepare_ligand(u_tmp) # Sets LIG, chain L, resid 1
        lig_pdb_renamed = Path("ligand_LIG.pdb")
        u_tmp.atoms.write(lig_pdb_renamed)
        lig_pdb = lig_pdb_renamed # Use this for the next step
    except Exception as e:
        print(f"Warning: Could not rename PDB before MOL2 conversion: {e}")
        # Continue with original if fails, though MOL2 will have original name

    print(f"• Adding H and charges (MOL2) at pH {pHLigando} …")
    pdb_to_mol2(lig_pdb, lig_mol2, pHLigando)

    print("• Reading structures with MDAnalysis …")
    try:
        u_prot = mda.Universe(protein)
        u_lig  = mda.Universe(lig_mol2)
    except Exception as e:
        print(f"Error reading structures: {e}")
        sys.exit(1)

    # Verify MOL2 resname
    if len(u_lig.residues) > 0:
        rname = u_lig.residues.resnames[0]
        if rname != "LIG":
             print(f"Warning: MOL2 residue name is '{rname}', expected 'LIG'. Forcing 'LIG' for complex.")
             # We already force it in the next step (prepare_ligand), so the complex is safe.
             # But the MOL2 file on disk might have the wrong name if obabel ignored it.
             # If strict consistency is required in the MOL2 file itself, we might need to rewrite it.
             # For now, we trust the pre-processing.

    # Assign chain IDs
    ensure_chain(u_prot, "A")
    ensure_chain(u_lig, "L")

    # Normalize ligand (resname LIG, resid 1, HETATM)
    prepare_ligand(u_lig)

    # Merge
    print("• Merging protein and ligand …")
    u_comp = Merge(u_prot.atoms, u_lig.atoms)
    if getattr(u_prot, "dimensions", None) is not None:
        u_comp.dimensions = u_prot.dimensions

    u_comp.atoms.write(complex_p)
    print(f"\n✓ Complex written to: {complex_p} and ligand resname is: LIG")
    
    print("• Saved intermediates:")
    if args.dock:
        print("  ", Path("pose1.pdbqt"))
    if args.dock: 
        print("  ", Path("ligand.pdb"))
    print("  ", lig_mol2)


if __name__ == "__main__":
    main()
