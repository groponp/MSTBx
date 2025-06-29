# -*- coding: utf-8 -*-

#//*****************************************************************************************//# 
# PSFGenMemb: Este módulo permite criar sistemas de proteina inserido em membrana ou para     #
#             para modelar petídeo/proteina que interage com a membrana, mas que não          #
#             esta inserido na membrana, se não que fica a uma distância dela.                #
#                                                                                             #
# autor     : Ropón-Palacios G., BSc - MSc estudante em Física Biomolecular.                  #
# afiliação : Departamento de Física, IBILCE/UNESP, São Jośe do Rio Preto, São Paulo.         #                                                  
# e-mail    : georcki.ropon@unesp.br                                                          #
# data      : Quarta-feira 12 de Junho do 2024.                                               #
# $rev$     : Rev Quarta-feira 12 de Junho de 2024                                            #                    
#//*****************************************************************************************//#

#// ****************************************************************************************//#
# Log mudanças no código:                                                                     #
#  1. Adicionando uma classe para preparar los sistemas - Quarta feira 12 de Junho 2024.      #
#  2. Atualmente só suporta fosfolipídeos, mas não acho que com colesterol tenha erro.        #
#  3. Eu modifiquei a seleção de átomos de fósforo, de name P para type PL Domingo 23 de      #
#     Junho 2024.                                                                             #
#// ****************************************************************************************//#

import os
import sys
import warnings
import time 
from ..Utils.Utils import UnixMessage 
from datetime import datetime
warnings.filterwarnings("ignore")

#// ****************************************************************************************//#
# Definição da classe  BuildMembrane                                                          #
#// ****************************************************************************************//#

