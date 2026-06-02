import click
import os
import subprocess
import re
from mstbx.core.Utils.Utils import UnixMessage

def get_psf_natoms(psf_path):
    """Extrae el número de átomos de un archivo PSF."""
    try:
        with open(psf_path, 'r') as f:
            for line in f:
                if "!NATOM" in line:
                    return int(line.split()[0])
    except Exception:
        return None
    return None

@click.command(help="Resetea un archivo PSF/PDB al formato X-PLOR, útil para sistemas con glicosilaciones o parches virtuales.")
@click.option('--psf', type=click.Path(exists=True, dir_okay=False), required=True, help="Archivo PSF original (formato CHARMM).")
@click.option('--pdb', type=click.Path(exists=True, dir_okay=False), required=True, help="Archivo PDB original.")
@click.option('--output', '-o', default="reset", help="Prefijo para los archivos de salida (reset.psf, reset.pdb).")
def resetpsf(psf, pdb, output):
    uxm = UnixMessage()
    uxm.message(f"Reseteando PSF/PDB de {psf} a formato X-PLOR...", "info")
    
    # Obtener átomos iniciales
    initial_atoms = get_psf_natoms(psf)
    if initial_atoms is None:
        uxm.message(f"No se pudo determinar el número de átomos en {psf}.", "warning")

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
    tcl_file = "resetpsf_run.tcl"
    with open(tcl_file, "w") as f:
        f.write(tcl_script)
    
    try:
        # Ejecutar VMD en modo texto
        result = subprocess.run(["vmd", "-dispdev", "text", "-e", tcl_file], capture_output=True, text=True, check=True)
        
        if os.path.exists(tcl_file):
            os.remove(tcl_file)

        # Verificar átomos finales
        final_psf = f"{output}.psf"
        final_atoms = get_psf_natoms(final_psf)
        
        if final_atoms is not None and initial_atoms is not None:
            if final_atoms == initial_atoms:
                uxm.message(f"Verificación exitosa: {final_atoms} átomos detectados (coincide con el original).", "info")
                uxm.message(f"Archivos {output}.psf y {output}.pdb generados con éxito en formato X-PLOR.", "info")
            else:
                uxm.message(f"Error de consistencia: {initial_atoms} átomos iniciales vs {final_atoms} átomos finales.", "error")
        else:
            uxm.message(f"Archivos {output}.psf y {output}.pdb generados, pero no se pudo verificar el número de átomos.", "warning")

    except subprocess.CalledProcessError as e:
        uxm.message(f"Error al ejecutar VMD: {e}", "error")
        if e.stdout:
            with open("resetpsf_vmd.log", "w") as f:
                f.write(e.stdout)
            uxm.message("Revisa 'resetpsf_vmd.log' para detalles del error.", "warning")
        if os.path.exists(tcl_file):
            uxm.message(f"Puedes revisar '{tcl_file}' para debug.", "warning")
