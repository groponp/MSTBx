import click
import os
import time
from mstbx.core.Build.PSFGenSol import BuildSolution, BuildSolutionSMD
from mstbx.core.Build.PSFGenMemb import BuildMembrane
from mstbx.core.Utils.Utils import UnixMessage

# Clase personalizada para agrupar opciones en el Help
class GroupedGroup(click.Command):
    def format_options(self, ctx, formatter):
        """Escribe las opciones agrupadas por categorías en el menú de ayuda."""
        opts_common = []
        opts_memb = []
        opts_smd = []
        
        for param in self.get_params(ctx):
            if param.name in ['psf', 'pdb', 'salt', 'ofile', 'hmr', 'padding', 'pad_x_pos', 'pad_x_neg', 'pad_y_pos', 'pad_y_neg', 'pad_z_pos', 'pad_z_neg', 'env']:
                opts_common.append(param.get_help_record(ctx))
            elif param.name in ['mol_outside', 'z_dist']:
                opts_memb.append(param.get_help_record(ctx))
            elif param.name in ['atoms_anchor', 'atoms_pull', 'extra_space']:
                opts_smd.append(param.get_help_record(ctx))

        if opts_common:
            with formatter.section("Opciones Comunes"):
                formatter.write_dl(opts_common)
        if opts_memb:
            with formatter.section("Opciones Específicas de Membrana (--env membrane)"):
                formatter.write_dl(opts_memb)
        if opts_smd:
            with formatter.section("Opciones Específicas de SMD (--env smd)"):
                formatter.write_dl(opts_smd)

@click.command(cls=GroupedGroup, help="Generación de sistemas (PSF/PDB) para diferentes entornos.")
@click.option('--env', type=click.Choice(['solution', 'membrane', 'smd']), required=True, help="Entorno del sistema a construir.")
# Common Options
@click.option('--psf', type=click.Path(exists=True, dir_okay=False), required=True, help="Archivo PSF de entrada.")
@click.option('--pdb', type=click.Path(exists=True, dir_okay=False), required=True, help="Archivo PDB de entrada.")
@click.option('--salt', default=0.150, help="Concentración de NaCl (mol/L). Default 0.150.")
@click.option('--ofile', default="macromol150mM", help="Prefijo para los archivos de salida.")
@click.option('--hmr', is_flag=True, help="Habilitar Hydrogen Mass Repartition.")
@click.option('--padding', default=18.0, help="Padding global (A). Default 18.0.")
@click.option('--pad-x-pos', type=float, help="Padding eje X+.")
@click.option('--pad-x-neg', type=float, help="Padding eje X-.")
@click.option('--pad-y-pos', type=float, help="Padding eje Y+.")
@click.option('--pad-y-neg', type=float, help="Padding eje Y-.")
@click.option('--pad-z-pos', type=float, help="Padding eje Z+.")
@click.option('--pad-z-neg', type=float, help="Padding eje Z-.")
# Membrane Options
@click.option('--mol-outside', is_flag=True, help="Colocar proteína fuera de la membrana.")
@click.option('--z-dist', default=10.0, help="Distancia en Z (A) desde la superficie.")
# SMD Options
@click.option('--atoms-anchor', help="Selección VMD para el grupo fijo.")
@click.option('--atoms-pull', help="Selección VMD para el grupo móvil.")
@click.option('--extra-space', default=50.0, help="Espacio extra en Z+ para SMD.")
def topopsfgen(env, psf, pdb, salt, ofile, hmr, padding, pad_x_pos, pad_x_neg, pad_y_pos, pad_y_neg, pad_z_pos, pad_z_neg, mol_outside, z_dist, atoms_anchor, atoms_pull, extra_space):
    """Módulo para construir sistemas solvatados, de membrana o SMD."""
    hmrbool = 1 if hmr else 0
    uxm = UnixMessage()
    
    if env == 'solution':
        builder = BuildSolution()
        builder.build(psf=psf, pdb=pdb, salt=salt, ofile=ofile, hmr=hmrbool, padding=padding,
                      pad_x_pos=pad_x_pos, pad_x_neg=pad_x_neg, pad_y_pos=pad_y_pos, 
                      pad_y_neg=pad_y_neg, pad_z_pos=pad_z_pos, pad_z_neg=pad_z_neg)
        script_tcl = "PSFGenSol.tcl"

    elif env == 'membrane':
        builder = BuildMembrane()
        peptide = 1 if mol_outside else 0
        builder.build(psf=psf, pdb=pdb, salt=salt, ofile=ofile, hmr=hmrbool, peptide=peptide, 
                      moveZ=z_dist, padding=padding)
        script_tcl = "PSFGenMemb.tcl"

    elif env == 'smd':
        if not atoms_anchor or not atoms_pull:
            uxm.message("Error: --atoms-anchor y --atoms-pull son obligatorios para SMD.", "error")
            return
        builder = BuildSolutionSMD()
        builder.build(psf=psf, pdb=pdb, salt=salt, ofile=ofile, hmr=hmrbool, atomsvec1=atoms_anchor, 
                      atomsvec2=atoms_pull, extrapadz=extra_space, padding=padding)
        script_tcl = "PSFGenSolSMD.tcl"

    # Ejecución Común
    uxm.makedir(dirs=["01build"])
    os.chdir("01build")
    if env == 'membrane' and os.path.exists("../step4_lipid.psf"):
        os.system("cp ../step4_*psf .")
        os.system("cp ../step4_*pdb .")
    else:
        os.system("cp ../*psf .")
        os.system("cp ../*pdb .")
        
    os.system(f"mv ../{script_tcl} .")
    os.system(f"vmd -dispdev text -e {script_tcl} 2>&1 | tee psfgen.log")
    time.sleep(2)
    uxm.message(f"Sistema {env} listo en 01build/", "info")
