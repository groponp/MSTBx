# -*- coding: utf-8 -*-

#//*****************************************************************************************//# 
# PSFGenSol : Este módulo permite criar sistemas em solução.                                  #
#             Ex proteína, peptídeos ou ligantes em agua e íons.                              #
#                                                                                             #
# autor     : Ropón-Palacios G., BSc - MSc estudante em Física Biomolecular.                  #
# afiliação : Departamento de Física, IBILCE/UNESP, São Jośe do Rio Preto, São Paulo.         #                                                  
# e-mail    : georcki.ropon@unesp.br                                                          #
# data      : Quarta-feira 12 de Junho do 2024.                                               #
# $rev$     : PASS Quarta feira 12 de Junho de 2024                                           #                    
#//*****************************************************************************************//#

#// ****************************************************************************************//#
# Log mudanças no código:                                                                     #
#  1. Adicionando uma classe para preparar los sistemas - Quarta feira 12 de Junho 2024.      #
#// ****************************************************************************************//#

import os
import sys
import warnings
import time 
from Utils import UnixMessage 
from datetime import datetime
warnings.filterwarnings("ignore")

#// ****************************************************************************************//#
# Definição da classe  BuildSolution                                                          #
#// ****************************************************************************************//#

class BuildSolution: 
    def __init__(self) -> None:
         pass 
    
    def build(self, psf: str, pdb: str, salt: float, ofile: str, hmr: int):
        ''' Este método escreve um script em tcl, chamado de PSFGenSol em  
            tcl, que vai fazer a solvatção é ionização do sistema. 
            para esta tarefa aproveitando as capacidades de VMD. 
        '''
        f = open("PSFGenSol.tcl", "w")
        tclscript = """\
#! Escrito por o módulo PSFGenSol de MSTBx em %s.
#! Atualmente ele só suporta os archivos PSF/PDB de charmm-gui ou criados com 
#! PSFGen de forma independente. 

set psf %s 
set pdb %s 
set sol solvated
set output %s 
set salt %s 

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
if {%s} {
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
""" % (UnixMessage().date(), psf, pdb, ofile, salt, hmr) 
        f.write(tclscript)
        f.close()


#// ****************************************************************************************//#
# Definição da classe  BuildSolutionSMD                                                       #
#// ****************************************************************************************//#

class BuildSolutionSMD: 
    def __init__(self) -> None:
         pass 
    
    def build(self, psf: str, pdb: str, salt: float, ofile: str, hmr: int, atomsvec1: str, atomsvec2: str, extrapadz: float):
        ''' Este método escreve um script em tcl, chamado de PSFGenSolSMD em  
            tcl, que vai fazer a solvatção é ionização do sistema para fazer simulações de SMD.
            para esta tarefa aproveitando as capacidades de VMD. 
        '''
        f = open("PSFGenSolSMD.tcl", "w")
        tclscript = """\
#! Escrito por o módulo PSFGenSol de MSTBx em %s.
#! Atualmente ele só suporta os archivos PSF/PDB de charmm-gui ou criados com 
#! PSFGen de forma independente. 

set psf %s 
set pdb %s 
set sol solvated
set output %s 
set salt %s 
set atomsanchor \"%s\" 
set atomspull \"%s\" 
set extraZ    %s

#//***************************************************************************************//#
#! Oriente as móleculas em Z                                                               !#
#//***************************************************************************************//#

mol new $psf  type psf waitfor all 
mol addfile $pdb  type pdb waitfor all 

set selall [atomselect top all]
set selanchor [atomselect top \"$atomsanchor\"] 
set selpulling [atomselect top \"$atomspull\"]
set anchor [measure center $selanchor]
set pulling [measure center $selpulling]
        
## This align the system in two steps: transvecinv rotates the vector
## to be along the x axis, and then transaxis rotates about the y axis to
## align your vector with z. 
## By Peter Freddolino (http://www.ks.uiuc.edu/Research/vmd/mailing_list/vmd-l/6725.html)
set axis [vecsub $pulling $anchor]
$selpulling delete
$selanchor delete
set M [transvecinv $axis] 
$selall move $M 
set M [transaxis y -90] 
$selall move $M 
$selall writepdb orientedtoZ.pdb 
mol delete all

#//***************************************************************************************//#
#! Calcula o tamanho da caixa de simulação                                                 !#
#//***************************************************************************************//#
mol new $psf  type psf waitfor all 
mol addfile orientedtoZ.pdb  type pdb waitfor all 

set model [atomselect top "all"] 
set center [measure center $model] 
set dimens [vecsub [lindex [measure minmax $model -withradii] 1] [lindex [measure minmax $model -withradii] 0]]
set maxvec [expr {max([lindex $dimens 0],[lindex $dimens 1],[lindex $dimens 2])}]

set boxpad 15  ;# Adicione un espaço extra de ao menos 15 A para evitar PBC self interaction. 

#---------------------------------------------------------------------------------
#! Nota: Adicionamos 7.5 angstroms a cada lado de xy para dar espaço ao pulling
#!       se ele vai por lado lateral durante o pull em Z. 
#---------------------------------------------------------------------------------
set max [expr round([expr round($maxvec)] + 2*$boxpad) + 1]
set boxlen [expr $max/2] ; # Length of cubic box vector
set minx [expr [lindex $center 0] - $boxlen - 7.5] ;#! Caixa mímina.
set miny [expr [lindex $center 1] - $boxlen - 7.5]
set minz [expr [lindex $center 2] - $boxlen] ;#! Só para ajustar na parte inferior adicionamos, e não restamos.
set boxmin [list $minx $miny $minz]

set maxx [expr [lindex $center 0] + $boxlen + 7.5] ;#! Caixa máxima. 
set maxy [expr [lindex $center 1] + $boxlen + 7.5]
set maxz [expr [lindex $center 2] + $boxlen + $extraZ]
set boxmax [list $maxx $maxy $maxz]

#//***************************************************************************************//#
#! Escreve a informação do PBC                                                             !#
#//***************************************************************************************//#
set fout [open "step3_pbcsetup.str" w]
puts $fout "SET A = [expr $boxlen * 2]"
puts $fout "SET B = [expr $boxlen * 2]"
puts $fout "SET C = [expr $boxlen * 2 + $extraZ]"

#//***************************************************************************************//#
#! Solvatação e Ionização                                                                  !#
#//***************************************************************************************//#
package require solvate
solvate $psf orientedtoZ.pdb -minmax [list $boxmin $boxmax] -o $sol -s W 

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
if {%s} {
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
""" % (UnixMessage().date(), psf, pdb, ofile, salt, atomsvec1, atomsvec2, extrapadz, hmr) 
        f.write(tclscript)
        f.close()
