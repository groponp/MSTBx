import click
import os
import time
from mstbx.core.MDProtocols.MDSolProtocol import MDProtocolSol, SMDProtocolSol, WTMetaDProtocolSol
from mstbx.core.MDProtocols.MDMembProtocol import MDProtocolMemb
from mstbx.core.Utils.Utils import UnixMessage

@click.command()
@click.option('--type', type=click.Choice(['sol', 'memb', 'smd-sol', 'metad-sol']), required=True, help="Type of protocol.")
@click.option('--psf', required=True, help="PSF file of your system.")
@click.option('--pdb', required=True, help="PDB file of your system.")
@click.option('--temperature', default=310.0, help="Temperature in Kelvin. Default 310.")
@click.option('--mdtime', default=100.0, help="MD production time in ns. Default 100.")
@click.option('--lparm', help="Ligand parameter file (str or prm). Optional.")
# SMD Options
@click.option('--selpull', help="VMD syntax for pulling group (only for 'smd-sol').")
@click.option('--selanchor', help="VMD syntax for anchor group (only for 'smd-sol').")
@click.option('--target-center', type=float, help="Max distance for pulling (only for 'smd-sol').")
@click.option('--kforce', default=1.5, help="Force constant for pulling (only for 'smd-sol'). Default 1.5.")
# Metadynamics Options
@click.option('--sel1', help="VMD syntax for first molecule selection (only for 'metad-sol').")
@click.option('--sel2', help="VMD syntax for second molecule selection (only for 'metad-sol').")
@click.option('--target-distance', default=50.0, help="Max distance for metadynamics (only for 'metad-sol'). Default 50.")
@click.option('--hill', default=0.01, help="Hill value for metadynamics bias. Default 0.01.")
@click.option('--hillfreq', default=500, help="Hill frequency for metadynamics bias. Default 500.")
@click.option('--width', default=1.0, help="Width for metadynamics bias. Default 1.0.")
@click.option('--biasT', default=15.0, help="Bias temperature for metadynamics bias. Default 15.")
def namdinputs(type, psf, pdb, temperature, mdtime, lparm, selpull, selanchor, target_center, kforce, sel1, sel2, target_distance, hill, hillfreq, width, biasT):
    """Generate NAMD configuration files for various protocols."""
    uxm = UnixMessage()
    uxm.message(message=f"Writing the configuration files for NAMD {type} simulation.", type="info")

    if type == 'sol':
        md = MDProtocolSol(psf=psf, pdb=pdb, temperature=temperature, mdtime=mdtime)
        listdirs = ["01build", "02nvt", "03npt", "04md"]
        uxm.makedir(dirs=listdirs)
        os.system("rm -rf 02mineq 03prod")
        md.copytoppar()
        md.nvt()
        md.npt()
        md.md()
        md.restraint()

    elif type == 'memb':
        md = MDProtocolMemb(psf=psf, pdb=pdb, temperature=temperature, mdtime=mdtime)
        listdirs = ["01build", "02nvt", "03npt1", "04npt2", "05md"]
        uxm.makedir(dirs=listdirs)
        os.system("rm -rf 02mineq 03prod")
        md.copytoppar()
        md.nvt()
        md.npt1()
        md.npt2()
        md.md()
        md.restraint()

    elif type == 'smd-sol':
        md = MDProtocolSol(psf=psf, pdb=pdb, temperature=temperature, mdtime=mdtime)
        smd = SMDProtocolSol(psf=psf, pdb=pdb, temperature=temperature, selpull=selpull, selanchor=selanchor,
                             targetCenter=target_center, kforce=kforce, mdtime=mdtime)
        listdirs = ["01build", "02nvt", "03npt", "04md"]
        uxm.makedir(dirs=listdirs)
        os.system("rm -rf 02mineq 03prod")
        md.copytoppar()
        md.nvt()
        md.npt()
        md.restraint()
        smd.smd()
        smd.colvars()
        smd.makecolvarspdb()

    elif type == 'metad-sol':
        md = MDProtocolSol(psf=psf, pdb=pdb, temperature=temperature, mdtime=mdtime)
        meta = WTMetaDProtocolSol(psf=psf, pdb=pdb, temperature=temperature, mdtime=mdtime, hill=hill, hillfreq=hillfreq,
                                  width=width, biasT=biasT, sel1=sel1, sel2=sel2, dunbind=target_distance)
        listdirs = ["01build", "02nvt", "03npt", "04md"]
        uxm.makedir(dirs=listdirs)
        os.system("rm -rf 02mineq 03prod")
        md.copytoppar()
        md.nvt()
        md.npt()
        md.restraint()
        meta.wtmetad()
        meta.colvars()
        meta.makecolvarspdb()

    if lparm:
        uxm.message(message=f"Your ligand parameters: {lparm}", type="info")
        os.system(f"cp -rv {lparm} toppar/")

    time.sleep(3)
    os.system("clear")
    uxm.message(message="Check out all generated files before running your simulation.", type="warning")
    uxm.message(message="Good luck with your simulation!", type="info")
