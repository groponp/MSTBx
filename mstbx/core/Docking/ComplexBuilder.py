"""Build a protein-ligand PDB from a docking pose."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import MDAnalysis as mda
from MDAnalysis.core.universe import Merge

from mstbx.core.Utils.Utils import UnixMessage
from mstbx.core.Utils.Validator import FormatValidator


class ComplexBuilder:
    """Normalize a docking ligand and merge it with a protein structure."""

    def __init__(self, protein_pdb, output_name):
        self.protein_pdb = Path(protein_pdb).resolve()
        self.output_name = Path(output_name).resolve()
        self.uxm = UnixMessage()

    def run_cmd(self, command):
        """Run an external conversion command without shell interpolation."""
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as error:
            detail = error.stderr.strip() or str(error)
            self.uxm.message(message=f"External command failed: {detail}", type="error")
            return False
        return True

    @staticmethod
    def extract_pose1(source: Path, destination: Path) -> None:
        """Extract `MODEL 1` from a multi-model PDBQT file."""
        in_pose = False
        found = False
        lines = []
        for line in source.read_text().splitlines():
            if line.startswith("MODEL"):
                in_pose = line.split()[1:] == ["1"]
                found = found or in_pose
            if in_pose:
                lines.append(line)
            if in_pose and line.startswith("ENDMDL"):
                break
        if not found or not any(line.startswith(("ATOM", "HETATM")) for line in lines):
            raise ValueError(f"PDBQT does not contain a usable MODEL 1: {source}")
        destination.write_text("\n".join(lines) + "\n")

    def pdbqt_to_pdb(self, source: Path, destination: Path) -> None:
        """Convert one PDBQT pose to PDB with Open Babel."""
        if not self.run_cmd(["obabel", "-ipdbqt", str(source), "-opdb", "-O", str(destination), "-d"]):
            raise RuntimeError("Open Babel could not convert the PDBQT pose.")

    def pdb_to_mol2(self, source: Path, destination: Path, ph: float) -> None:
        """Convert a normalized ligand PDB to MOL2 with Gasteiger charges."""
        command = [
            "obabel", "-ipdb", str(source), "-omol2", "-O", str(destination),
            "--partialcharge", "gasteiger", "-p", str(ph), "-d",
        ]
        if not self.run_cmd(command):
            raise RuntimeError("Open Babel could not generate the ligand MOL2.")

    @staticmethod
    def ensure_chain(universe: mda.Universe, chain_id: str) -> None:
        """Assign one PDB chain identifier to every atom in a universe."""
        if not hasattr(universe.atoms, "chainIDs"):
            universe.add_TopologyAttr("chainIDs", [""] * len(universe.atoms))
        universe.atoms.chainIDs = [chain_id] * len(universe.atoms)

    @staticmethod
    def prepare_ligand(universe: mda.Universe) -> None:
        """Normalize ligand records to HETATM/LIG/resid 1."""
        if not hasattr(universe.atoms, "record_types"):
            universe.add_TopologyAttr("record_types", ["HETATM"] * len(universe.atoms))
        universe.atoms.record_types = ["HETATM"] * len(universe.atoms)
        universe.residues.resnames = ["LIG"] * len(universe.residues)
        universe.residues.resids = [1] * len(universe.residues)

    def build(self, ligand_input, ligand_pH=7.4, is_pdbqt=True):
        """Build and validate a protein-ligand complex PDB."""
        if not self.protein_pdb.is_file():
            raise FileNotFoundError(f"Protein PDB not found: {self.protein_pdb}")
        ligand_input = Path(ligand_input).resolve()
        if not ligand_input.is_file():
            raise FileNotFoundError(f"Ligand input not found: {ligand_input}")
        self.output_name.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix=".mkdocking-", dir=self.output_name.parent) as temp:
            work = Path(temp)
            ligand_pdb = ligand_input
            if is_pdbqt:
                pose = work / "pose1.pdbqt"
                self.extract_pose1(ligand_input, pose)
                ligand_pdb = work / "ligand.pdb"
                self.pdbqt_to_pdb(pose, ligand_pdb)

            normalized = work / "ligand_LIG.pdb"
            ligand = mda.Universe(ligand_pdb)
            self.prepare_ligand(ligand)
            ligand.atoms.write(normalized)

            mol2 = work / "ligand.mol2"
            self.pdb_to_mol2(normalized, mol2, ligand_pH)
            valid, report = FormatValidator.validate(mol2)
            if not valid:
                raise ValueError(f"Open Babel generated invalid MOL2: {report}")

            protein = mda.Universe(self.protein_pdb)
            converted_ligand = mda.Universe(mol2)
            self.ensure_chain(protein, "A")
            self.ensure_chain(converted_ligand, "L")
            self.prepare_ligand(converted_ligand)
            complex_universe = Merge(protein.atoms, converted_ligand.atoms)
            if protein.dimensions is not None:
                complex_universe.dimensions = protein.dimensions
            complex_universe.atoms.write(self.output_name)
        return True
