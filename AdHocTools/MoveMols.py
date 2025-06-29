import subprocess
import os
import argparse
import logging
from datetime import datetime

def setup_logger(logfile="move_molecule.log"):
    logger = logging.getLogger("move_molecule")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s %(asctime)s] %(message)s', datefmt='%H:%M:%S %d-%m-%Y')
    fh = logging.FileHandler(logfile)
    fh.setFormatter(formatter)
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.handlers = []
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger

def fix_pdb_segname(pdb_file):
    lines = []
    with open(pdb_file, "r") as f:
        for line in f:
            if line.startswith(("ATOM", "HETATM")):
                # Garante que a linha tem pelo menos 80 caracteres
                line = line.rstrip('\n')
                line = line + ' ' * (80 - len(line)) if len(line) < 80 else line

                # Verifica e ajusta o chainID (coluna 22, índice 21)
                chain_id = line[21].strip()
                if not chain_id:
                    chain_id = "A"
                    # Substitui o chainID vazio por "A"
                    line = line[:21] + chain_id + line[22:]

                segname = f"PRO{chain_id}"
                # Insere o segname nas colunas 73-76 (índices 72:76)
                new_line = line[:72] + f"{segname:>4}" + line[76:]
                lines.append(new_line + '\n')
            else:
                lines.append(line)
    with open(pdb_file, "w") as f:
        f.writelines(lines)

def main(input_pdb, output_pdb, logger, distance, mode):
    # ================================
    # TCL script for VMD to move molecule
    # ================================
    vmd_script = f"""
mol new {input_pdb} type pdb waitfor all
set sel_mol [atomselect top "all"]
set com_mol [measure center $sel_mol weight mass]
set x_mol [lindex $com_mol 0]
set y_mol [lindex $com_mol 1]
set z_mol [lindex $com_mol 2]
$sel_mol moveby [list [expr -1.0 * $x_mol] [expr -1.0 * $y_mol] [expr -1.0 * $z_mol]]
"""

    if mode == "relative":
        # Move to distance above phosphorus atoms (assumed at 19 Å)
        vmd_script += f"$sel_mol moveby [list 0.0 0.0 [expr {distance} + 19.0]]\n"
    elif mode == "absolute":
        # Move to absolute Z position
        vmd_script += f"$sel_mol moveby [list 0.0 0.0 {distance}]\n"

    vmd_script += f"animate write pdb {output_pdb} sel $sel_mol\n"
    vmd_script += "exit\n"

    with open("vmd_tmp.tcl", "w") as f:
        f.write(vmd_script)

    logger.info("Running VMD to center and move the molecule...")
    subprocess.run(["vmd", "-dispdev", "text", "-e", "vmd_tmp.tcl"], check=True)

    os.remove("vmd_tmp.tcl")
    logger.info(f"Done! Output file generated: {output_pdb}")

    # Corrige el segname en el PDB
    fix_pdb_segname(output_pdb)
    logger.info(f"Segname ajustado a PROX en {output_pdb}")

if __name__ == "__main__":
    example_text = (
        "\nExample usage:\n"
        "  python MoveMols.py -m input.pdb -o output.pdb -d 29 --mode absolute\n"
        "  python MoveMols.py -m input.pdb -o output.pdb -d 10 --mode relative\n"
    )
    parser = argparse.ArgumentParser(
        description=(
            "This script centers a molecule (protein/peptide/small molecule) from a PDB file and moves it to a specified Z position.\n"
            "Modes: --mode relative (default, places at <distance> Å above phosphorus atoms, assumed at 19 Å), "
            "or --mode absolute (places at Z = <distance> Å)."
            + example_text
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-m", "--molecule", required=True, help="Input PDB file of the molecule")
    parser.add_argument("-o", "--output", default="moved_molecule.pdb", help="Output PDB file")
    parser.add_argument("-l", "--log", default="move_molecule.log", help="Log file name")
    parser.add_argument("-d", "--distance", type=float, default=10.0, help="Distance in Å (meaning depends on --mode)")
    parser.add_argument("--mode", choices=["relative", "absolute"], default="relative",
                        help="Positioning mode: 'relative' (default, above phosphorus atoms) or 'absolute' (Z = distance)")
    args = parser.parse_args()
    logger = setup_logger(args.log)
    main(args.molecule, args.output, logger, args.distance, args.mode)
