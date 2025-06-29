"""
Convert NAMD topology and coordinates to GROMACS format.

Este script automatiza la conversión de archivos de NAMD (PSF, COOR, XSC) a archivos compatibles con GROMACS (.pdb, .gro, .top) usando VMD y TopoTools.
- Genera un archivo PDB con CRYST1 usando VMD.
- Genera los archivos .gro y .top usando todos los archivos de parámetros encontrados en una carpeta (--toppar_dir).
- Opcionalmente, genera un archivo index.ndx de GROMACS con grupos personalizados (--tc_groups).
- Todos los archivos de salida se guardan en la carpeta 04md_gmx o 05md_gmx, según corresponda.

Uso por línea de comandos:
    python MDTranslate.py --psf system.psf --coor restart.coor --xsc restart.xsc --outprefix nptlast --toppar_dir toppar/ --tc_groups "{'SOLU': 'protein', 'MEMB': 'segid MEMB', 'SOLV': 'all and not (protein or segid MEMB)'}"

Para ayuda y descripción de argumentos:
    python MDTranslate.py -h

Todos los mensajes en pantalla estarán en inglés. Los comentarios internos están en español.
"""

import sys
import os
import logging
import shutil
import subprocess
import argparse
from datetime import datetime

def setup_logger():
    logger = logging.getLogger("MDTranslate")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s %(asctime)s] %(message)s', datefmt='%H:%M:%S %d-%m-%Y')
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.handlers = []
    logger.addHandler(sh)
    return logger

def get_gmx_folder():
    if os.path.exists("04md"):
        return "04md_gmx"
    elif os.path.exists("05md"):
        return "05md_gmx"
    else:
        raise RuntimeError("Neither 04md nor 05md folder was found.")

def check_inputs(files, logger):
    for f in files:
        if not os.path.isfile(f):
            logger.error(f"File not found: {f}")
            sys.exit(1)

def check_vmd(logger):
    if shutil.which("vmd") is None:
        logger.error("VMD is not in the system PATH.")
        sys.exit(1)

def psfcoor4pdb(psf, coor, xsc, outpdb, logger, workdir="."):
    import os
    # Convertir todas las rutas a absolutas
    psf = os.path.abspath(psf)
    coor = os.path.abspath(coor)
    xsc = os.path.abspath(xsc)
    outpdb = os.path.abspath(outpdb)
    tcl_path = os.path.abspath(os.path.join(workdir, "psfcoor4pdb.tcl"))
    tcl_code = f'''
# TCL generado automáticamente, rutas absolutas embebidas
set psf "{psf}"
set coor "{coor}"
set xsc "{xsc}"
set out "{outpdb}"

mol new $psf type psf
mol addfile $coor type namdbin waitfor all
animate goto end
set all [atomselect top all]
set fh [open $xsc r]
set goodlines {{}}
foreach line [split [read $fh] "\\n"] {{
    if {{[string trim $line] eq ""}} {{ continue }}
    if {{[string match "#*" $line]}} {{ continue }}
    lappend goodlines $line
}}
close $fh
set fields [split [lindex $goodlines end]]
set ax [lindex $fields 1]
set by [lindex $fields 5]
set cz [lindex $fields 9]
set a [expr {{abs($ax)}}]
set b [expr {{abs($by)}}]
set c [expr {{abs($cz)}}]
puts "Final box: a=$a Å  b=$b Å  c=$c Å"
set tmp "_tmp.pdb"
$all writepdb $tmp
set in [open $tmp r]
set pdblines {{}}
foreach line [split [read $in] "\\n"] {{
    if {{[string match "CRYST1*" $line]}} {{ continue }}
    lappend pdblines $line
}}
close $in
file delete $tmp
set outF [open $out w]
set cryst [format "CRYST1%9.3f%9.3f%9.3f%7.2f%7.2f%7.2f P 1           1\\n" $a $b $c 90.0 90.0 90.0]
puts -nonewline $outF "$cryst[join $pdblines "\\n"]\\n"
close $outF
puts "$out written in CRYST1 format as in VMD"
quit
'''
    with open(tcl_path, "w") as f:
        f.write(tcl_code)
    logger.info(f"TCL script generated: {tcl_path}")

    vmd_cmd = [
        "vmd", "-dispdev", "text", "-e", tcl_path
    ]
    logger.info(f"Running VMD to generate the PDB with CRYST1...")
    logger.info(f"Command: {' '.join(vmd_cmd)}")
    try:
        subprocess.run(vmd_cmd, check=True, cwd=workdir)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running VMD: {e}")
        raise
    logger.info(f"{outpdb} written in CRYST1 format as in VMD")

