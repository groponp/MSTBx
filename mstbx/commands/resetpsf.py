import click
import os
import subprocess
from mstbx.core.Utils.Utils import UnixMessage

@click.command(help="Resetea un archivo PSF/PDB al formato X-PLOR, útil para sistemas con glicosilaciones o parches virtuales.")
@click.option('--psf', type=click.Path(exists=True, dir_okay=False), required=True, help="Archivo PSF original (formato CHARMM).")
@click.option('--pdb', type=click.Path(exists=True, dir_okay=False), required=True, help="Archivo PDB original.")
@click.option('--output', '-o', default="reset", help="Prefijo para los archivos de salida (reset.psf, reset.pdb).")
def resetpsf(psf, pdb, output):
    uxm = UnixMessage()
    uxm.message(f"Reseteando PSF/PDB de {psf} a formato X-PLOR...", "info")
    
    tcl_script = f"""
package require psfgen
resetpsf
readpsf {psf}
coordpdb {pdb}
vpbonds 1
writepsf x-plor {output}.psf
writepdb {output}.pdb
quit
"""
    with open("resetpsf_run.tcl", "w") as f:
        f.write(tcl_script)
    
    try:
        # Ejecutar VMD en modo texto
        subprocess.run(["vmd", "-dispdev", "text", "-e", "resetpsf_run.tcl"], check=True, capture_output=True)
        os.remove("resetpsf_run.tcl")
        uxm.message(f"Archivos {output}.psf y {output}.pdb generados con éxito.", "info")
    except subprocess.CalledProcessError as e:
        uxm.message(f"Error al ejecutar VMD: {e}", "error")
        if os.path.exists("resetpsf_run.tcl"):
            uxm.message("Puedes revisar 'resetpsf_run.tcl' para debug.", "warning")
