#! Escrito por o módulo PSFGenSol de MSTBx em 07/27/2024 00:47:56.251060.
#! Atualmente ele só suporta os archivos PSF/PDB de charmm-gui ou criados com 
#! PSFGen de forma independente. 

set psf step1_pdbreader.psf 
set pdb step1_pdbreader.pdb 
set sol solvated
set output mol 
set salt 0.15 

#//***************************************************************************************//#
#! Calcula o tamanho da caixa de simulação                                                 !#
#//***************************************************************************************//#
mol new $psf  type psf waitfor all 
mol addfile $pdb  type pdb waitfor all 

set model [atomselect top "all"] 
set center [measure center $model] 
#! note: não uso -withradii para calcular o minmax.
set dimens [vecsub [lindex [measure minmax $model ] 1] [lindex [measure minmax $model ] 0]]
set maxvec [expr {max([lindex $dimens 0],[lindex $dimens 1],[lindex $dimens 2])}]

set boxpad 15  ;# Adicione un espaço extra de ao menos 15 A para evitar PBC self interaction. 

set max [expr round([expr round($maxvec)] + 2*$boxpad) + 1]
set boxlen [expr $max/2] ; # Length of cubic box vector
set minx [expr [lindex $center 0] - $boxlen] ;#! Caixa mímina.
set miny [expr [lindex $center 1] - $boxlen]
set minz [expr [lindex $center 2] - $boxlen]
set boxmin [list $minx $miny $minz]

set maxx [expr [lindex $center 0] + $boxlen] ;#! Caixa máxima. 
set maxy [expr [lindex $center 1] + $boxlen]
set maxz [expr [lindex $center 2] + $boxlen]
set boxmax [list $maxx $maxy $maxz]

#//***************************************************************************************//#
#! Escreve a informação do PBC                                                             !#
#//***************************************************************************************//#
set fout [open "step3_pbcsetup.str" w]
puts $fout "SET A = [expr $boxlen * 2]"
puts $fout "SET B = [expr $boxlen * 2]"
puts $fout "SET C = [expr $boxlen * 2]"

#//***************************************************************************************//#
#! Solvatação e Ionização                                                                  !#
#//***************************************************************************************//#
package require solvate
solvate $psf $pdb -minmax [list $boxmin $boxmax] -o $sol -s W 

mol delete all 
package require autoionize 
autoionize -psf $sol.psf -pdb $sol.pdb -cation SOD -anion CLA -sc $salt -o ionized -seg ION

#//***************************************************************************************//#
#! Recentrando o sistema para o origem 0,0,0                                               !#
#//***************************************************************************************//#
mol delete all 
mol new ionized.psf 
mol addfile ionized.pdb type pdb waitfor all
set all [atomselect top all]
set center [measure center $all]
set move_dist [transoffset [vecsub {0 0 0} $center]]
$all move $move_dist
$all writepdb $output.pdb 
$all writepsf $output.psf

#//***************************************************************************************//#
#! Calcula o centro da caixa para o CellOrigin do PBC                                      !#
#//***************************************************************************************//#
# calculte center box
mol delete all
mol new $output.pdb
mol addfile $output.psf
set all [atomselect top all]
set center [measure center $all]
set xcen [lindex $center 0]
set ycen [lindex $center 1]
set zcen [lindex $center 2]

#//***************************************************************************************//#
#! Finalizando para escrever a informação para o PBC                                       !#
#//***************************************************************************************//#
puts $fout "SET XCEN  = $xcen"
puts $fout "SET YCEN  = $ycen"
puts $fout "SET ZCEN  = $zcen"
close $fout 

#//***************************************************************************************//#
#! Favorece usar repartição de massas de hidrogênio (HMR)                                  !#
#//***************************************************************************************//#
if {0} {
    mol delete all 
    package require psfgen
    psfcontext reset
    readpsf $output.psf pdb $output.pdb
    hmassrepart
    writepsf $output.hmr.psf
    writepdb $output.hmr.pdb
}

#//***************************************************************************************//#
#! Finaliza o script e fecha VMD                                                           !#
#//***************************************************************************************//#
quit