def topogmx(psf, pdb, outprefix, toppar_dir, logger, workdir="."):
    """
    Escribe y ejecuta un script TCL para generar .gro y .top usando topotools,
    con rutas absolutas directamente en el TCL (sin -args).
    """
    import os
    # Convertir rutas a absolutas
    psf = os.path.abspath(psf)
    pdb = os.path.abspath(pdb)
    toppar_dir = os.path.abspath(toppar_dir)
    tcl_path = os.path.abspath(os.path.join(workdir, "topogmx.tcl"))
    tcl_code = f'''
# TCL generado automáticamente, rutas absolutas embebidas
set psf "{psf}"
set pdb "{pdb}"
set outprefix "{outprefix}"
set toppar_dir "{toppar_dir}"

package require topotools 1.8

mol new $psf type psf
mol addfile $pdb type pdb waitfor all
animate goto end
set sel [atomselect top all]

set box [molinfo top get {{a b c}}]
puts "Box detected: $box"

if {{[lindex $box 0] == 0.0 || [lindex $box 1] == 0.0 || [lindex $box 2] == 0.0}} {{
    puts "WARNING: The box seems empty. Are you sure your PDB has CRYST1?"
}}

set param_files [glob -nocomplain -directory $toppar_dir *]
puts "Parameter files found: $param_files"

$sel writegro "${{outprefix}}.gro"
topo writegmxtop "${{outprefix}}.top" $param_files

puts "Generated: ${{outprefix}}.top and ${{outprefix}}.gro"
quit
'''
    with open(tcl_path, "w") as f:
        f.write(tcl_code)
    logger.info(f"TCL script generated: {tcl_path}")

    vmd_cmd = [
        "vmd", "-dispdev", "text", "-e", tcl_path
    ]
    logger.info(f"Running VMD to generate .gro and .top for GROMACS...")
    logger.info(f"Command: {' '.join(vmd_cmd)}")
    try:
        subprocess.run(vmd_cmd, check=True, cwd=workdir)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running VMD: {e}")
        raise
    logger.info(f".gro and .top files generated successfully in {workdir}")

def create_index_ndx(gro_file, out_file, tc_groups_str, logger):
    """
    Creates a GROMACS index.ndx file with custom groups using MDAnalysis.

    Parameters:
        gro_file (str): Path to the input .gro file.
        out_file (str): Path to the output .ndx file.
        tc_groups_str (str): Dict string with group names and selections.
    """
    import MDAnalysis as mda
    from MDAnalysis.selections.gromacs import SelectionWriter
    import ast

    # Load universe
    try:
        u = mda.Universe(gro_file)
    except Exception as e:
        logger.error(f"Could not load .gro file {gro_file}: {e}")
        return

    # Parse group dictionary
    try:
        group_dict = ast.literal_eval(tc_groups_str)
    except Exception as e:
        logger.error("Error interpreting --tc_groups. Use double quotes outside, single quotes inside.")
        return

    # Write .ndx file
    try:
        with SelectionWriter(out_file, mode='w') as ndx:
            for group_name, selection_str in group_dict.items():
                try:
                    sel = u.select_atoms(selection_str)
                    ndx.write(sel, name=group_name)
                except Exception as e:
                    logger.warning(f"Error processing group '{group_name}' with selection '{selection_str}': {e}")
        logger.info(f"File {out_file} created successfully with groups: {', '.join(group_dict.keys())}")
    except Exception as e:
        logger.error(f"Could not write index file {out_file}: {e}")

def create_index_ndx_auto(outdir, outprefix, tc_groups_str, logger):
    """
    Creates a GROMACS index.ndx file with custom groups using MDAnalysis.
    Uses the .gro file generated by topogmx (outprefix.gro) in outdir.

    Example usage:
        python MDTranslate.py --psf system.psf --coor restart.coor --xsc restart.xsc --outprefix nptlast --toppar_dir toppar/ --tc_groups "{'SOLU': 'protein', 'SOLV': 'resname SOL CL'}" --write_mdp --temperature 300 --mdtime 5
    """
    gro_file = os.path.join(outdir, f"{outprefix}.gro")
    out_file = os.path.join(outdir, "index.ndx")
    create_index_ndx(gro_file, out_file, tc_groups_str, logger)

