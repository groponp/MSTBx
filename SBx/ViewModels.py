#!/usr/bin/env python3
# ViewModels.py
"""
Loads multiple PDB files from a directory, colors each according to the
discrete 4-color AlphaFold pLDDT confidence scheme (consistent for ChimeraX and PyMOL), 
and visualizes them using either ChimeraX or PyMOL.
Only the first loaded model is shown initially; others are hidden for interactive display.
PyMOL visualization includes specific styling and activates the sequence viewer.
A color key/legend for pLDDT is displayed in ChimeraX.

Written by: Ropon-Palacios G., assisted by Gemini 2.5Pro.
"""

import os
import sys
import argparse
import subprocess
import tempfile
import shutil
import glob
from typing import List, Optional
import re
import logging

# --- Configuración del Logger ---
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(SCRIPT_NAME)

class LoggerConfigurator:
    @staticmethod
    def setup(script_name_for_log_file: str):
        logger.setLevel(logging.DEBUG)
        log_filename = f"{script_name_for_log_file}.log"
        log_file_msg_path = f"'{log_filename}' (log file potentially not writable)"

        try:
            fh = logging.FileHandler(log_filename, mode='w')
            fh.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
            fh.setFormatter(file_formatter)
            if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
                logger.addHandler(fh)
            log_file_msg_path = os.path.abspath(log_filename)
        except Exception as e:
            sys.stderr.write(f"WARNING: Could not configure logging to file '{log_filename}'. Error: {e}\n")
            if not logger.handlers:
                ch_fallback = logging.StreamHandler(sys.stdout)
                ch_fallback.setLevel(logging.INFO)
                console_formatter_fallback = logging.Formatter('[%(levelname)-8s] %(message)s')
                ch_fallback.setFormatter(console_formatter_fallback)
                logger.addHandler(ch_fallback)

        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(logging.INFO)
            console_formatter = logging.Formatter('[%(levelname)-8s] %(message)s')
            ch.setFormatter(console_formatter)
            logger.addHandler(ch)
        
        logger.info(f"Logging configured. Detailed logs may be saved to {log_file_msg_path}.")

# Colores pLDDT (EBI/AlphaFold Server scheme)
ALPHAFOLD_COLORS_RGB_NORMALIZED = {
    "vhigh": [16/255, 109/255, 255/255], # Azul #106dff (>90)
    "conf":  [16/255, 207/255, 241/255], # Cian #10cff1 (70-90)
    "low":   [246/255, 237/255, 18/255],  # Amarillo #f6ed12 (50-70)
    "vlow":  [239/255, 130/255, 30/255]   # Naranja #ef821e (<=50)
}
PYMOL_COLOR_NAMES_MAP = {
    "vhigh": "color_af_blue",
    "conf":  "color_af_cyan",
    "low":   "color_af_yellow",
    "vlow":  "color_af_orange"
}
# Paleta para ChimeraX con los 4 colores discretos y puntos de corte, como confirmaste que funciona.
CHIMERAX_DISCRETE_PLDDT_PALETTE_DEFINITION = \
    "0,#ef821e:49.999,#ef821e:50.000,#f6ed12:69.999,#f6ed12:70.000,#10cff1:89.999,#10cff1:90.000,#106dff:100,#106dff"

def find_executable(name_or_path: str) -> Optional[str]:
    if os.path.sep in name_or_path: 
        if os.path.isfile(name_or_path) and os.access(name_or_path, os.X_OK):
            return os.path.abspath(name_or_path)
        else: return None
    else: return shutil.which(name_or_path)

def generate_pymol_object_name(pdb_filename: str) -> str:
    base_name = os.path.splitext(os.path.basename(pdb_filename))[0]
    rank_match = re.search(r"rank_(\d+)", base_name, re.IGNORECASE)
    if rank_match:
        object_name = f"AFRank{rank_match.group(1).zfill(3)}"
    else:
        sanitized_name = re.sub(r'[^\w_]', '_', base_name)
        if sanitized_name and sanitized_name[0].isdigit(): object_name = "_" + sanitized_name
        elif not sanitized_name: object_name = "model"
        else: object_name = sanitized_name
    return object_name[:60]

