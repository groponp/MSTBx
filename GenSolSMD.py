# -*- coding: utf-8 -*-

#//*****************************************************************************************//# 
# PSFGenSol_SMD : Este módulo permite criar sistemas em solução para fazer simulações de      #
#             dinâmica molecular de Estiramento                                               #
#                                                                                             #
# autor     : Ropón-Palacios G., BSc - MSc estudante em Física Biomolecular.                  #
# afiliação : Departamento de Física, IBILCE/UNESP, São Jośe do Rio Preto, São Paulo.         #                                                  
# e-mail    : georcki.ropon@unesp.br                                                          #
# data      : Quarta-feira 12 de Junho do 2024.                                               #
# $rev$     : $rev$     : PASSS - all OK  Sexta-feira 14 de Junho de 2024.                   #                    
#//*****************************************************************************************//#

#// ****************************************************************************************//#
# Log mudanças no código:                                                                     #
#  1. Adicionando uma classe para preparar los sistemas - Sexta feira 14 de Junho 2024.      #
#// ****************************************************************************************//#

import os 
import sys 
import optparse 
from datetime import datetime
import warnings
import time 
warnings.filterwarnings("ignore")

#// ****************************************************************************************//#
# Importando meus módulos                                                                     #
#// ****************************************************************************************//#
from LIB.Build.PSFGenSol import BuildSolutionSMD
from LIB.Utils import UnixMessage 

#// ****************************************************************************************//#
# Configurando a informação das opções                                                        #
#// ****************************************************************************************//#
disclaimer="GenSol SMD Module from MSTBx"
parser = optparse.OptionParser(description=disclaimer) 

inputs_group = optparse.OptionGroup(parser, "Input Options")
inputs_group.add_option("--psf", help="PSF file of your system", type=str)
inputs_group.add_option("--pdb", help="PDB file of your system", type=str)
inputs_group.add_option("--salt", help="Select salt concentration of your system in mol/L unit. Defautl 0.150 mol/L.", 
                        type=float, default=0.150, dest="salt")
inputs_group.add_option("--atoms_anchor", help="Select in VMD syntax the first anchor atom group to orient the molecule. Example: \"segid PROA and resid 10\".", 
                        type=str, dest="atomsvec1", action="store")
inputs_group.add_option("--atoms_pull", help="Same as \"--atomsvec2\". Example: \"segid PROB and resid 20\" the pull atom group.", 
                        type=str, dest="atomsvec2", action="store")
inputs_group.add_option("--extra_space", help="Extra space to add in Z axis and enable pull. Default 50 Angstroms.", 
                        type=float, dest="extraspace", default=50)
parser.add_option_group(inputs_group)


outputs_group = optparse.OptionGroup(parser, "Output Options")
outputs_group.add_option("--hmr", help="Enable Hydrogen mass repartition option. Optional.", 
                         action="store_true")
outputs_group.add_option("--ofile", help="Prefix of the output file. Example: macromol150mM. Default macromol150mM.", 
                        type=str, default="macromol150mM", dest="ofile")
parser.add_option_group(outputs_group)
options, args = parser.parse_args() 


#// ****************************************************************************************//#
# Cá chamamos a PSFGenSolSMD                                                                  #
#// ****************************************************************************************//#
sol = BuildSolutionSMD()
if options.hmr != True:  #! Então é False, como se fora off. 
    hmrbool = 0
    sol.build(psf=options.psf, pdb=options.pdb, salt=options.salt, ofile=options.ofile, hmr=hmrbool, atomsvec1=options.atomsvec1, 
              atomsvec2=options.atomsvec2, extrapadz=options.extraspace)
    uxm = UnixMessage()
    listdirs = ["01build", "02mineq", "03prod"]
    uxm.makedir(dirs=listdirs)
    os.chdir("01build")
    os.system("cp ../*psf .")
    os.system("cp ../*pdb .")
    os.system("mv ../PSFGenSolSMD.tcl .")
    dirt = os.path.abspath(".")
    UnixMessage().message(message=f"Working inside: {dirt}", type="info")
    os.system("vmd -dispdev text -e PSFGenSolSMD.tcl 2>&1 | tee psfgenSMD.log")
    time.sleep(3)
    os.system("clear")
    UnixMessage().message(message=f"The system is ready to use.", type="info")
    UnixMessage().message(message=f"Check out the psfgen.log to get more details.", type="info")
    UnixMessage().message(message=f"Review the log carefully to make sure your system has no errors.", type="warning")
    time.sleep(3)

else:
    hmrbool = 1
    sol.build(psf=options.psf, pdb=options.pdb, salt=options.salt, ofile=options.ofile, hmr=hmrbool, atomsvec1=options.atomsvec1, 
              atomsvec2=options.atomsvec2, extrapadz=options.extraspace)
    uxm = UnixMessage()
    listdirs = ["01build", "02mineq", "03prod"]
    uxm.makedir(dirs=listdirs)
    os.chdir("01build")
    os.system("cp ../*psf .")
    os.system("cp ../*pdb .")
    os.system("mv ../PSFGenSolSMD.tcl .")
    dirt = os.path.abspath(".")
    UnixMessage().message(message=f"Working inside: {dirt}", type="info")
    os.system("vmd -dispdev text -e PSFGenSolSMD.tcl 2>&1 | tee psfgenSMD.log")
    time.sleep(3)
    os.system("clear")
    UnixMessage().message(message=f"The system is ready to use.", type="info")
    UnixMessage().message(message=f"Check out the psfgen.log to get more details.", type="info")
    UnixMessage().message(message=f"Review the log carefully to make sure your system has no errors.", type="warning")
    time.sleep(3)
