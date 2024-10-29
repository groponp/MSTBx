#! A simple tool para reset the psf and make compatible CHARMM PSF and NAMD PSF. 

import sys 
import os 

psf = sys.argv[1]
pdb = sys.argv[2]

print("[   ] INFO reset the PSF/PDB.")
fout = open("resetpsf.tcl", "w")
script = """\
package require psfgen 
resetpsf 
readpsf %s 
coordpdb %s 
vpbonds 1
writepsf x-plor reset.psf 
writepdb reset.pdb     
quit
""" % (psf, pdb)

fout.write(script)
fout.close() 

os.system("vmd -dispdev text -e resetpsf.tcl")

