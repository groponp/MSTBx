import os
import sys
import subprocess
from pathlib import Path
import MDAnalysis as mda
from MDAnalysis.core.universe import Merge
import warnings

class ComplexBuilder:
    def __init__(self, protein_pdb, output_name):
        self.protein_pdb = Path(protein_pdb).resolve()
        self.output_name = Path(output_name).resolve()
        
        # Suppress MDAnalysis warnings
        warnings.filterwarnings("ignore", category=UserWarning, module="MDAnalysis.coordinates.PDB")
        warnings.filterwarnings("ignore", category=UserWarning, module="MDAnalysis.topology.PDBParser")

    def run_cmd(self, cmd):
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing: {cmd}")
            return False
        return True

    def extract_pose1(self, src: Path, dst: Path):
        awk = r"/^MODEL[[:space:]]+1/,/^ENDMDL/ {print}"
        os.system(f"awk '{awk}' {src} > {dst}")

    def pdbqt_to_pdb(self, src: Path, dst: Path):
        return self.run_cmd(f"obabel -ipdbqt {src} -opdb -O {dst} -d")

    def pdb_to_mol2(self, src: Path, dst: Path, pH: float):
        return self.run_cmd(f"obabel -ipdb {src} -omol2 -O {dst} --partialcharge gasteiger -p {pH} -d")

    def ensure_chain(self, u: mda.Universe, chain_id: str):
        if "chainIDs" not in u.atoms.names:
            u.add_TopologyAttr("chainIDs", [""] * len(u.atoms))
        u.atoms.chainIDs = [chain_id] * len(u.atoms)

    def prepare_ligand(self, u: mda.Universe):
        n_atoms = len(u.atoms)
        n_res = len(u.residues)
        
        if "record_types" not in u.atoms.names:
            u.add_TopologyAttr("record_types", ["HETATM"] * n_atoms)
        u.atoms.record_types = ["HETATM"] * n_atoms

        if not hasattr(u.residues, 'resnames'):
            u.add_TopologyAttr("resnames", ["LIG"] * n_res, elements="residues")
        u.residues.resnames = ["LIG"] * n_res
        
        if not hasattr(u.residues, 'resids'):
            u.add_TopologyAttr("resids", [1] * n_res, elements="residues")
        u.residues.resids = [1] * n_res

    def build(self, ligand_input, ligand_pH=7.4, is_pdbqt=True):
        lig_pdb = Path("ligand_tmp.pdb")
        lig_mol2 = Path("ligand_tmp.mol2")

        if is_pdbqt:
            pose1_qt = Path("pose1_tmp.pdbqt")
            self.extract_pose1(Path(ligand_input), pose1_qt)
            self.pdbqt_to_pdb(pose1_qt, lig_pdb)
        else:
            lig_pdb = Path(ligand_input)

        # Normalize resname to LIG before MOL2 conversion
        u_tmp = mda.Universe(lig_pdb)
        self.prepare_ligand(u_tmp)
        lig_pdb_normalized = Path("ligand_LIG_tmp.pdb")
        u_tmp.atoms.write(lig_pdb_normalized)
        
        self.pdb_to_mol2(lig_pdb_normalized, lig_mol2, ligand_pH)

        u_prot = mda.Universe(self.protein_pdb)
        u_lig = mda.Universe(lig_mol2)

        self.ensure_chain(u_prot, "A")
        self.ensure_chain(u_lig, "L")
        self.prepare_ligand(u_lig)

        u_comp = Merge(u_prot.atoms, u_lig.atoms)
        if getattr(u_prot, "dimensions", None) is not None:
            u_comp.dimensions = u_prot.dimensions

        u_comp.atoms.write(self.output_name)
        
        # Cleanup
        for f in ["pose1_tmp.pdbqt", "ligand_tmp.pdb", "ligand_LIG_tmp.pdb", "ligand_tmp.mol2"]:
            if os.path.exists(f): os.remove(f)
            
        return True
