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
# $rev$     : PASSS - all OK  Quarta-feira 12 de Junho de 2024.                               #                    
#//*****************************************************************************************//#

#// ****************************************************************************************//#
# Log mudanças no código:                                                                     #
#  1. Adicionando uma classe para preparar los sistemas - Quarta feira 12 de Junho 2024.      #
#  2. Atualmente só suporta fosfolipídeos, mas não acho que com colesterol tenha erro.        #
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
from LIB.Build.PSFGenMemb import BuildMembrane
from LIB.Utils import UnixMessage 

#// ****************************************************************************************//#
# Configurando a informação das opções                                                        #
#// ****************************************************************************************//#
disclaimer="GenMemb Module from MSTBx"
parser = optparse.OptionParser(description=disclaimer) 

inputs_group = optparse.OptionGroup(parser, "Input Options")
inputs_group.add_option("--psf", help="PSF file of your system", type=str)
inputs_group.add_option("--pdb", help="PDB file of your system", type=str)
inputs_group.add_option("--salt", help="Select salt concentration of your system in mol/L unit. Defautl 0.150 mol/L.", 
                        type=float, default=0.150, dest="salt")
parser.add_option_group(inputs_group)

outsidememb_group = optparse.OptionGroup(parser, "Inputs for molecule outside of the membrane")
outsidememb_group.add_option("--mol_outside_memb", help="Enable to place any molecule outside from membrane. Optional.", 
                  action="store_true", dest="outsidememb")
outsidememb_group.add_option("--move_in_z", help=r"Enable to place any molecule outside from membrane. Optional. Default is 10 Angstrom.", 
                  default=10, dest="moveZ")
parser.add_option_group(outsidememb_group)

outputs_group = optparse.OptionGroup(parser, "Output Options")
outputs_group.add_option("--hmr", help="Enable Hydrogen mass repartition option. Optional.", 
                         action="store_true")
outputs_group.add_option("--ofile", help="Prefix of the output file. Example: macromol150mM. Default macromol150mM.", 
                        type=str, default="macromol150mM", dest="ofile")

parser.add_option_group(outputs_group)
options, args = parser.parse_args() 

#// ****************************************************************************************//#
# Condicionais para asegurar o uso correto de alguns opções                                   #
#// ****************************************************************************************//#
if options.outsidememb and not options.moveZ:
    UnixMessage().message(message="Option '--move_in_z' is obligatory if use '--mol_outside_memb'", type="error")
    exit()

#// ****************************************************************************************//#
# Cá chamamos a PSFGenMemb                                                                    #
#// ****************************************************************************************//#
mem = BuildMembrane()
if options.hmr != True:  #! Então é False, como se fora off. 
    hmrbool = 0
    if options.outsidememb: #!"on" Este permite colocar o peptídeo/proteína etc fora da membrana.
        peptide = 1 
        mem.build(psf=options.psf, pdb=options.pdb, salt=options.salt, ofile=options.ofile, hmr=hmrbool, peptide=peptide, 
                  moveZ=options.moveZ)
        uxm = UnixMessage()
        listdirs = ["01build", "02mineq", "03prod"]
        uxm.makedir(dirs=listdirs)
        os.chdir("01build")
        os.system("cp ../*psf .")
        os.system("cp ../*pdb .")
        os.system("mv ../PSFGenMemb.tcl .")
        dirt = os.path.abspath(".")
        UnixMessage().message(message=f"Working inside: {dirt}", type="info")
        os.system("vmd -dispdev text -e PSFGenMemb.tcl 2>&1 | tee psfgen.log")
        time.sleep(3)
        os.system("clear")
        UnixMessage().message(message=f"The system is ready to use.", type="info")
        UnixMessage().message(message=f"Check out the psfgen.log to get more details.", type="info")
        UnixMessage().message(message=f"Review the log carefully to make sure your system has no errors.", type="warning")
        time.sleep(3)
    else:
        peptide = 0 
        mem.build(psf=options.psf, pdb=options.pdb, salt=options.salt, ofile=options.ofile, hmr=hmrbool, peptide=peptide, 
                  moveZ=options.moveZ)
        uxm = UnixMessage()
        listdirs = ["01build", "02mineq", "03prod"]
        uxm.makedir(dirs=listdirs)
        os.chdir("01build")
        os.system("cp ../*psf .")
        os.system("cp ../*pdb .")
        os.system("mv ../PSFgenMemb.tcl .")
        dirt = os.path.abspath(".")
        UnixMessage().message(message=f"Working inside: {dirt}", type="info")
        os.system("vmd -dispdev text -e PSFGenMemb.tcl 2>&1 | tee psfgen.log")
        time.sleep(3)
        os.system("clear")
        UnixMessage().message(message=f"The system is ready to use.", type="info")
        UnixMessage().message(message=f"Check out the psfgen.log to get more details.", type="info")
        UnixMessage().message(message=f"Review the log carefully to make sure your system has no errors.", type="warning")
        time.sleep(3)

else:
    hmrbool = 1
    if options.outsidememb:
        peptide = 1 
        mem.build(psf=options.psf, pdb=options.pdb, salt=options.salt, ofile=options.ofile, hmr=hmrbool, peptide=peptide, 
                  moveZ=options.moveZ)
        uxm = UnixMessage()
        listdirs = ["01build", "02mineq", "03prod"]
        uxm.makedir(dirs=listdirs)
        os.chdir("01build")
        os.system("cp ../*psf .")
        os.system("cp ../*pdb .")
        os.system("mv ../PSFGenMemb.tcl .")
        dirt = os.path.abspath(".")
        UnixMessage().message(message=f"Working inside: {dirt}", type="info")
        os.system("vmd -dispdev text -e PSFGenMemb.tcl 2>&1 | tee psfgen.log")
        time.sleep(3)
        os.system("clear")
        UnixMessage().message(message=f"The system is ready to use.", type="info")
        UnixMessage().message(message=f"Check out the psfgen.log to get more details.", type="info")
        UnixMessage().message(message=f"Review the log carefully to make sure your system has no errors.", type="warning")
        time.sleep(3)
        
    else:
        peptide = 0 
        mem.build(psf=options.psf, pdb=options.pdb, salt=options.salt, ofile=options.ofile, hmr=hmrbool, peptide=peptide, 
                  moveZ=options.moveZ)
        uxm = UnixMessage()
        listdirs = ["01build", "02mineq", "03prod"]
        uxm.makedir(dirs=listdirs)
        os.chdir("01build")
        os.system("cp ../step4_*psf .")
        os.system("cp ../step4_*pdb .")
        os.system("mv ../master.tcl .")
        dirt = os.path.abspath(".")
        UnixMessage().message(message=f"Working inside: {dirt}", type="info")
        os.system("vmd -dispdev text -e master.tcl 2>&1 | tee psfgen.log")
        time.sleep(3)
        os.system("clear")
        UnixMessage().message(message=f"The system is ready to use.", type="info")
        UnixMessage().message(message=f"Check out the psfgen.log to get more details.", type="info")
        UnixMessage().message(message=f"Review the log carefully to make sure your system has no errors.", type="warning")
        time.sleep(3)