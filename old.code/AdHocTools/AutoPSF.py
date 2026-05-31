#!/usr/bin/env python3
import argparse
import subprocess
import os
import sys
import shutil
from Bio.PDB import PDBParser, PDBIO, Select
from Bio.PDB.Polypeptide import is_aa

# Mapeo de residuos protonados de PDB2PQR a CHARMM
PROTONATION_MAP = {
    'ASH': ('ASP', 'ASPP'),
    'GLH': ('GLU', 'GLUP'),
    'LYN': ('LYS', 'LSDE'),
    'ARN': ('ARG', 'ARNE'),
    'HSD': ('HSD', None),
    'HSE': ('HSE', None),
    'HSP': ('HSP', None),
    'TYL': ('TYR', 'TYR_DEPROT')
}

# Mapeo de Iones y Residuos Problematicos PDB -> CHARMM
RESIDUE_MAP = {
    'NA': 'SOD',
    'CL': 'CLA',
    'K': 'POT',
    'MG': 'MG',
    'CA': 'CAL',
    'ZN': 'ZN2',
    'MN': 'MN2',
    'FE': 'FE2',
    'CU': 'CU2',
    'BGLN': 'NAG', # Forzar NAG en el PDB
    'BGNA': 'NAG'
}

# Lista de glicanos soportados (basado en autopsf)
GLYCANS = {'AMAN', 'BMAN', 'AFUC', 'BGLN', 'MAN', 'BMA', 'FUC', 'NAG', 'AGLC', 'BGLC', 'AALT', 'BALT', 'AALL', 'BALL', 'AGAL', 'BGAL', 'AGUL', 'BGUL', 'AIDO', 'BIDO', 'ATAL', 'BTAL', 'AXYL', 'BXYL', 'AFUC', 'BFUC', 'ARHM', 'BRHM'}

def run_pdb2pqr(input_pdb, output_pqr, ph):
    """Ejecuta pdb2pqr con los flags solicitados."""
    pdb_out = output_pqr.replace('.pqr', '.pdb')
    
    cmd = [
        'pdb2pqr',
        input_pdb,
        output_pqr,
        '--ff=CHARMM',
        '--keep-chain',
        '--ffout=CHARMM',
        f'--pdb-output={pdb_out}',
        '--titration-state-method=propka',
        f'--with-ph={ph}'
    ]
    
    print(f"Running PDB2PQR: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error running pdb2pqr: {e.stderr.decode()}")
        print("Continuing... checking if output exists.")
        if not os.path.exists(output_pqr):
            return False, None
    except FileNotFoundError:
        print("pdb2pqr not found. Skipping protonation calculation.")
        return False, None
        
    return True, pdb_out

def parse_protonation_from_pdb(pdb_file):
    """Lee el PDB generado por PDB2PQR para obtener los nombres de residuos (HSD, HSE, etc.)."""
    protonation_states = {}
    if not pdb_file or not os.path.exists(pdb_file):
        return protonation_states
        
    parser = PDBParser(QUIET=True)
    try:
        structure = parser.get_structure('pdb2pqr_out', pdb_file)
    except Exception as e:
        print(f"Warning: Could not parse PDB2PQR output PDB: {e}")
        return protonation_states

    for model in structure:
        for chain in model:
            for residue in chain:
                key = (chain.id, residue.id[1])
                protonation_states[key] = residue.get_resname()
    return protonation_states

def get_segid(chain_id):
    """Genera SegID estilo CHARMM-GUI (PROA, PROB...)."""
    cid = chain_id if chain_id.strip() else 'A'
    return f"PRO{cid}"[:4]

def detect_ssbonds(structure, threshold=3.0):
    """Detecta puentes disulfuro."""
    cysteines = []
    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.get_resname() in ['CYS', 'CYX'] and 'SG' in residue:
                    cysteines.append(residue)
    
    ssbonds = []
    for i, res1 in enumerate(cysteines):
        for res2 in cysteines[i+1:]:
            atom1 = res1['SG']
            atom2 = res2['SG']
            if res1 == res2: continue
            
            dist = atom1 - atom2
            if dist <= threshold:
                ssbonds.append((res1, res2, dist))
    return ssbonds