def view_with_chimerax_dir(pdb_files: List[str]):
    chimerax_exe = find_executable("chimerax")
    if not chimerax_exe:
        logger.error("ChimeraX executable not found in PATH. Ensure it is installed and accessible.")
        sys.exit(1)

    script_commands = ["lighting soft"] # Esto no esta funcionando. pero no es importante.
    
    # Cargar todos los modelos primero
    for i, pdb_filepath in enumerate(pdb_files):
        pdb_filepath_abs = os.path.abspath(pdb_filepath)
        model_id_chx = i + 1 
        script_commands.append(f'echo "Loading model #{model_id_chx}: {os.path.basename(pdb_filepath_abs)}"')
        script_commands.append(f'open "{pdb_filepath_abs}"')
        script_commands.append(f'show #{model_id_chx} cartoon') 

    # Aplicar el coloreado pLDDT y la clave de color UNA VEZ a todos los modelos cargados.
    logger.info("Applying pLDDT coloring to all loaded models in ChimeraX using custom discrete palette...")
    # Este es el comando que confirmaste que funciona para colorear globalmente con la paleta.
    script_commands.append(f'color bfactor palette {CHIMERAX_DISCRETE_PLDDT_PALETTE_DEFINITION}')

    # Ahora, manejar la visibilidad: ocultar todos excepto el primero.
    for i, pdb_filepath in enumerate(pdb_files): 
        model_id_chx = i + 1
        if i == 0: 
            logger.info(f"Model #{model_id_chx} ({os.path.basename(pdb_files[i])}) will remain shown in ChimeraX.")
        else: 
            script_commands.append(f'hide #{model_id_chx} models') # Usar 'models' como indicaste que funciona
            logger.info(f"Model #{model_id_chx} ({os.path.basename(pdb_files[i])}) will be initially hidden in ChimeraX.")

    script_commands.extend(['view orient', 
                            'echo "All models loaded and colored. Model #1 is initially shown. Use Model Panel (Ctrl-8 or Tools->General->Model Panel) to show/hide."'])
    script_content = "\n".join(script_commands)
    logger.debug(f"ChimeraX script content:\n------BEGIN CXC SCRIPT------\n{script_content}\n-------END CXC SCRIPT-------")
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cxc', delete=False, encoding='utf-8') as tmp:
            tmp.write(script_content); tmp_script_path = tmp.name
        logger.info(f"ChimeraX script: {tmp_script_path}")
        logger.info(f"Launching ChimeraX with {len(pdb_files)} PDBs...")
        subprocess.Popen([chimerax_exe, tmp_script_path])
        logger.info(f"ChimeraX should open shortly. Temp script: {tmp_script_path}")
    except Exception as e: logger.error(f"Error with ChimeraX: {e}")

def view_with_pymol_dir(pdb_files: List[str], pymol_executable_path: str):
    # La parte de PyMOL se mantiene como estaba en la versión anterior que funcionaba bien,
    # incluyendo los rangos con < X.001 y > X para evitar problemas con >= y <=.
    script_commands = [
        #"set cartoon_fancy_helices, 1",   # Apague para que se paresca a chimera, ademas se veia feo.
        #"set cartoon_smooth_loops, 1",
        #"set ray_trace_mode, 0", 
        #"set ray_opaque_background, on", 
        #"set antialias, 2",
        #"set ambient, 0.6", 
        #"set direct, 0.0", 
        #"set specular, off",
        "unset depth_cue", 
        "set orthoscopic, on"
    ]
    for color_key_internal, rgb_list in ALPHAFOLD_COLORS_RGB_NORMALIZED.items():
        pymol_defined_color_name = PYMOL_COLOR_NAMES_MAP[color_key_internal]
        script_commands.append(f"set_color {pymol_defined_color_name}, [{rgb_list[0]:.3f},{rgb_list[1]:.3f},{rgb_list[2]:.3f}]")

    for i, pdb_filepath in enumerate(pdb_files):
        obj_name = generate_pymol_object_name(pdb_filepath)
        script_commands.append(f'print("Loading: {os.path.basename(pdb_filepath)} as {obj_name}")')
        script_commands.append(f'load "{os.path.abspath(pdb_filepath)}", {obj_name}')
        script_commands.append(f'show cartoon, {obj_name}'); script_commands.append(f'hide lines, {obj_name}')
        script_commands.append(f'util.cbaas("{obj_name}")')
        
        # Coloreado pLDDT discreto para PyMOL consistente con la paleta de ChimeraX
        # (usando < X.001 y > X para definir los límites de los rangos)
        script_commands.extend([
            f"color {PYMOL_COLOR_NAMES_MAP['vlow']}, {obj_name} and b < 50.001",      # Naranja: pLDDT <= 50
            f"color {PYMOL_COLOR_NAMES_MAP['low']}, {obj_name} and b > 50 and b < 70.001",    # Amarillo: 50 < pLDDT <= 70
            f"color {PYMOL_COLOR_NAMES_MAP['conf']}, {obj_name} and b > 70 and b < 90.001",   # Cian: 70 < pLDDT <= 90
            f"color {PYMOL_COLOR_NAMES_MAP['vhigh']}, {obj_name} and b > 90.000"          # Azul: pLDDT > 90 (usar 90.000 para ser explícito)
        ])
        if i == 0:
            script_commands.append(f'enable {obj_name}')
            logger.info(f"Object '{obj_name}' ({os.path.basename(pdb_filepath)}) will be shown in PyMOL.")
        else:
            script_commands.append(f'disable {obj_name}')
            logger.info(f"Object '{obj_name}' ({os.path.basename(pdb_filepath)}) loaded but initially hidden.")
    
    script_commands.extend(['set seq_view, on', 'orient', 'zoom visible, 1.2', 
                           'print("All models loaded. Seq viewer on. Colored by pLDDT (EBI/AF scheme). Use object panel to toggle.")'])
    
    # Se eliminó la leyenda de PyMOL en versiones anteriores a petición tuya.
    # Si se desea, se podría re-añadir aquí.

    script_content = "\n".join(script_commands)
    logger.debug(f"PyMOL script content:\n------BEGIN PML SCRIPT------\n{script_content}\n-------END PML SCRIPT-------")
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pml', delete=False, encoding='utf-8') as tmp:
            tmp.write(script_content); tmp_script_path = tmp.name
        logger.info(f"PyMOL script: {tmp_script_path}")
        logger.info(f"Launching PyMOL (using '{pymol_executable_path}') with {len(pdb_files)} PDBs...")
        subprocess.Popen([pymol_executable_path, "-q", tmp_script_path])
        logger.info(f"PyMOL should open shortly. Temp script: {tmp_script_path}")
    except Exception as e: logger.error(f"Error with PyMOL: {e}")

