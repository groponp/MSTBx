import click
import os
from mstbx.core.Build.PDBWriter import PDBWriter
from mstbx.core.Utils.Utils import UnixMessage

from mstbx.core.Utils.Validator import FormatValidator

@click.command(help="Advanced PDB preparation (Fix, Protonate, Edit, SSBOND) and CRD generation.")
@click.option('--input', '-i', type=click.Path(exists=True, dir_okay=False), help="Input PDB/MMCIF file.")
@click.option('--pdb', type=click.Path(exists=True, dir_okay=False), help="Input PDB file (alias for --input).")
@click.option('--psf', type=click.Path(exists=True, dir_okay=False), help="Input PSF file (optional, used for CRD).")
@click.option('--output', '-o', type=click.Path(dir_okay=False), help="Output file base or PDB.")
@click.option('--fix', is_flag=True, help="Run PDBFixer to repair missing atoms/residues.")
@click.option('--internal-only', is_flag=True, default=True, help="If fixing, only repair internal gaps, not terminals.")
@click.option('--ph', type=float, help="pH for protonation using pdb2pqr.")
@click.option('--ff-out', type=click.Choice(['CHARMM', 'AMBER']), default='CHARMM', help="Force field nomenclature for output.")
@click.option('--ssbond', is_flag=True, help="Detect disulfide bonds and add SSBOND lines.")
@click.option('--rename-chain', multiple=True, help="Rename chain: 'old:new' (e.g., 'A:B').")
@click.option('--renumber', type=int, help="Renumber residues starting from this value.")
@click.option('--segid', help="Add/Modify segid for all atoms.")
@click.option('--write-ext-crd', is_flag=True, help="Generate an extended CHARMM-GUI style .crd file.")
@click.option('--check-mol-format', is_flag=True, help="Validate the input format (PDB, PSF, CRD, MOL2) and exit.")
def pdbwriter(input, pdb, psf, output, fix, internal_only, ph, ff_out, ssbond, rename_chain, renumber, segid, write_ext_crd, check_mol_format):
    """PDBWriter: Advanced PDB preparation module."""
    uxm = UnixMessage()
    
    input_file = input or pdb
    if not input_file:
        uxm.message(message="Error: --input or --pdb must be provided.", type="error")
        raise click.Abort()

    if check_mol_format:
        uxm.message(message=f"Validating format for {input_file}...", type="info")
        valid, report = FormatValidator.validate(input_file)
        if valid:
            uxm.message(message=f"SUCCESS: {report}", type="info")
        else:
            uxm.message(message=f"FAILURE: {report}", type="error")
        return

    if not output:
        uxm.message(message="Error: --output must be provided.", type="error")
        raise click.Abort()

    uxm.message(message=f"Starting PDBWriter for {input_file}", type="info")
    
    writer = PDBWriter(input_file, psf_file=psf)
    
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
    
    if write_ext_crd:
        crd_output = output if output.endswith('.crd') else output.rsplit('.', 1)[0] + '.crd'
        uxm.message(message="Generating extended CRD...", type="info")
        writer.write_ext_crd(crd_output)
    
    if not output.endswith('.crd') or not write_ext_crd:
        pdb_output = output if output.endswith('.pdb') else output.rsplit('.', 1)[0] + '.pdb'
        writer.write_final_pdb(pdb_output)
    
    uxm.message(message=f"Successfully processed inputs.", type="info")
    uxm.message(message="Check 'pdbwriter_report.log' for details.", type="warning")
