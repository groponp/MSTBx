import click
import os
import time
from mstbx.core.MDProtocols.MDSolProtocol import MDProtocolSol
from mstbx.core.MDProtocols.MDMembProtocol import MDProtocolMemb
from mstbx.core.Utils.Utils import UnixMessage

@click.command(help="Genera archivos de configuración para Dinámica Molecular estándar.")
@click.option('--engine', type=click.Choice(['namd', 'amber', 'gromacs', 'openmm']), default='namd', help="Motor de simulación a utilizar.")
@click.option('--type', type=click.Choice(['sol', 'memb']), required=True, help="Tipo de sistema.")
@click.option('--psf', type=click.Path(exists=True), required=True, help="Archivo PSF del sistema.")
@click.option('--pdb', type=click.Path(exists=True), required=True, help="Archivo PDB del sistema.")
@click.option('--temperature', default=310.0, help="Temperatura en Kelvin. Default 310.")
@click.option('--mdtime', default=100.0, help="Tiempo de producción en ns. Default 100.")
@click.option('--dcdfreq', default=10.0, help="Frecuencia de guardado de trayectoria en ps. Default 10.0.")
@click.option('--lparm', help="Parámetros de ligando (str o prm).")
def md_inputs(engine, type, psf, pdb, temperature, mdtime, dcdfreq, lparm):
    uxm = UnixMessage()
    
    if engine != 'namd':
        uxm.message(f"El motor '{engine}' aún no está implementado para este módulo.", "error")
        return

    uxm.message(f"Generando configuración {type} para {engine}...", "info")

    if type == 'sol':
        md = MDProtocolSol(psf=psf, pdb=pdb, temperature=temperature, mdtime=mdtime, dcdfreq=dcdfreq)
        uxm.makedir(dirs=["01build", "02nvt", "03npt", "04md"])
        os.system("rm -rf 02mineq 03prod")
        md.copytoppar()
        md.nvt()
        md.npt()
        md.md()
        md.restraint()

    elif type == 'memb':
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

    uxm.message("Configuración generada con éxito.", "info")
