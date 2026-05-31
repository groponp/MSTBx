import click
import os
from mstbx.core.Build.PDBWriter import PDBWriter
from mstbx.core.Utils.Utils import UnixMessage

@click.command(help="Advanced PDB preparation (Fix, Protonate, Edit, SSBOND).")
@click.option('--input', '-i', type=click.Path(exists=True, dir_okay=False), required=True, help="Input PDB/MMCIF file.")
@click.option('--output', '-o', type=click.Path(dir_okay=False), required=True, help="Output PDB file.")
@click.option('--fix', is_flag=True, help="Run PDBFixer to repair missing atoms/residues.")
@click.option('--internal-only', is_flag=True, default=True, help="If fixing, only repair internal gaps, not terminals.")
@click.option('--ph', type=float, help="pH for protonation using pdb2pqr.")
@click.option('--ff-out', type=click.Choice(['CHARMM', 'AMBER']), default='CHARMM', help="Force field nomenclature for output.")
@click.option('--ssbond', is_flag=True, help="Detect disulfide bonds and add SSBOND lines.")
@click.option('--rename-chain', multiple=True, help="Rename chain: 'old:new' (e.g., 'A:B').")
@click.option('--renumber', type=int, help="Renumber residues starting from this value.")
@click.option('--segid', help="Add/Modify segid for all atoms.")
def pdbwriter(input, output, fix, internal_only, ph, ff_out, ssbond, rename_chain, renumber, segid):
    """PDBWriter: Advanced PDB preparation module."""
    uxm = UnixMessage()
    uxm.message(message=f"Starting PDBWriter for {input}", type="info")
    
    writer = PDBWriter(input)
    
    if fix:
        uxm.message(message="Running PDBFixer...", type="info")
        writer.fix_structure(fix_only_internal=internal_only)
    
    if ph is not None:
        uxm.message(message=f"Protonating at pH {ph}...", type="info")
        writer.protonate(pH=ph, ff=ff_out)
    
    if ssbond:
        uxm.message(message="Detecting S-S bonds...", type="info")
        writer.find_ssbonds()
    
    chains_dict = {}
    for rc in rename_chain:
        if ':' in rc:
            old, new = rc.split(':')
            chains_dict[old] = new
    
    if chains_dict or renumber is not None or segid:
        uxm.message(message="Applying structural edits...", type="info")
        writer.edit_structure(rename_chains=chains_dict, renumber_residues=renumber, add_segid=segid)
    
    writer.write_final_pdb(output)
    uxm.message(message=f"Successfully generated {output}", type="info")
    uxm.message(message="Check 'pdbwriter_report.log' for details.", type="warning")
