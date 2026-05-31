set psf 01build/aqp.psf 
set pdb 01build/aqp.pdb 

mol new $psf
mol addfile $pdb 

set all [atomselect top "all"] 
$all set beta 0 
set lipid [atomselect top "(protein) or (segid MEMB and type PL) or (segid HETA and noh) or waters or ions"] 
$lipid set beta 5               ;# Set force constant k=5 kcal/mol for restraint atoms
$all writepdb restraints/meltlipid.ref 

set all [atomselect top "all"]
$all set beta 0 
set protein [atomselect top "protein or (segid HETA and noh)"]
$protein set beta 5 
$all writepdb restraints/protein.ref

set all [atomselect top "all"]
$all set beta 0
set backbone [atomselect top "(protein and backbone) or (segid HETA and noh)"]
$backbone set beta 5
$all writepdb restraints/backbone.ref 

quit
