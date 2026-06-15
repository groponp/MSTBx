set psf 01build/mol.psf 
set pdb 01build/mol.pdb 
set selpull "resid 100"
set selanchor "resid 1"  
set targetcenter 50.0 

mol new $psf
mol addfile $pdb 

set all [atomselect top "all"] 
$all set beta 0 
set pullAtom [atomselect top "$selpull"]
$pullAtom set beta 1.0
$all writepdb 04md/PullAtom.pdb 

set all [atomselect top "all"]
$all set beta 0 
set AnchorAtom [atomselect top "$selanchor"]
$AnchorAtom set beta 5.0       ;# kcal/mol/A² 
$all writepdb 04md/AnchorAtom.pdb 

set centerpull [lindex [measure center [atomselect top "$selpull"] ] 2]
set restraintcenter [lindex [measure center [atomselect top "$selanchor"]] 2]
set targetcom [expr $centerpull + $targetcenter]

exec sed -i -e "s/xcenter/$centerpull/g" 04md/smd.in 
exec sed -i -e "s/xtarget/$targetcom/g" 04md/smd.in 

quit 