def write_production_mdp(filename, temperature=310, mdtime_ns=1.0, tc_groups_str=None, logger=None):
    """
    Writes a GROMACS production MDP file (pro.mdp) with user-defined temperature, simulation time, and tc_grps.
    - filename: output file name (str)
    - temperature: temperature in Kelvin (float)
    - mdtime_ns: simulation time in nanoseconds (float)
    - tc_groups_str: dict string with group names (str)
    nsteps is calculated for dt=0.002 ps. nstxout-compressed is always 50000 (50 ps).
    """
    import ast

    dt_ps = 0.002  # time step in ps
    total_ps = mdtime_ns * 1000
    nsteps = int(total_ps / dt_ps)
    nstxout_compressed = int(50 / dt_ps)  # 50 ps

    # Default groups if not provided
    if tc_groups_str:
        try:
            group_dict = ast.literal_eval(tc_groups_str)
            tc_grps = " ".join(group_dict.keys())
            n_groups = len(group_dict)
        except Exception as e:
            if logger:
                logger.warning("Could not parse --tc_groups, using default groups: SOLU MEMB SOLV")
            tc_grps = "SOLU MEMB SOLV"
            n_groups = 3
    else:
        tc_grps = "SOLU MEMB SOLV"
        n_groups = 3

    tau_t = "1.0 " * n_groups
    ref_t = (f"{temperature} " * n_groups).strip()

    mdp_content = f"""integrator              = md
dt                      = {dt_ps}
nsteps                  = {nsteps}
nstxout-compressed      = {nstxout_compressed}
nstxout                 = 0
nstvout                 = 0
nstfout                 = 0
nstcalcenergy           = 100
nstenergy               = 1000
nstlog                  = 1000
;
cutoff-scheme           = Verlet
nstlist                 = 20
rlist                   = 1.2
vdwtype                 = Cut-off
vdw-modifier            = Force-switch
rvdw_switch             = 1.0
rvdw                    = 1.2
coulombtype             = PME
rcoulomb                = 1.2
;
tcoupl                  = v-rescale
tc_grps                 = {tc_grps}
tau_t                   = {tau_t.strip()}
ref_t                   = {ref_t}
;
pcoupl                  = C-rescale
pcoupltype              = semiisotropic
tau_p                   = 5.0
compressibility         = 4.5e-5  4.5e-5
ref_p                   = 1.0     1.0
;
constraints             = h-bonds
constraint_algorithm    = LINCS
continuation            = yes
;
nstcomm                 = 100
comm_mode               = linear
comm_grps               = {tc_grps}
"""
    with open(filename, "w") as f:
        f.write(mdp_content)
    if logger:
        logger.info(f"MDP file '{filename}' written with temperature={temperature} K, mdtime={mdtime_ns} ns, tc_grps={tc_grps}.")

def write_gmx_run_script(outdir, outprefix="prod"):
    """
    Escribe un script bash para preparar y correr una simulación de GROMACS.
    Usa prod.mdp, prod.gro, prod.top y (si existe) index.ndx.
    """
    import os
    script_path = os.path.join(outdir, "run_gmx.sh")
    mdp = os.path.join(outdir, f"{outprefix}.mdp")
    gro = os.path.join(outdir, f"{outprefix}.gro")
    top = os.path.join(outdir, f"{outprefix}.top")
    ndx = os.path.join(outdir, "index.ndx")
    tpr = os.path.join(outdir, f"{outprefix}.tpr")

    # Detecta si existe index.ndx
    ndx_line = f"-n index.ndx \\" if os.path.isfile(ndx) else ""

    bash_script = f"""#!/bin/bash
set -e
cd {outdir}

echo "Preparando el archivo .tpr..."
gmx grompp -f {os.path.basename(mdp)} -o {os.path.basename(tpr)} -c {os.path.basename(gro)} -p {os.path.basename(top)} {ndx_line}

echo "Corriendo la simulación de producción..."
gmx mdrun -v -deffnm {outprefix}

echo "Simulación finalizada. Archivos principales:"
ls -lh {outprefix}.tpr {outprefix}.trr {outprefix}.edr {outprefix}.log {outprefix}.cpt
"""

    with open(script_path, "w") as f:
        f.write(bash_script)
    os.chmod(script_path, 0o755)
    print(f"Script para correr GROMACS escrito en: {script_path}")

