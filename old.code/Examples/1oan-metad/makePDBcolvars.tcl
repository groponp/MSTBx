set psf 01build/mol.psf 
set pdb 01build/mol.pdb 
set selp1 "segid PROA and name CA"
set selp2 "segid PROB and name CA"
set dunbind 50.0


mol new $psf
mol addfile $pdb 

set all [atomselect top "all"] 
$all set beta 0 
set p1 [atomselect top "$selp1"]
$p1 set beta 1.0
$all writepdb 04md/P1.pdb 

set all [atomselect top "all"]
$all set beta 0 
set p2 [atomselect top "$selp2"]
$p2 set beta 1.0      
$all writepdb 04md/P2.pdb 

# Calcular a distância entre as duas moléculas
set p1cm [atomselect top $selp1]
set p2cm [atomselect top $selp2]

set cm1 [measure center $p1cm]
set cm2 [measure center $p2cm]
set d [vecdist $cm1 $cm2]

# lower and upper boundaries. 
set lb [format "%.2f" [expr $d - 1.0]]              ;# Eu subtraio -1 ou adiciono + 1 para dar um espaço extra na variável coletiva. 
set ub [format "%.2f" [expr $d + $dunbind + 1.0]]


exec sed -i -e "s/xa/$lb/g" 04md/wtmetad.in
exec sed -i -e "s/xb/$ub/g" 04md/wtmetad.in
exec sed -i -e "s/xc/$lb/g" 04md/wtmetad.in
exec sed -i -e "s/xd/$ub/g" 04md/wtmetad.in

quit 
