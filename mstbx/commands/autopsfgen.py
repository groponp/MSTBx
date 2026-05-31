import click
import os
import time
from mstbx.core.Build.PSFGenSol import BuildSolution, BuildSolutionSMD
from mstbx.core.Build.PSFGenMemb import BuildMembrane
from mstbx.core.Utils.Utils import UnixMessage

@click.command()
@click.option('--type', type=click.Choice(['sol', 'memb', 'smd-sol']), required=True, help="Type of system to build.")
@click.option('--psf', type=click.Path(exists=True), required=True, help="PSF file of your system.")
@click.option('--pdb', type=click.Path(exists=True), required=True, help="PDB file of your system.")
@click.option('--salt', default=0.150, help="Salt concentration in mol/L. Default 0.150.")
@click.option('--ofile', default="macromol150mM", help="Prefix of the output file.")
@click.option('--hmr', is_flag=True, help="Enable Hydrogen Mass Repartition.")
# Padding Options
@click.option('--padding', default=18.0, help="Global padding in Angstroms. Default 18.0.")
@click.option('--pad-x-pos', type=float, help="Padding for X+ axis.")
@click.option('--pad-x-neg', type=float, help="Padding for X- axis.")
@click.option('--pad-y-pos', type=float, help="Padding for Y+ axis.")
@click.option('--pad-y-neg', type=float, help="Padding for Y- axis.")
@click.option('--pad-z-pos', type=float, help="Padding for Z+ axis.")
@click.option('--pad-z-neg', type=float, help="Padding for Z- axis.")
# Membrane specific
@click.option('--mol-outside-memb', is_flag=True, help="Enable to place molecule outside from membrane (only for 'memb').")
@click.option('--move-in-z', default=10.0, help="Distance in Angstrom to move molecule in Z (only with --mol-outside-memb).")
# SMD specific
@click.option('--atoms-anchor', help="VMD syntax for anchor group (only for 'smd-sol').")
@click.option('--atoms-pull', help="VMD syntax for pull group (only for 'smd-sol').")
@click.option('--extra-space', default=50.0, help="Extra space in Z+ axis for SMD (only for 'smd-sol').")
def autopsfgen(type, psf, pdb, salt, ofile, hmr, padding, pad_x_pos, pad_x_neg, pad_y_pos, pad_y_neg, pad_z_pos, pad_z_neg, mol_outside_memb, move_in_z, atoms_anchor, atoms_pull, extra_space):
    """Generate PSF/PDB systems with granular padding control and accurate PBC reporting."""
    hmrbool = 1 if hmr else 0
    uxm = UnixMessage()
    
    if type == 'sol':
        sol = BuildSolution()
        sol.build(psf=psf, pdb=pdb, salt=salt, ofile=ofile, hmr=hmrbool, padding=padding,
                  pad_x_pos=pad_x_pos, pad_x_neg=pad_x_neg, pad_y_pos=pad_y_pos, 
                  pad_y_neg=pad_y_neg, pad_z_pos=pad_z_pos, pad_z_neg=pad_z_neg)
        listdirs = ["01build"]
        uxm.makedir(dirs=listdirs)
        os.chdir("01build")
        os.system("cp ../*psf .")
        os.system("cp ../*pdb .")
        os.system("mv ../PSFGenSol.tcl .")
        os.system("vmd -dispdev text -e PSFGenSol.tcl 2>&1 | tee psfgen.log")

    elif type == 'memb':
        mem = BuildMembrane()
        peptide = 1 if mol_outside_memb else 0
        mem.build(psf=psf, pdb=pdb, salt=salt, ofile=ofile, hmr=hmrbool, peptide=peptide, 
                  moveZ=move_in_z, padding=padding)
        listdirs = ["01build"]
        uxm.makedir(dirs=listdirs)
        os.chdir("01build")
        if os.path.exists("../step4_lipid.psf"):
            os.system("cp ../step4_*psf .")
            os.system("cp ../step4_*pdb .")
        else:
            os.system("cp ../*psf .")
            os.system("cp ../*pdb .")
        os.system("mv ../PSFGenMemb.tcl .")
        os.system("vmd -dispdev text -e PSFGenMemb.tcl 2>&1 | tee psfgen.log")

    elif type == 'smd-sol':
        sol = BuildSolutionSMD()
        sol.build(psf=psf, pdb=pdb, salt=salt, ofile=ofile, hmr=hmrbool, atomsvec1=atoms_anchor, 
                  atomsvec2=atoms_pull, extrapadz=extra_space, padding=padding)
        listdirs = ["01build"]
        uxm.makedir(dirs=listdirs)
        os.chdir("01build")
        os.system("cp ../*psf .")
        os.system("cp ../*pdb .")
        os.system("mv ../PSFGenSolSMD.tcl .")
        os.system("vmd -dispdev text -e PSFGenSolSMD.tcl 2>&1 | tee psfgenSMD.log")

    time.sleep(3)
    uxm.message(message=f"System ready. PBC info written to 01build/step3_pbcsetup.str", type="info")
