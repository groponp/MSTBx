import click
import os
import time
from mstbx.core.Build.PSFGenSol import BuildSolution, BuildSolutionSMD
from mstbx.core.Build.PSFGenMemb import BuildMembrane
from mstbx.core.Utils.Utils import UnixMessage

@click.command()
@click.option('--type', type=click.Choice(['sol', 'memb', 'smd-sol']), required=True, help="Type of system to build.")
@click.option('--psf', required=True, help="PSF file of your system.")
@click.option('--pdb', required=True, help="PDB file of your system.")
@click.option('--salt', default=0.150, help="Salt concentration in mol/L. Default 0.150.")
@click.option('--ofile', default="macromol150mM", help="Prefix of the output file.")
@click.option('--hmr', is_flag=True, help="Enable Hydrogen Mass Repartition.")
@click.option('--mol-outside-memb', is_flag=True, help="Enable to place molecule outside from membrane (only for 'memb').")
@click.option('--move-in-z', default=10.0, help="Distance in Angstrom to move molecule in Z (only with --mol-outside-memb).")
@click.option('--atoms-anchor', help="VMD syntax for anchor group (only for 'smd-sol').")
@click.option('--atoms-pull', help="VMD syntax for pull group (only for 'smd-sol').")
@click.option('--extra-space', default=50.0, help="Extra space in Z axis for SMD (only for 'smd-sol').")
def autopsfgen(type, psf, pdb, salt, ofile, hmr, mol_outside_memb, move_in_z, atoms_anchor, atoms_pull, extra_space):
    """Generate PSF/PDB systems for solution, membrane, or SMD."""
    hmrbool = 1 if hmr else 0
    uxm = UnixMessage()
    
    if type == 'sol':
        sol = BuildSolution()
        sol.build(psf=psf, pdb=pdb, salt=salt, ofile=ofile, hmr=hmrbool)
        listdirs = ["01build", "02mineq", "03prod"]
        uxm.makedir(dirs=listdirs)
        os.chdir("01build")
        os.system("cp ../*psf .")
        os.system("cp ../*pdb .")
        os.system("mv ../PSFGenSol.tcl .")
        dirt = os.path.abspath(".")
        uxm.message(message=f"Working inside: {dirt}", type="info")
        os.system("vmd -dispdev text -e PSFGenSol.tcl 2>&1 | tee psfgen.log")

    elif type == 'memb':
        mem = BuildMembrane()
        peptide = 1 if mol_outside_memb else 0
        mem.build(psf=psf, pdb=pdb, salt=salt, ofile=ofile, hmr=hmrbool, peptide=peptide, moveZ=move_in_z)
        listdirs = ["01build", "02mineq", "03prod"]
        uxm.makedir(dirs=listdirs)
        os.chdir("01build")
        if os.path.exists("../step4_lipid.psf"):
            os.system("cp ../step4_*psf .")
            os.system("cp ../step4_*pdb .")
        else:
            os.system("cp ../*psf .")
            os.system("cp ../*pdb .")
        os.system("mv ../PSFGenMemb.tcl .")
        dirt = os.path.abspath(".")
        uxm.message(message=f"Working inside: {dirt}", type="info")
        os.system("vmd -dispdev text -e PSFGenMemb.tcl 2>&1 | tee psfgen.log")

    elif type == 'smd-sol':
        sol = BuildSolutionSMD()
        sol.build(psf=psf, pdb=pdb, salt=salt, ofile=ofile, hmr=hmrbool, atomsvec1=atoms_anchor, 
                  atomsvec2=atoms_pull, extrapadz=extra_space)
        listdirs = ["01build", "02mineq", "03prod"]
        uxm.makedir(dirs=listdirs)
        os.chdir("01build")
        os.system("cp ../*psf .")
        os.system("cp ../*pdb .")
        os.system("mv ../PSFGenSolSMD.tcl .")
        dirt = os.path.abspath(".")
        uxm.message(message=f"Working inside: {dirt}", type="info")
        os.system("vmd -dispdev text -e PSFGenSolSMD.tcl 2>&1 | tee psfgenSMD.log")

    time.sleep(3)
    os.system("clear")
    uxm.message(message=f"The system is ready to use.", type="info")
    uxm.message(message=f"Review the log carefully to make sure your system has no errors.", type="warning")
