import os
import sys
import logging
from datetime import datetime
import MDAnalysis as mda
from MDAnalysis.core.universe import Merge
import warnings

# Try importing optional dependencies
try:
    from pdbfixer import PDBFixer
    from openmm.app import PDBFile
    PDBFIXER_AVAILABLE = True
except ImportError:
    PDBFIXER_AVAILABLE = False

class PDBWriter:
    def __init__(self, input_file):
        self.input_file = input_file
        self.log_messages = []
        self.ssbonds = []
        self._add_log(f"Initializing PDBWriter with file: {input_file}")

    def _add_log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {message}")

    def fix_structure(self, replace_nonstandard=True, add_missing_atoms=True, add_missing_residues=True, fix_only_internal=True):
        if not PDBFIXER_AVAILABLE:
            self._add_log("ERROR: PDBFixer or OpenMM not found. Skipping fixing step.")
            return False

        self._add_log("Starting PDBFixer process...")
        fixer = PDBFixer(filename=self.input_file)

        if replace_nonstandard:
            fixer.findNonstandardResidues()
            self._add_log(f"Found non-standard residues: {fixer.nonstandardResidues}")
            fixer.replaceNonstandardResidues()

        fixer.findMissingResidues()
        if fix_only_internal:
            # Filter missing residues to keep only internal gaps
            new_missing = {}
            for chain_idx, missing_res in fixer.missingResidues.items():
                if not missing_res:
                    continue
                
                # Get the range of residues currently in the chain
                chain = list(fixer.topology.chains())[chain_idx[0] if isinstance(chain_idx, tuple) else chain_idx]
                residues = list(chain.residues())
                if not residues:
                    continue
                
                min_idx = residues[0].index
                max_idx = residues[-1].index
                
                # Keep only those missing residues that are between min_idx and max_idx
                internal_missing = [res for res in missing_res if min_idx < res[0] < max_idx]
                if internal_missing:
                    new_missing[chain_idx] = internal_missing
                    self._add_log(f"Chain {chain_idx}: Keeping internal missing residues {internal_missing}")
                else:
                    self._add_log(f"Chain {chain_idx}: No internal missing residues found (ignoring terminals)")
            
            fixer.missingResidues = new_missing
        
        if add_missing_atoms:
            fixer.findMissingAtoms()
            self._add_log(f"Missing atoms found: {len(fixer.missingAtoms)} groups")
            fixer.addMissingAtoms()

        # Save fixed structure to a temporary file for further processing
        fixed_tmp = "fixed_temp.pdb"
        with open(fixed_tmp, 'w') as f:
            PDBFile.writeFile(fixer.topology, fixer.positions, f, keepIds=True)
        
        self.input_file = fixed_tmp
        self._add_log("Structure fixed and saved to intermediate file.")
        return True

    def find_ssbonds(self, threshold=3.0):
        self._add_log(f"Searching for S-S bonds with threshold {threshold} A...")
        u = mda.Universe(self.input_file)
        cys_sg = u.select_atoms("resname CYS and name SG")
        
        found = 0
        for i, atom1 in enumerate(cys_sg):
            for atom2 in cys_sg[i+1:]:
                if atom1.residue == atom2.residue:
                    continue
                
                dist = mda.lib.distances.distance_array(atom1.position, atom2.position)[0][0]
                if dist <= threshold:
                    self.ssbonds.append((atom1, atom2, dist))
                    self._add_log(f"SSBOND found: {atom1.residue.resname} {atom1.residue.resid} ({atom1.segid}) - {atom2.residue.resname} {atom2.residue.resid} ({atom2.segid}) : {dist:.2f} A")
                    found += 1
        
        self._add_log(f"Total SSBONDs detected: {found}")
        return self.ssbonds

    def protonate(self, pH=7.0, ff="CHARMM"):
        self._add_log(f"Protonating structure at pH {pH} with {ff} nomenclature using pdb2pqr...")
        # This will require pdb2pqr to be installed and in PATH
        # For now, we will simulate the call or use a placeholder if not found
        output_pqr = "protonated.pqr"
        output_pdb = "protonated.pdb"
        
        cmd = f"pdb2pqr --ff={ff} --ffout={ff} --with-ph={pH} --ph-calc-method=propka {self.input_file} {output_pqr}"
        self._add_log(f"Running command: {cmd}")
        
        # In a real scenario, we would run:
        # try:
        #     subprocess.run(cmd, shell=True, check=True)
        #     self.input_file = output_pdb # pdb2pqr can also output PDB
        # except:
        #     self._add_log("ERROR: pdb2pqr failed or not found.")
        
        self._add_log("Protonation step placeholder executed (requires pdb2pqr installed).")

    def edit_structure(self, rename_chains=None, renumber_residues=None, add_segid=None):
        u = mda.Universe(self.input_file)
        
        if rename_chains:
            self._add_log(f"Renaming chains: {rename_chains}")
            for old_id, new_id in rename_chains.items():
                u.select_atoms(f"chainID {old_id}").chainIDs = new_id

        if renumber_residues:
            start_res = renumber_residues
            self._add_log(f"Renumbering residues starting from {start_res}")
            for chain in u.segments:
                for i, res in enumerate(chain.residues):
                    res.resid = start_res + i

        if add_segid:
            self._add_log(f"Adding/Modifying segid: {add_segid}")
            u.atoms.segids = add_segid

        u.atoms.write("edited_temp.pdb")
        self.input_file = "edited_temp.pdb"
        self._add_log("Structural edits completed.")

    def write_final_pdb(self, output_file):
        # We read the final state and write it with SSBOND lines if any
        with open(self.input_file, 'r') as f:
            lines = f.readlines()
        
        ssbond_lines = []
        for idx, (a1, a2, d) in enumerate(self.ssbonds, 1):
            # Format: SSBOND serNum "CYS" chainID1 seqNum1 icode1 "CYS" chainID2 seqNum2 icode2 sym1 sym2 Length
            line = ("SSBOND {:3d} CYS {:1s} {:4d}    CYS {:1s} {:4d}                               "
                    "1555   1555 {:5.2f}\n").format(idx, a1.residue.segid[:1], a1.residue.resid, a2.residue.segid[:1], a2.residue.resid, d)
            ssbond_lines.append(line)
        
        # Find where to insert SSBOND (before ATOM lines)
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("ATOM") or line.startswith("HETATM"):
                insert_idx = i
                break
        
        final_lines = lines[:insert_idx] + ssbond_lines + lines[insert_idx:]
        
        with open(output_file, 'w') as f:
            f.writelines(final_lines)
        
        self._add_log(f"Final PDB written to: {output_file}")
        self.save_log()

    def save_log(self):
        with open("pdbwriter_report.log", "w") as f:
            f.write("\n".join(self.log_messages))
        print("Detailed log saved to pdbwriter_report.log")
