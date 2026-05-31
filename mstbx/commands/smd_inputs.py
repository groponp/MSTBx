import click
import os
from mstbx.core.MDProtocols.MDSolProtocol import MDProtocolSol, SMDProtocolSol
from mstbx.core.Utils.Utils import UnixMessage

@click.command(help="Genera archivos de configuración para Steered Molecular Dynamics (SMD).")
@click.option('--engine', type=click.Choice(['namd', 'amber', 'gromacs', 'openmm']), default='namd', help="Motor de simulación a utilizar.")
@click.option('--env', type=click.Choice(['solution']), default='solution', help="Entorno del sistema.")
@click.option('--psf', type=click.Path(exists=True, dir_okay=False), required=True, help="Archivo PSF del sistema.")
@click.option('--pdb', type=click.Path(exists=True, dir_okay=False), required=True, help="Archivo PDB del sistema.")
@click.option('--temperature', default=310.0, help="Temperatura en Kelvin.")
@click.option('--mdtime', '--md-time', default=100.0, help="Tiempo de producción en ns.")
@click.option('--dcdfreq', default=10.0, help="Frecuencia de guardado en ps.")
@click.option('--selpull', required=True, help="Selección VMD para el grupo que se estira.")
@click.option('--selanchor', required=True, help="Selección VMD para el grupo de anclaje.")
@click.option('--target-center', type=float, required=True, help="Distancia máxima de estiramiento.")
@click.option('--kforce', default=1.5, help="Constante de fuerza para el tirón.")
def smd_inputs(engine, env, psf, pdb, temperature, mdtime, dcdfreq, selpull, selanchor, target_center, kforce):
    uxm = UnixMessage()
    
    if engine != 'namd':
        uxm.message(f"El motor '{engine}' aún no está implementado para SMD.", "error")
        return

    uxm.message(f"Generando configuración SMD para {engine}...", "info")
    
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
    
    uxm.message("Configuración SMD generada con éxito.", "info")
