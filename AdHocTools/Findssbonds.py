#!/usr/bin/env python3
import argparse
import os
import sys
from datetime import datetime
from Bio.PDB import PDBParser, MMCIFParser, PDBIO

def find_ssbonds(structure, threshold=3.0):
    # Seleccionar átomos de azufre (SG) en residuos de cisteína (CYS)
    # Esto esta basado en el criterio de distancia usado por autopsf.
    cysteines = []
    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.get_resname() == 'CYS' and 'SG' in residue:
                    cysteines.append(residue['SG'])
    
    ssbonds = []
    for i, atom1 in enumerate(cysteines):
        for atom2 in cysteines[i+1:]:
            # Verificar que no sean del mismo residuo
            res1 = atom1.get_parent()
            res2 = atom2.get_parent()
            chain1 = res1.get_parent()
            chain2 = res2.get_parent()
            
            # Comparar identidad de objetos residuo y cadena para asegurar que son distintos
            if res1 == res2 and chain1 == chain2:
                continue
            
            # BioPython permite restar átomos para obtener distancia
            dist = atom1 - atom2
            
            if dist <= threshold:
                ssbonds.append((atom1, atom2, dist))
    return ssbonds

def write_pdb_with_ssbond_lines(pdb_file, ssbonds, output_file):
    with open(pdb_file, 'r') as f:
        lines = f.readlines()

    # Generar header personalizado
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    header_line = f"REMARK 999 Script generated with AdHocTools Findssbonds.py from MSTBx written by Ropón-Palacios G. date: {now}\n"
    
    # Insertar header al principio
    lines.insert(0, header_line)

    # Buscar dónde insertar las líneas SSBOND (antes de la primera línea ATOM/HETATM)
    insert_index = 0
    for i, line in enumerate(lines):
        if line.startswith('ATOM') or line.startswith('HETATM'):
            insert_index = i
            break

    ssbond_lines = []
    for idx, (atom1, atom2, dist) in enumerate(ssbonds, 1):
        res1 = atom1.get_parent()
        res2 = atom2.get_parent()
        chain1 = res1.get_parent().id
        chain2 = res2.get_parent().id
        resnum1 = res1.id[1]
        resnum2 = res2.id[1]
        icode1 = res1.id[2] if res1.id[2] != ' ' else ''
        icode2 = res2.id[2] if res2.id[2] != ' ' else ''
        
        # Formato PDB SSBOND: columnas fijas, 80 caracteres aprox.
        # SSBOND serNum "CYS" chainID1 seqNum1 icode1 "CYS" chainID2 seqNum2 icode2 sym1 sym2 Length
        
        c1 = chain1[:1] if len(chain1) > 0 else ' '
        c2 = chain2[:1] if len(chain2) > 0 else ' '
        
        # Formato corregido para alineación estricta PDB (agregado espacio despues de SSBOND)
        line = ("SSBOND {:3d} CYS {:1s} {:4d}{:1s}   CYS {:1s} {:4d}{:1s}                       "
                "1555   1555 {:5.2f}\n").format(idx, c1, resnum1, icode1, c2, resnum2, icode2, dist)
        ssbond_lines.append(line)

    new_lines = lines[:insert_index] + ssbond_lines + lines[insert_index:]

    with open(output_file, 'w') as f:
        f.writelines(new_lines)

def main():
    parser = argparse.ArgumentParser(description="Detect disulfide bonds (SSBOND) in a PDB/CIF and add SSBOND lines to a PDB output using BioPython.")
    parser.add_argument('--input', '-i', required=True, help='Input file (PDB or CIF)')
    parser.add_argument('--output', '-o', required=True, help='Output PDB file with SSBOND lines')
    parser.add_argument('--cutoff', '-c', type=float, default=3.0, help='Maximum distance (A) to define an SSBOND (default 3.0 A)')

    args = parser.parse_args()

    # Detectar formato y cargar
    ext = os.path.splitext(args.input)[1].lower()
    if ext == '.cif':
        parser_obj = MMCIFParser(QUIET=True)
    elif ext == '.pdb' or ext == '.ent':
        parser_obj = PDBParser(QUIET=True)
    else:
        print(f"Error: Unsupported extension {ext}. Use .pdb or .cif")
        sys.exit(1)

    try:
        structure = parser_obj.get_structure('struct', args.input)
    except Exception as e:
        print(f"Error loading structure: {e}")
        sys.exit(1)

    # Asignar SegID igual al ChainID para compatibilidad con CHARMM
    for atom in structure.get_atoms():
        chain_id = atom.get_parent().get_parent().id
        # Asegurar que SegID no exceda 4 caracteres (limite PDB)
        # Si chain_id es vacio, dejarlo vacio o asignar ' '
        segid = chain_id[:4] if chain_id else ' '
        # Corregido: Asignar atributo directamente
        atom.segid = segid

    ssbonds = find_ssbonds(structure, threshold=args.cutoff)

    print(f"Found {len(ssbonds)} possible disulfide bonds with cutoff {args.cutoff} A")
    for a1, a2, d in ssbonds:
        res1 = a1.get_parent()
        res2 = a2.get_parent()
        c1 = res1.get_parent().id
        c2 = res2.get_parent().id
        print(f"CYS {c1} {res1.id[1]} - CYS {c2} {res2.id[1]} : {d:.2f} A")

    # Guardar estructura base como PDB
    io = PDBIO()
    io.set_structure(structure)
    io.save(args.output)
    
    # Insertar líneas SSBOND y Header
    write_pdb_with_ssbond_lines(args.output, ssbonds, args.output)
    print(f"PDB rewritten to {args.output} with SSBOND lines added.")

if __name__ == '__main__':
    main()
