import click
import os
import time
from mstbx.core.Build.PSFGenSol import BuildSolution, BuildSolutionSMD
from mstbx.core.Build.PSFGenMemb import BuildMembrane
from mstbx.core.Utils.Utils import UnixMessage

@click.group(help="Generación de sistemas (PSF/PDB) para diferentes entornos.")
def topopsfgen():
    """Módulo para construir sistemas solvatados, de membrana o preparados para SMD."""
    pass

# Helper para opciones comunes
def common_options(f):
    options = [
        click.option('--psf', type=click.Path(exists=True, dir_okay=False), required=True, help="Archivo PSF de entrada."),
        click.option('--pdb', type=click.Path(exists=True, dir_okay=False), required=True, help="Archivo PDB de entrada."),
        click.option('--salt', default=0.150, help="Concentración de NaCl (mol/L). Default 0.150."),
        click.option('--ofile', default="macromol150mM", help="Prefijo para los archivos de salida."),
        click.option('--hmr', is_flag=True, help="Habilitar Hydrogen Mass Repartition (para pasos de 4fs)."),
        click.option('--padding', default=18.0, help="Padding global (A). Default 18.0."),
        click.option('--pad-x-pos', type=float, help="Padding específico para eje X+."),
        click.option('--pad-x-neg', type=float, help="Padding específico para eje X-."),
        click.option('--pad-y-pos', type=float, help="Padding específico para eje Y+."),
        click.option('--pad-y-neg', type=float, help="Padding específico para eje Y-."),
        click.option('--pad-z-pos', type=float, help="Padding específico para eje Z+."),
        click.option('--pad-z-neg', type=float, help="Padding específico para eje Z-."),
    ]
    for option in reversed(options):
        f = option(f)
    return f

@topopsfgen.command(name="sol", help="Construye un sistema de proteína en solución (agua + iones).")
@common_options
def sol(psf, pdb, salt, ofile, hmr, padding, pad_x_pos, pad_x_neg, pad_y_pos, pad_y_neg, pad_z_pos, pad_z_neg):
    hmrbool = 1 if hmr else 0
    uxm = UnixMessage()
    builder = BuildSolution()
    builder.build(psf=psf, pdb=pdb, salt=salt, ofile=ofile, hmr=hmrbool, padding=padding,
                  pad_x_pos=pad_x_pos, pad_x_neg=pad_x_neg, pad_y_pos=pad_y_pos, 
                  pad_y_neg=pad_y_neg, pad_z_pos=pad_z_pos, pad_z_neg=pad_z_neg)
    
    uxm.makedir(dirs=["01build"])
    os.chdir("01build")
    os.system("cp ../*psf .")
    os.system("cp ../*pdb .")
    os.system("mv ../PSFGenSol.tcl .")
    os.system("vmd -dispdev text -e PSFGenSol.tcl 2>&1 | tee psfgen.log")
    time.sleep(3)
    uxm.message("Sistema en solución listo en 01build/", "info")

@topopsfgen.command(name="memb", help="Inserta y solvata una proteína en una bicapa lipídica.")
@common_options
@click.option('--mol-outside', is_flag=True, help="Colocar la proteína/péptido fuera de la membrana.")
@click.option('--z-dist', default=10.0, help="Distancia en Z (A) desde la superficie de la membrana.")
def memb(psf, pdb, salt, ofile, hmr, padding, pad_x_pos, pad_x_neg, pad_y_pos, pad_y_neg, pad_z_pos, pad_z_neg, mol_outside, z_dist):
    hmrbool = 1 if hmr else 0
    uxm = UnixMessage()
    builder = BuildMembrane()
    peptide = 1 if mol_outside else 0
    
    builder.build(psf=psf, pdb=pdb, salt=salt, ofile=ofile, hmr=hmrbool, peptide=peptide, 
                  moveZ=z_dist, padding=padding)
    
    uxm.makedir(dirs=["01build"])
    os.chdir("01build")
    # Soporte para prefijo step4 de Membrane Builder
    if os.path.exists("../step4_lipid.psf"):
        os.system("cp ../step4_*psf .")
        os.system("cp ../step4_*pdb .")
    else:
        os.system("cp ../*psf .")
        os.system("cp ../*pdb .")
        
    os.system("mv ../PSFGenMemb.tcl .")
    os.system("vmd -dispdev text -e PSFGenMemb.tcl 2>&1 | tee psfgen.log")
    time.sleep(3)
    uxm.message("Sistema de membrana listo en 01build/", "info")

@topopsfgen.command(name="smd", help="Orienta y construye un sistema para Steered Molecular Dynamics.")
@common_options
@click.option('--atoms-anchor', required=True, help="Selección VMD para el grupo fijo (anclaje).")
@click.option('--atoms-pull', required=True, help="Selección VMD para el grupo que se estira.")
@click.option('--extra-space', default=50.0, help="Espacio extra (A) en Z+ para el estiramiento.")
def smd(psf, pdb, salt, ofile, hmr, padding, pad_x_pos, pad_x_neg, pad_y_pos, pad_y_neg, pad_z_pos, pad_z_neg, atoms_anchor, atoms_pull, extra_space):
    hmrbool = 1 if hmr else 0
    uxm = UnixMessage()
    builder = BuildSolutionSMD()
    
    builder.build(psf=psf, pdb=pdb, salt=salt, ofile=ofile, hmr=hmrbool, atomsvec1=atoms_anchor, 
                  atomsvec2=atoms_pull, extrapadz=extra_space, padding=padding)
    
    uxm.makedir(dirs=["01build"])
    os.chdir("01build")
    os.system("cp ../*psf .")
    os.system("cp ../*pdb .")
    os.system("mv ../PSFGenSolSMD.tcl .")
    os.system("vmd -dispdev text -e PSFGenSolSMD.tcl 2>&1 | tee psfgenSMD.log")
    time.sleep(3)
    uxm.message("Sistema SMD listo en 01build/", "info")