# --- Agrega los argumentos a main ---
def main():
    logger = setup_logger()
    parser = argparse.ArgumentParser(
        description=(
            "Convert NAMD topology and coordinates to GROMACS format.\n\n"
            "This script automates the conversion of NAMD files (PSF, COOR, XSC) to GROMACS-compatible files (.pdb, .gro, .top) using VMD and TopoTools.\n"
            "- Generates a PDB with CRYST1 using VMD.\n"
            "- Generates .gro and .top files using all parameter files found in a directory (--toppar_dir).\n"
            "- Optionally, generates a GROMACS index.ndx file with custom groups (--tc_groups).\n"
            "- Optionally, writes a production MDP file (--write_mdp) with user-defined temperature and simulation time.\n"
            "- All output files are placed in 04md_gmx or 05md_gmx, as appropriate.\n\n"
            "Example usage:\n"
            "  python MDTranslate.py --psf system.psf --coor restart.coor --xsc restart.xsc --outprefix nptlast --toppar_dir toppar/ --tc_groups \"{'SOLU': 'protein', 'SOLV': 'resname SOL CL'}\" --write_mdp --temperature 300 --mdtime 5\n"
            "\nFor help and argument description:\n"
            "  python MDTranslate.py -h\n"
            "\nAll screen messages are in English. Internal comments are in Spanish."
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--psf", required=True, help="Input PSF file")
    parser.add_argument("--coor", required=True, help="Input NAMD binary coordinates file (.coor)")
    parser.add_argument("--xsc", required=True, help="Input NAMD extended system file (.xsc)")
    parser.add_argument("--outprefix", required=True, help="Output prefix for .pdb, .gro, .top")
    parser.add_argument("--toppar_dir", required=True, help="Directory containing all parameter files (.prm, .str, etc.)")
    parser.add_argument("--tc_groups", required=False, help="Groups for index.ndx as a dict string. Example: \"{'SOLU': 'protein', 'SOLV': 'resname SOL CL'}\"")
    parser.add_argument("--write_mdp", action="store_true", help="Write a production MDP file (pro.mdp) in the output directory")
    parser.add_argument("--temperature", type=float, default=310, help="Temperature in Kelvin for MDP file (default: 310)")
    parser.add_argument("--mdtime", type=float, default=1.0, help="Simulation time in nanoseconds for MDP file (default: 1.0)")
    parser.add_argument("--comm_groups", required=False, help="Groups for comm.ndx as a dict string. Example: \"{'SOLU': 'protein', 'SOLV': 'resname SOL CL'}\"")
    args = parser.parse_args()

    # Check VMD and input files
    check_vmd(logger)
    check_inputs([args.psf, args.coor, args.xsc], logger)
    if not os.path.isdir(args.toppar_dir):
        logger.error(f"Parameter directory not found: {args.toppar_dir}")
        sys.exit(1)

    # Create output directory BEFORE anything else
    outdir = get_gmx_folder()
    os.makedirs(outdir, exist_ok=True)
    logger.info(f"Output directory: {outdir}")

    # Generar PDB
    outpdb_path = os.path.join(outdir, f"{args.outprefix}.pdb")
    psfcoor4pdb(args.psf, args.coor, args.xsc, outpdb_path, logger, workdir=outdir)
    if not os.path.isfile(outpdb_path):
        logger.error(f"PDB file was not generated: {outpdb_path}")
        sys.exit(1)

    # Generar .gro y .top
    topogmx(args.psf, outpdb_path, args.outprefix, args.toppar_dir, logger, workdir=outdir)
    outgro_path = os.path.join(outdir, f"{args.outprefix}.gro")
    outtop_path = os.path.join(outdir, f"{args.outprefix}.top")
    if not os.path.isfile(outgro_path):
        logger.error(f"GRO file was not generated: {outgro_path}")
        sys.exit(1)
    if not os.path.isfile(outtop_path):
        logger.error(f"TOP file was not generated: {outtop_path}")
        sys.exit(1)

    # Opcional: index.ndx
    if args.tc_groups:
        create_index_ndx_auto(outdir, args.outprefix, args.tc_groups, logger)
        outndx_path = os.path.join(outdir, "index.ndx")
        if not os.path.isfile(outndx_path):
            logger.error(f"NDX file was not generated: {outndx_path}")
            sys.exit(1)

    # Opcional: pro.mdp
    if args.write_mdp:
        mdp_path = os.path.join(outdir, "prod.mdp")
        write_production_mdp(
            mdp_path,
            temperature=args.temperature,
            mdtime_ns=args.mdtime,
            tc_groups_str=args.tc_groups,
            logger=logger
        )
        if not os.path.isfile(mdp_path):
            logger.error(f"MDP file was not generated: {mdp_path}")
            sys.exit(1)

    # Opcional: comm.ndx
    if args.comm_groups:
        commndx_path = os.path.join(outdir, "comm.ndx")
        create_index_ndx(
            os.path.join(outdir, f"{args.outprefix}.gro"),
            commndx_path,
            args.comm_groups,
            logger
        )
        if not os.path.isfile(commndx_path):
            logger.error(f"COMM NDX file was not generated: {commndx_path}")
            sys.exit(1)

    logger.info("Process completed successfully.")
    write_gmx_run_script(outdir, args.outprefix)

if __name__ == "__main__":
    main()