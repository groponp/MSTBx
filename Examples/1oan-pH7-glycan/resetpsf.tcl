mol new step1_pdbreader.psf 
mol addfile step1_pdbreader.pdb 

set all [atomselect top all] 
$all writepdb new.pdb 
$all writepsf new.psf 
quit 
