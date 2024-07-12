# -*- coding: utf-8 -*-

#//*****************************************************************************************//# 
# GenMDSolProtocol: Este módulo escreve o protcolo estandar para realizar simulações de       #
#                moléculas, em solução, tais como: Proteínas ou proteina e ligando            #
#                                                                                             #
# autor     : Ropón-Palacios G., BSc - MSc estudante em Física Biomolecular.                  #
# afiliação : Departamento de Física, IBILCE/UNESP, São Jośe do Rio Preto, São Paulo.         #                                                  
# e-mail    : georcki.ropon@unesp.br                                                          #
# data      : Terça-feira 2 de Julho do 2024.                                               #
# $rev$     : Rev Terça-feira 2 de Julho de 2024                                              #                    
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
from LIB.MDProtocols.MDSolProtocol import MDProtocolSol
from LIB.Utils import UnixMessage 

#// ****************************************************************************************//#
# Configurando a informação das opções                                                        #
#// ****************************************************************************************//#
disclaimer="GenMDSolConfg Module from MSTBx"
parser = optparse.OptionParser(description=disclaimer) 

inputs_group = optparse.OptionGroup(parser, "Input Options")
inputs_group.add_option("--psf", help="PSF file of your system", type=str)
inputs_group.add_option("--pdb", help="PDB file of your system", type=str)
inputs_group.add_option("--lparm", help="File in str or prm format of the ligand. Optional.", action="store", 
                        dest="ligandparm", default=None)
parser.add_option_group(inputs_group)

outputs_group = optparse.OptionGroup(parser, "Output Options")
outputs_group.add_option("--temperature", help="Select temperature to perform the simulation in Kelvin units. Default 310 K.", 
                        type=float, default=310, dest="temperature")
outputs_group.add_option("--mdtime", help="Select the time in nanoseconds to perform the md production. Default 100 ns.", 
                        type=float, default=100, dest="mdtime")
parser.add_option_group(outputs_group)
options, args = parser.parse_args() 


#// ****************************************************************************************//#
# Cá chamamos a MDProtocolSol                                                                 #
#// ****************************************************************************************//#
md = MDProtocolSol(psf=options.psf, pdb=options.pdb, temperature=options.temperature, mdtime=options.mdtime)
listdirs = ["01build", "02nvt", "03npt", "04md"]
uxm = UnixMessage()
UnixMessage().message(message=f"Writing the configuration files to running molecular dynamics.", type="info")
uxm.makedir(dirs=listdirs)
os.system("rm -rf 02mineq")
os.system("rm -rf 03prod")
md.copytoppar()
md.nvt()
md.npt()
md.md()
md.restraint()
time.sleep(3)
os.system("clear")
ligand = options.ligandparm

if ligand:
    UnixMessage().message(message=f"Your ligand parmaters is %s." % (options.ligandparm), type="warning")
    os.system("cp -rv %s toppar/" % (options.ligandparm))

#if options.hmr != True:  #! Então é False, como se fora off. 
#hmrbool = 0

UnixMessage().message(message=f"Check out all files generates before running your simulation. .", type="warning")
UnixMessage().message(message=f"Good luck with your simulation!.", type="info")


#else:
#    hmrbool = 1
#    sol.build(psf=options.psf, pdb=options.pdb, salt=options.salt, ofile=options.ofile, hmr=hmrbool)
#    uxm = UnixMessage()
#    listdirs = ["01build", "02mineq", "03prod"]
#    uxm.makedir(dirs=listdirs)
#    os.chdir("01build")
#    os.system("cp ../*psf .")
#    os.system("cp ../*pdb .")
#    os.system("mv ../PSFGenSol.tcl .")
#    dirt = os.path.abspath(".")
#    UnixMessage().message(message=f"Working inside: {dirt}", type="info")
#    os.system("vmd -dispdev text -e PSFGenSol.tcl 2>&1 | tee psfgen.log")
#    time.sleep(3)
#    os.system("clear")
#    UnixMessage().message(message=f"The system is ready to use.", type="info")
#    UnixMessage().message(message=f"Check out the psfgen.log to get more details.", type="info")
#    UnixMessage().message(message=f"Review the log carefully to make sure your system has no errors.", type="warning")
#    time.sleep(3)
