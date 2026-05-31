import click
import os
import time
from mstbx.core.MDProtocols.MDSolProtocol import MDProtocolSol
from mstbx.core.MDProtocols.MDMembProtocol import MDProtocolMemb
from mstbx.core.Utils.Utils import UnixMessage

@click.command(help="Generates configuration files for standard Molecular Dynamics.")
@click.option('--engine', type=click.Choice(['namd', 'amber', 'gromacs', 'openmm']), default='namd', help="Simulation engine to use.")
@click.option('--env', type=click.Choice(['solution', 'membrane']), required=True, help="System environment.")
@click.option('--psf', type=click.Path(exists=True, dir_okay=False), required=True, help="Input PSF file.")
@click.option('--pdb', type=click.Path(exists=True, dir_okay=False), required=True, help="Input PDB file.")
@click.option('--temperature', default=310.0, help="Temperature in Kelvin. Default 310.")
@click.option('--mdtime', '--md-time', default=100.0, help="Production time in ns. Default 100.")
@click.option('--dcdfreq', default=10.0, help="DCD trajectory saving frequency in ps. Default 10.0.")
@click.option('--lparm', '--ligand-parm', type=click.Path(exists=True), help="Ligand parameter file (must be CHARMM .str or .prm format).")
def md_inputs(engine, env, psf, pdb, temperature, mdtime, dcdfreq, lparm):
    uxm = UnixMessage()
    
    if engine != 'namd':
        uxm.message(f"Engine '{engine}' is not yet implemented for this module.", "error")
        return

    uxm.message(f"Generating {env} configuration for {engine}...", "info")

    if env == 'solution':
        md = MDProtocolSol(psf=psf, pdb=pdb, temperature=temperature, mdtime=mdtime, dcdfreq=dcdfreq)
        uxm.makedir(dirs=["01build", "02nvt", "03npt", "04md"])
        os.system("rm -rf 02mineq 03prod")
        md.copytoppar()
        md.nvt()
        md.npt()
        md.md()
        md.restraint()

    elif env == 'membrane':
        md = MDProtocolMemb(psf=psf, pdb=pdb, temperature=temperature, mdtime=mdtime, dcdfreq=dcdfreq)
        uxm.makedir(dirs=["01build", "02nvt", "03npt1", "04npt2", "05md"])
        os.system("rm -rf 02mineq 03prod")
        md.copytoppar()
        md.nvt()
        md.npt1()
        md.npt2()
        md.md()
        md.restraint()

    if lparm:
        os.system(f"cp -rv {lparm} toppar/")

    uxm.message("Configuration generated successfully.", "info")
