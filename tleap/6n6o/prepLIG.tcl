mol new 6N6O.pdb
set lig [atomselect top "resname KE7"] 
$lig set resname LIG
$lig writepdb LIG.pdb
exec obabel LIG.pdb -O LIGX.mol2 -p 7 
exec sed -i "s/UNL/LIG/g" LIGX.mol2
quit 