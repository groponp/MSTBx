import click
import os
from mstbx.core.MDProtocols.MDSolProtocol import MDProtocolSol, SMDProtocolSol
from mstbx.core.Utils.Utils import UnixMessage

@click.command(help="Generates configuration files for Steered Molecular Dynamics (SMD).")
@click.option('--engine', type=click.Choice(['namd', 'amber', 'gromacs', 'openmm']), default='namd', help="Simulation engine to use.")
@click.option('--env', type=click.Choice(['solution']), default='solution', help="System environment.")
@click.option('--psf', type=click.Path(exists=True, dir_okay=False), required=True, help="Input PSF file.")
@click.option('--pdb', type=click.Path(exists=True, dir_okay=False), required=True, help="Input PDB file.")
@click.option('--temperature', default=310.0, help="Temperature in Kelvin.")
@click.option('--mdtime', '--md-time', default=100.0, help="Production time in ns.")
@click.option('--dcdfreq', default=10.0, help="DCD trajectory saving frequency in ps.")
@click.option('--selpull', required=True, help="VMD selection for the pulling group.")
@click.option('--selanchor', required=True, help="VMD selection for the anchor group.")
@click.option('--target-center', type=float, required=True, help="Maximum pulling distance.")
@click.option('--kforce', default=1.5, help="Force constant for pulling.")
def smd_inputs(engine, env, psf, pdb, temperature, mdtime, dcdfreq, selpull, selanchor, target_center, kforce):
    uxm = UnixMessage()
    
    if engine != 'namd':
        uxm.message(f"Engine '{engine}' is not yet implemented for SMD.", "error")
        return

    uxm.message(f"Generating SMD configuration for {engine}...", "info")
    
    md = MDProtocolSol(psf=psf, pdb=pdb, temperature=temperature, mdtime=mdtime, dcdfreq=dcdfreq)
    smd = SMDProtocolSol(psf=psf, pdb=pdb, temperature=temperature, selpull=selpull, selanchor=selanchor,
                         targetCenter=target_center, kforce=kforce, mdtime=mdtime, dcdfreq=dcdfreq)
    
    uxm.makedir(dirs=["01build", "02nvt", "03npt", "04md"])
    os.system("rm -rf 02mineq 03prod")
    md.copytoppar()
    md.nvt()
    md.npt()
    md.restraint()
    smd.smd()
    smd.colvars()
    smd.makecolvarspdb()
    smd.runner_script()
    
    uxm.message("SMD configuration generated successfully.", "info")
