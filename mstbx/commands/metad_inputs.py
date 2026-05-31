import click
import os
from mstbx.core.MDProtocols.MDSolProtocol import MDProtocolSol, WTMetaDProtocolSol
from mstbx.core.Utils.Utils import UnixMessage

@click.command(help="Genera archivos de configuración para Well-Tempered Metadynamics.")
@click.option('--engine', type=click.Choice(['namd', 'amber', 'gromacs', 'openmm']), default='namd', help="Motor de simulación a utilizar.")
@click.option('--type', type=click.Choice(['sol']), default='sol', help="Tipo de sistema.")
@click.option('--psf', type=click.Path(exists=True), required=True, help="Archivo PSF del sistema.")
@click.option('--pdb', type=click.Path(exists=True), required=True, help="Archivo PDB del sistema.")
@click.option('--temperature', default=310.0, help="Temperatura en Kelvin.")
@click.option('--mdtime', default=100.0, help="Tiempo de producción en ns.")
@click.option('--dcdfreq', default=10.0, help="Frecuencia de guardado en ps.")
# Metadynamics specific
@click.option('--sel1', required=True, help="Selección VMD para la primera molécula.")
@click.option('--sel2', required=True, help="Selección VMD para la segunda molécula.")
@click.option('--target-distance', default=50.0, help="Distancia máxima para la metadinámica.")
@click.option('--hill', default=0.01, help="Peso de la colina (kcal/mol).")
@click.option('--hillfreq', default=500, help="Frecuencia de depósito de colinas (pasos).")
@click.option('--width', default=1.0, help="Ancho de la colina (desviación estándar).")
@click.option('--biasT', 'biast', default=15.0, help="Temperatura de bias (K).")
def metad_inputs(engine, type, psf, pdb, temperature, mdtime, dcdfreq, sel1, sel2, target_distance, hill, hillfreq, width, biast):
    uxm = UnixMessage()
    
    if engine != 'namd':
        uxm.message(f"El motor '{engine}' aún no está implementado para Metadinámica.", "error")
        return

    uxm.message(f"Generando configuración Metadinámica para {engine}...", "info")
    
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
    
    uxm.message("Configuración Metadinámica generada con éxito.", "info")
