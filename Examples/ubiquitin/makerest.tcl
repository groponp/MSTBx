set psf 01build/ubq.psf 
set pdb 01build/ubq.pdb 

mol new $psf
mol addfile $pdb 

set all [atomselect top "all"] 
$all set beta 0 
set restraints [atomselect top "(protein and backbone) or (segid HETA and noh)"] 
$restraints set beta 5 ;# Set force constant k=5 kcal/mol for restraint atoms
$all writepdb restraints/prot_posres.ref
quit