def main():
    LoggerConfigurator.setup(SCRIPT_NAME)
    parser = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="Load multiple PDBs, color by AlphaFold pLDDT (EBI/AF server scheme), and view. First model shown initially.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--pdb-directory", required=True, metavar="PDB_DIR", help="Directory with input PDB files.")
    viewer_group = parser.add_mutually_exclusive_group(required=True)
    viewer_group.add_argument("--chimerax-view", action="store_true", help="View PDBs using ChimeraX.")
    viewer_group.add_argument("--pymol-view", action="store_true", help="View PDBs using PyMOL.")
    parser.add_argument("--pymol-executable", default="pymol", metavar="PYMOL_CMD",
                        help="Custom PyMOL executable (name or path, default: 'pymol'). Used if --pymol-view. Default: use pymol installed.")
    parser.add_argument("--debug", action="store_true", help="Enable debug level logging.")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG); [h.setLevel(logging.DEBUG) for h in logger.handlers]
        logger.debug("Debug logging enabled.")
    else:
        logger.setLevel(logging.INFO)
        [h.setLevel(logging.INFO) for h in logger.handlers if isinstance(h, logging.StreamHandler)]

    logger.info(f"Starting {SCRIPT_NAME}...")
    pymol_exe_to_use, chimerax_exe_to_use = None, None 
    if args.pymol_view:
        pymol_exe_to_use = find_executable(args.pymol_executable)
        if not pymol_exe_to_use: logger.critical(f"PyMOL executable '{args.pymol_executable}' not found. Exiting."); sys.exit(1)
        logger.info(f"Using PyMOL: {pymol_exe_to_use}")
    elif args.chimerax_view:
         chimerax_exe_to_use = find_executable("chimerax") # find_executable se llama ahora dentro de view_with_chimerax_dir
         if not chimerax_exe_to_use: logger.critical("ChimeraX executable 'chimerax' not found. Exiting."); sys.exit(1)
         logger.info(f"Using ChimeraX (path found: {chimerax_exe_to_use})")


    if not os.path.isdir(args.pdb_directory): logger.error(f"PDB directory not found: {args.pdb_directory}"); sys.exit(1)
    pdb_files = [f for ext in ("*.pdb","*.pdb.gz","*.cif","*.cif.gz") for f in glob.glob(os.path.join(args.pdb_directory, ext))]
    if not pdb_files: logger.error(f"No PDB/mmCIF files found in: {args.pdb_directory}"); sys.exit(1)
    pdb_files.sort()
    logger.info(f"Found {len(pdb_files)} PDB/mmCIF file(s): {', '.join(map(os.path.basename, pdb_files))}")

    if args.chimerax_view: view_with_chimerax_dir(pdb_files)
    elif args.pymol_view and pymol_exe_to_use: view_with_pymol_dir(pdb_files, pymol_exe_to_use)
    
    logger.info(f"{SCRIPT_NAME} finished. Viewer launched if successful.")

if __name__ == "__main__":
    main()
