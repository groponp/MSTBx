# -*- coding: utf-8 -*-

#//*****************************************************************************************//# 
# PSFGenSol : Este módulo permite criar sistemas em solução.                                  #
#             Ex proteína, peptídeos ou ligantes em agua e íons.                              #
#                                                                                             #
# autor     : Ropón-Palacios G., BSc - MSc estudante em Física Biomolecular.                  #
# afiliação : Departamento de Física, IBILCE/UNESP, São Jośe do Rio Preto, São Paulo.         #                                                  
# e-mail    : georcki.ropon@unesp.br                                                          #
# data      : Quarta-feira 12 de Junho do 2024.                                               #
# $rev$     : $rev$     : PASSS - all OK  Quarta-feira 12 de Junho de 2024.                   #                    
#//*****************************************************************************************//#

#// ****************************************************************************************//#
# Log mudanças no código:                                                                     #
#  1. Adicionando uma classe para preparar los sistemas - Quarta feira 12 de Junho 2024.      #
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
from LIB.Build.PSFGenSol import BuildSolution
from LIB.Utils.Utils import UnixMessage 

#// ****************************************************************************************//#
# Configurando a informação das opções                                                        #
#// ****************************************************************************************//#
disclaimer="GenSol Module from MSTBx"
parser = optparse.OptionParser(description=disclaimer) 

inputs_group = optparse.OptionGroup(parser, "Input Options")
inputs_group.add_option("--psf", help="PSF file of your system", type=str)
inputs_group.add_option("--pdb", help="PDB file of your system", type=str)
inputs_group.add_option("--salt", help="Select salt concentration of your system in mol/L unit. Defautl 0.150 mol/L.", 
                        type=float, default=0.150, dest="salt")
parser.add_option_group(inputs_group)


outputs_group = optparse.OptionGroup(parser, "Output Options")
outputs_group.add_option("--hmr", help="Enable Hydrogen mass repartition option. Optional.", 
                         action="store_true")
outputs_group.add_option("--ofile", help="Prefix of the output file. Example: macromol150mM. Default macromol150mM.", 
                        type=str, default="macromol150mM", dest="ofile")
parser.add_option_group(outputs_group)
options, args = parser.parse_args() 


#// ****************************************************************************************//#
# Cá chamamos a PSFGenSol                                                                     #
#// ****************************************************************************************//#
sol = BuildSolution()
if options.hmr != True:  #! Então é False, como se fora off. 
    hmrbool = 0
    sol.build(psf=options.psf, pdb=options.pdb, salt=options.salt, ofile=options.ofile, hmr=hmrbool)
    uxm = UnixMessage()
    listdirs = ["01build", "02mineq", "03prod"]
    uxm.makedir(dirs=listdirs)
    os.chdir("01build")
    os.system("cp ../*psf .")
    os.system("cp ../*pdb .")
    os.system("mv ../PSFGenSol.tcl .")
    dirt = os.path.abspath(".")
    UnixMessage().message(message=f"Working inside: {dirt}", type="info")
    os.system("vmd -dispdev text -e PSFGenSol.tcl 2>&1 | tee psfgen.log")
    time.sleep(3)
    os.system("clear")
    UnixMessage().message(message=f"The system is ready to use.", type="info")
    UnixMessage().message(message=f"Check out the psfgen.log to get more details.", type="info")
    UnixMessage().message(message=f"Review the log carefully to make sure your system has no errors.", type="warning")
    time.sleep(3)

else:
    hmrbool = 1
    sol.build(psf=options.psf, pdb=options.pdb, salt=options.salt, ofile=options.ofile, hmr=hmrbool)
    uxm = UnixMessage()
    listdirs = ["01build", "02mineq", "03prod"]
    uxm.makedir(dirs=listdirs)
    os.chdir("01build")
    os.system("cp ../*psf .")
    os.system("cp ../*pdb .")
    os.system("mv ../PSFGenSol.tcl .")
    dirt = os.path.abspath(".")
    UnixMessage().message(message=f"Working inside: {dirt}", type="info")
    os.system("vmd -dispdev text -e PSFGenSol.tcl 2>&1 | tee psfgen.log")
    time.sleep(3)
    os.system("clear")
    UnixMessage().message(message=f"The system is ready to use.", type="info")
    UnixMessage().message(message=f"Check out the psfgen.log to get more details.", type="info")
    UnixMessage().message(message=f"Review the log carefully to make sure your system has no errors.", type="warning")
    time.sleep(3)