def detect_glycan_patches(structure, dist_threshold=2.0):
    """Detecta enlaces glicosídicos."""
    patches = []
    glycan_residues = []
    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.get_resname() in GLYCANS:
                    if 'C1' in residue:
                        glycan_residues.append(residue)
    
    for res in glycan_residues:
        c1 = res['C1']
        best_link = None
        min_dist = dist_threshold
        
        for model in structure:
            for chain in model:
                for target_res in chain:
                    if target_res == res: continue
                    
                    candidates = ['O1', 'O2', 'O3', 'O4', 'O6', 'ND2']
                    for atom_name in candidates:
                        if atom_name in target_res:
                            target_atom = target_res[atom_name]
                            dist = c1 - target_atom
                            if dist < min_dist:
                                min_dist = dist
                                best_link = (target_res, atom_name)
        
        if best_link:
            target_res, link_atom_name = best_link
            current_resname = res.get_resname()
            link_resname = target_res.get_resname()
            
            if any(x in current_resname for x in ['AMAN','AFUC','AGLC','AALT','AALL','AGAL','AGUL','AIDO','ATAL','AXYL','ARHM','ADEO','ARIB','AARB','ALYF','AXYF','MAN','FUC']):
                dir1 = "a"
            else:
                dir1 = "b"
            
            patch_name = None
            if link_atom_name == "ND2":
                patch_name = "NGLB" 
            elif link_atom_name.startswith("O"):
                link_num = link_atom_name[1]
                axial_o2 = ['AMAN','BMAN','MAN','BMA','AALT','BALT','ARHM','BRHM','AIDO','BIDO','ATAL','BTAL']
                axial_o3 = ['AALT','BALT','AALL','BALL','AGUL','BGUL','AIDO','BIDO']
                axial_o4 = ['AFUC','BFUC','FUC','AGAL','BGAL','AGUL','BGUL','AIDO','BIDO','ATAL','BTAL']
                
                dir2 = "b"
                if link_num == '2' and link_resname in axial_o2: dir2 = "a"
                if link_num == '3' and link_resname in axial_o3: dir2 = "a"
                if link_num == '4' and link_resname in axial_o4: dir2 = "a"
                
                patch_name = f"1{link_num}{dir1}{dir2}"
            
            if patch_name:
                patches.append((target_res, res, patch_name))
                
    return patches

