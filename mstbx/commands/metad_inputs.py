import click
import os
from mstbx.core.MDProtocols.MDSolProtocol import MDProtocolSol, WTMetaDProtocolSol
from mstbx.core.Utils.Utils import UnixMessage

@click.command(help="Generates configuration files for Well-Tempered Metadynamics.")
@click.option('--engine', type=click.Choice(['namd', 'amber', 'gromacs', 'openmm']), default='namd', help="Simulation engine to use.")
@click.option('--env', type=click.Choice(['solution']), default='solution', help="System environment.")
@click.option('--psf', type=click.Path(exists=True, dir_okay=False), required=True, help="Input PSF file.")
@click.option('--pdb', type=click.Path(exists=True, dir_okay=False), required=True, help="Input PDB file.")
@click.option('--temperature', default=310.0, help="Temperature in Kelvin.")
@click.option('--mdtime', '--md-time', default=100.0, help="Production time in ns.")
@click.option('--dcdfreq', default=10.0, help="DCD trajectory saving frequency in ps.")
# Metadynamics specific
@click.option('--sel1', required=True, help="VMD selection for the first molecule.")
@click.option('--sel2', required=True, help="VMD selection for the second molecule.")
@click.option('--target-distance', default=50.0, help="Maximum distance for metadynamics.")
@click.option('--hill', default=0.01, help="Hill weight (kcal/mol).")
@click.option('--hillfreq', default=500, help="Hill deposition frequency (steps).")
@click.option('--width', default=1.0, help="Hill width (standard deviation).")
@click.option('--biasT', 'biast', default=15.0, help="Bias temperature (K).")
@click.option('--colvar-input', type=click.Path(exists=True, file_okay=False, dir_okay=True), help="Directory containing custom wtmetad.in and dependencies.")
def metad_inputs(engine, env, psf, pdb, temperature, mdtime, dcdfreq, sel1, sel2, target_distance, hill, hillfreq, width, biast, colvar_input):
    uxm = UnixMessage()
    
    if engine != 'namd':
        uxm.message(f"Engine '{engine}' is not yet implemented for Metadynamics.", "error")
        return

    uxm.message(f"Generating Metadynamics configuration for {engine}...", "info")
    
    md = MDProtocolSol(psf=psf, pdb=pdb, temperature=temperature, mdtime=mdtime, dcdfreq=dcdfreq)
    meta = WTMetaDProtocolSol(psf=psf, pdb=pdb, temperature=temperature, mdtime=mdtime, hill=hill, hillfreq=hillfreq,
                              width=width, biasT=biast, sel1=sel1, sel2=sel2, dunbind=target_distance, dcdfreq=dcdfreq)
    
    uxm.makedir(dirs=["01build", "02nvt", "03npt", "04md"])
    os.system("rm -rf 02mineq 03prod")
    md.copytoppar()
    md.nvt()
    md.npt()
    md.restraint()
    meta.wtmetad()
    meta.colvars()
    meta.makecolvarspdb()
    meta.runner_script()
    
    uxm.message("Metadynamics configuration generated successfully.", "info")