class BuildMembrane:
    def __init__(self) -> None:
        pass

    def build(self, psf: str, pdb: str, salt: float, ofile: str, hmr: int, peptide: int, 
              moveZ: float):
        ''' Este método escreve um script em tcl, chamado de PSFGenMemb em  
            tcl, que permite criar sistemas de petídeo/proteína interagindo 
            com a membrana, seja inserido na membrana ou a uma distância. 
            O sistem se prepara com charmm-gui só até paso 4, cá usar PDB 
            orient e move en Z ao menos 25 A, para asegurar que não fique inserido 
            na membrana, so en caso que quer colocar a proteína o peptídeo que fique 
            a uma distância da membrana.
            Cá, além disso, com a opção  moveZ essa distância e rescalada, tomando em conta
            a distância entrada pelo o usario, a respecto  da superfície da membrana (P). 
        '''
        f = open("PSFGenMemb.tcl", "w")
        script = """\
#! Escrito por o módulo PSFGenMemb de MSTBx em %s.
#! Atualmente ele só suporta os archivos PSF/PDB de charmm-gui ou criados com 
#! PSFGen de forma independente. 

set psf %s 
set pdb %s 
set sol solvated
set output %s 
set salt %s 
set peptidemem %s

#//***************************************************************************************//#
#! Carregando o PSF e PDB                                                                  !#
#//***************************************************************************************//#
mol new $psf  type psf waitfor all 
mol addfile $pdb  type pdb waitfor all

#//***************************************************************************************//#
#! Permite rescalar sua posição em Z+ da proteína ou peptídeo a uma distância da membrana  !#
#//***************************************************************************************//#
if {$peptidemem} {
    set psf orient.psf 
    set pdb orient.pdb
    set headlipid [atomselect top \"segid MEMB and type PL and z > 0\"]
    set headcom [measure center $headlipid]
    set zheadcom [lindex $headcom 2]
    set pep [atomselect top protein]
    set pepcom [measure center $pep]
    set zpepcom [lindex $pepcom 2]

    set extended %s   ;# moveZ variable here. 
    set currentd [expr $zheadcom - zpepcom]
    set z [expr $extended - $currentd]
    $pep moveby [list 0 0 $z]

    set all [atomselect top all]
    writepsf $psf.psf
    writepdb $pdb.pdb
} 

#//***************************************************************************************//#
#! Recarregar seja a proteina ou peptídeo orientado ou não.                                !#
#//***************************************************************************************//#
mol delete all
mol new $psf 
mol addfile $pdb


#//***************************************************************************************//#
#! Calcula o tamanho da caixa de simulação                                                 !#
#//***************************************************************************************//#
set all [atomselect top \"segid MEMB and type PL or protein\"] 
set minmax [measure minmax $all]

set xylen [vecsub [lindex $minmax 1] [lindex $minmax 0]] 
set maxvec [expr {min([lindex $xylen 0],[lindex $xylen 1])}] ;# Obtener max só de XY.
set vec [expr $maxvec/2]  ;# En geral cá se adiciona 1, más eu não vou adicionar para não extender a caixa.

set zlen [vecsub [lindex $minmax 1] [lindex $minmax 0]]
set zboxpad [expr ([lindex $zlen 2] + 44)/2] ;# add 22.5 Angstrom more to Z(+/-) axis. 

set xmin [expr -1.0*$vec] ;# add 1 to make sure the equilibration.
set ymin [expr -1.0*$vec]
set zmin [expr -1.0*$zboxpad]
set boxmin [list $xmin $ymin $zmin]
 
set xmax [expr 1.0*$vec]
set ymax [expr 1.0*$vec]
set zmax [expr 1.0*$zboxpad]
set boxmax [list $xmax $ymax $zmax]

#//***************************************************************************************//#
#! Solvatação, remove bad waters e Ionização                                               !#
#//***************************************************************************************//#
package require solvate
solvate $psf $pdb -minmax [list $boxmin $boxmax] -o $sol -s W 

# Remove bad waters
mol delete all

set id [mol new $sol.psf type psf waitfor all]
mol addfile $sol.pdb type pdb waitfor all 

set all [atomselect $id all]
set badw1 [atomselect top "waters and same residue as within 3 of protein"]
#-----------------------------------------------------------------------
# Em charmm-gui os grupos fosfatos estão centrados em Z -19/+19
# então  para eliminar as moléculas de agua nas regiões hidrofóbicas da 
# membrana, usamos un cutoff de 20 A, assim também evitamos a formação de
# borbulhas. 
#-----------------------------------------------------------------------
set badw2 [atomselect top "waters and same residue as abs(z) < 19"]
$badw1 num
$badw2 num

$badw1 set beta 1
$badw2 set beta 1

set allbadwater [atomselect top "name OH2 and beta > 0"]
set seglistwater [$allbadwater get segid]
set reslistwater [$allbadwater get resid]

mol delete all
package require psfgen
resetpsf
readpsf $sol.psf
coordpdb $sol.pdb

foreach segid $seglistwater resid $reslistwater {
   	delatom $segid $resid
}

writepsf ${sol}_removeW.psf
writepdb ${sol}_removeW.pdb

#mol delete all 
package require autoionize 
autoionize -psf ${sol}_removeW.psf -pdb ${sol}_removeW.pdb -cation SOD -anion CLA -sc $salt -o ionized -seg ION

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
#! Escreve a informação do PBC                                                             !#
#//***************************************************************************************//#
mol delete all
mol new $output.pdb
mol addfile $output.psf
set wat [atomselect top \"waters\"] ;## only membrane proteins 
set all  [atomselect top \"all\"] 
set minmax [measure minmax $wat]
set vec [vecsub [lindex $minmax 1] [lindex $minmax 0]]
set A [lindex $vec 0]
set B [lindex $vec 1]
set C [lindex $vec 2]

set AB [expr {max([lindex $vec 0],[lindex $vec 1])}] 
set center [measure center $all]
set xcen [lindex $center 0]
set ycen [lindex $center 1]
set zcen [lindex $center 2]

set fout [open "step3_pbcsetup.str" w]
puts $fout "SET A = $AB"
puts $fout "SET B = $AB"
puts $fout "SET C = $C"
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
""" % (UnixMessage().date(), psf, pdb, ofile, salt, peptide, moveZ, hmr) 
        f.write(script)
        f.close()
