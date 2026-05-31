from pdbfixer import PDBFixer
from openmm.app import PDBFile
import os 

fixer = PDBFixer(filename='6N6O.pdb')
fixer.findMissingResidues()
chains = list(fixer.topology.chains())
keys = list(fixer.missingResidues.keys())
for key in keys:
    chain = chains[key[0]]
    if key[1] == 0 or key[1] == len(list(chain.residues())):
        del fixer.missingResidues[key]
fixer.findNonstandardResidues()
fixer.replaceNonstandardResidues()
fixer.removeHeterogens(True)
fixer.findMissingAtoms()
fixer.addMissingAtoms()
PDBFile.writeFile(fixer.topology, fixer.positions, open('tmp.fix.pdb', 'w'))
os.system("grep -v -e 'HOH' tmp.fix.pdb > 6N6O.fix.pdb")


