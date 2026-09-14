"""Build a protein-ligand PDB from a docking pose."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import MDAnalysis as mda

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
        """Convert a normalized ligand PDB to MOL2 with Gasteiger charges.

        `--title LIG` pins the MOL2 MOLECULE name to `LIG`. Without it, Open
        Babel falls back to the source file's path as the title (the ligand
        PDB lives in a temp working directory, so the title becomes a
        throwaway path like `/tmp/.../ligand_LIG.pdb`). CGenFF Web uses that
        MOLECULE title as the RESI name in the returned .str file, so an
        unset title produces a RESI like `/tmp/cla` (truncated path) instead
        of `LIG`, which then cannot match the `LIG` residue name written into
        the complex PDB, breaking `topogmx`/CHARMM-GUI parameter assignment.
        """
        command = [
            "obabel", "-ipdb", str(source), "-omol2", "-O", str(destination),
            "--partialcharge", "gasteiger", "-p", str(ph), "-d", "--title", "LIG",
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

    def ligand_mol2_path(self) -> Path:
        """Path of the persisted ligand MOL2, next to the complex output."""
        return self.output_name.with_name(f"{self.output_name.stem}_ligand.mol2")

    @staticmethod
    def _splice_complex(protein_pdb: Path, ligand_pdb: Path, output: Path) -> None:
        """Append the ligand as text after the protein's own atom records.

        The protein is never reloaded through MDAnalysis here. `pdb2pqr`
        --ffout CHARMM writes 4-letter residue names (ASPP, GLUP, CTER, NTER)
        starting one column early, in the PDB altLoc slot (columns 18-21
        instead of the strict 18-20), e.g. altLoc='A' resName='SPP' for
        'ASPP'. A strict fixed-column reader like MDAnalysis truncates the
        leading letter, and writing that universe back out bakes the
        corrupted resName (SPP, TER) into the final complex, which CHARMM-GUI
        then reports as unrecognized/engineered residues. Splicing raw text
        keeps the protein's original bytes, chains, and CHARMM residue names
        untouched; only the ligand (resName LIG, 3 letters, no CHARMM
        4-letter names involved) goes through MDAnalysis.
        """
        protein_lines = [
            line for line in protein_pdb.read_text().splitlines()
            if line.startswith(("ATOM", "HETATM", "TER", "CRYST1"))
        ]
        if not any(line.startswith(("ATOM", "HETATM")) for line in protein_lines):
            raise ValueError(f"No ATOM/HETATM records found in protein PDB: {protein_pdb}")

        max_serial = 0
        for line in protein_lines:
            if line.startswith(("ATOM", "HETATM")):
                try:
                    max_serial = max(max_serial, int(line[6:11]))
                except ValueError:
                    pass

        if not protein_lines[-1].startswith("TER"):
            last_atom = next(line for line in reversed(protein_lines) if line.startswith(("ATOM", "HETATM")))
            max_serial += 1
            # resName (columns 18-20) is left blank: it is optional in a TER
            # record, and reading it from the last atom line would hit the
            # same CHARMM 4-letter-name column overflow described above.
            # chainID/resSeq are safe to reuse, they are not shifted by it.
            ter = f"TER   {max_serial:>5d}      {'':3s} {last_atom[21]}{last_atom[22:26]}"
            protein_lines.append(ter)

        ligand_lines = []
        for line in ligand_pdb.read_text().splitlines():
            if not line.startswith(("ATOM", "HETATM")):
                continue
            max_serial += 1
            ligand_lines.append(f"HETATM{max_serial:>5d}" + line[11:])

        output.write_text("\n".join(protein_lines + ligand_lines) + "\nEND\n")

    def build(self, ligand_input, ligand_pH=7.4, is_pdbqt=True):
        """Build and validate a protein-ligand complex PDB and ligand MOL2.

        CHARMM-GUI's PDB Reader & Manipulator and Ligand Reader & Modeler need
        both artifacts: the combined PDB and a standalone, Gasteiger-charged
        ligand MOL2. Both are written next to `output_name`.
        """
        if not self.protein_pdb.is_file():
            raise FileNotFoundError(f"Protein PDB not found: {self.protein_pdb}")
        ligand_input = Path(ligand_input).resolve()
        if not ligand_input.is_file():
            raise FileNotFoundError(f"Ligand input not found: {ligand_input}")
        self.output_name.parent.mkdir(parents=True, exist_ok=True)
        ligand_mol2 = self.ligand_mol2_path()

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

            converted_ligand = mda.Universe(mol2)
            self.ensure_chain(converted_ligand, "L")
            self.prepare_ligand(converted_ligand)
            ligand_only = work / "ligand_only.pdb"
            converted_ligand.atoms.write(ligand_only)

            self._splice_complex(self.protein_pdb, ligand_only, self.output_name)
            shutil.copy2(mol2, ligand_mol2)
        return {"complex": self.output_name, "ligand_mol2": ligand_mol2}