def main():
    parser = argparse.ArgumentParser(description="AutoPSF: Generate PSF/PDB using VMD autopsf plugin.")
    parser.add_argument('--input', '-i', required=True, help='Input PDB file')
    parser.add_argument('--output', '-o', required=True, help='Output prefix')
    parser.add_argument('--ph', type=float, default=7.0, help='pH for protonation calculation (default 7.0)')
    parser.add_argument('--nter', default='NTER', help='N-terminal patch (default NTER)')
    parser.add_argument('--cter', default='CTER', help='C-terminal patch (default CTER)')
    parser.add_argument('--toppar', help='Directory containing topology files (optional)')
    
    args = parser.parse_args()
    
    # 1. Run PDB2PQR
    pqr_file = f"{args.output}_temp.pqr"
    success, pdb2pqr_pdb = run_pdb2pqr(args.input, pqr_file, args.ph)
    
    protonation = {}
    if success and pdb2pqr_pdb:
        print(f"Reading protonation states from {pdb2pqr_pdb}")
        protonation = parse_protonation_from_pdb(pdb2pqr_pdb)
    
    # 2. Process Input PDB
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure('input', args.input)
    
    io = PDBIO()
    patches_to_apply = []
    
    # Combined PDB for loading into VMD
    combined_pdb = f"{args.output}_combined.pdb"
    
    for model in structure:
        for chain in model:
            segid = get_segid(chain.id)
            
            # Create a list of residues to remove to avoid modification during iteration
            residues_to_remove = []
            
            for residue in chain:
                key = (chain.id, residue.id[1])
                resname = residue.get_resname().strip()
                
                # REMOVE GLYCANS (User Request)
                if resname in GLYCANS:
                    print(f"Removing Glycan {resname} {chain.id}:{residue.id[1]}")
                    residues_to_remove.append(residue.id)
                    continue

                # Renaming (Ions)
                if resname in RESIDUE_MAP:
                    new_name = RESIDUE_MAP[resname]
                    if resname != new_name:
                        print(f"Renaming {resname} {chain.id}:{residue.id[1]} to {new_name}")
                        residue.resname = new_name
                        resname = new_name
                
                # Protonation Renaming
                if key in protonation:
                    pqr_name = protonation[key]
                    if pqr_name in ['HSD', 'HSE', 'HSP']:
                        if resname != pqr_name:
                            print(f"Renaming HIS {chain.id}:{residue.id[1]} to {pqr_name}")
                            residue.resname = pqr_name
                    elif pqr_name in PROTONATION_MAP:
                        new_name, patch = PROTONATION_MAP[pqr_name]
                        if resname != new_name:
                            residue.resname = new_name
                        if patch:
                            patch_cmd = f"{patch} {chain.id}:{residue.id[1]}"
                            if patch_cmd not in patches_to_apply:
                                print(f"Applying patch {patch} to {new_name} {chain.id}:{residue.id[1]}")
                                patches_to_apply.append(patch_cmd)
            
            # Remove marked residues
            for res_id in residues_to_remove:
                chain.detach_child(res_id)

            # Update SegID in structure (BioPython)
            for atom in chain.get_atoms():
                atom.segid = segid

    # Save modified structure
    io.set_structure(structure)
    io.save(combined_pdb)

    # 3. Detect Patches (SSBOND only)
    ssbonds = detect_ssbonds(structure)
    for res1, res2, dist in ssbonds:
        c1 = res1.get_parent().id
        c2 = res2.get_parent().id
        r1 = res1.id[1]
        r2 = res2.id[1]
        
        # Format: DISU CHAIN1 RESID1 CHAIN2 RESID2
        patch_cmd = f"DISU {c1} {r1} {c2} {r2}"
        if patch_cmd not in patches_to_apply:
            print(f"Detected SSBOND between {c1}:{r1} and {c2}:{r2} ({dist:.2f} A)")
            patches_to_apply.append(patch_cmd)

    # GLYCANS DISABLED
    # glycan_patches = detect_glycan_patches(structure)
    # for target_res, source_res, patch_name in glycan_patches:
    #     ...

    # 4. Generate VMD Script using autopsf CLI
    tcl_script = f"{args.output}_autopsf.tcl"
    with open(tcl_script, 'w') as f:
        f.write("package require autopsf\n")
        
        # Explicitly load topologies
        f.write("::autopsf::init_topologies\n")
        f.write("foreach t $::autopsf::topfiles { topology $t }\n")
        
        # OVERRIDE ALIASES
        f.write("pdbalias residue NAG NAG\n")
        f.write("pdbalias residue BGLN NAG\n")
        
        # REDEFINE autopsf TERMINAL PROCS
        # This forces autopsf to use our requested patches
        nter_val = args.nter.upper()
        cter_val = args.cter.upper()
        
        f.write(f"""
proc ::autopsf::get_nter {{segid resname thischaintype}} {{
    set prot [expr {{$thischaintype == 0}}]
    set nuc  [expr {{$thischaintype == 1 || $thischaintype == 2}}]

    if {{$prot}} {{
        # User requested NTER
        return "{nter_val}"
    }} elseif {{$nuc}} {{
        return "5TER"
    }} else {{
        return "none"
    }}
}}

proc ::autopsf::get_cter {{segid thischaintype}} {{
    set prot [expr {{$thischaintype == 0}}]
    set nuc  [expr {{$thischaintype == 1 || $thischaintype == 2}}]

    if {{$prot}} {{
        # User requested CTER
        return "{cter_val}"
    }} elseif {{$nuc}} {{
        return "3TER"
    }} else {{
        return "none"
    }}
}}
""")
        
        # Load the combined PDB
        f.write(f"mol new {combined_pdb}\n")
        
        # Build autopsf command
        cmd_parts = []
        cmd_parts.append(f"autopsf -mol top")
        cmd_parts.append(f"-prefix {args.output}")
        # Note: We do NOT use -noterm here, because we want autopsf to apply terminals,
        # but we want it to use OUR values (via the redefined procs).
        
        # Add patches
        for p in patches_to_apply:
            cmd_parts.append(f"-patch \"{p}\"")
            
        # Execute autopsf
        f.write(f"{' '.join(cmd_parts)}\n")
        
        f.write("exit\n")

    print(f"Generated VMD script: {tcl_script}")
    
    # 6. Run VMD
    print("Running VMD...")
    try:
        subprocess.run(['vmd', '-dispdev', 'text', '-e', tcl_script], check=True)
        print(f"Successfully generated {args.output}.psf and {args.output}.pdb")
    except subprocess.CalledProcessError:
        print("Error running VMD.")

if __name__ == '__main__':
    main()
