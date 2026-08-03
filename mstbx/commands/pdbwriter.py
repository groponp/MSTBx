import click
import urllib.request
from pathlib import Path
import tempfile
from mstbx.core.Build.CGenFFInputs import CGenFFInputConfig, CGenFFInputPreparer
from mstbx.core.Build.PDBWriter import PDBWriter
from mstbx.core.Utils.Utils import UnixMessage

from mstbx.core.Utils.Validator import FormatValidator


def _write_selected_chains(source, destination, chains):
    """Write a PDB containing only the requested chain records."""
    selected = {chain.strip() for chain in chains.split(",") if chain.strip()}
    output = []
    found = set()
    coordinate_records = {"ATOM", "HETATM"}
    for line in Path(source).read_text().splitlines():
        record = line[:6].strip()
        if record in coordinate_records:
            chain = line[21].strip() if len(line) > 21 else ""
            if chain in selected:
                output.append(line)
                found.add(chain)
        elif record == "TER":
            chain = line[21].strip() if len(line) > 21 else ""
            if chain in selected:
                output.append(line)
        elif record == "SEQRES":
            chain = line[11].strip() if len(line) > 11 else ""
            if chain in selected:
                output.append(line)
        elif record not in {"CONECT", "MASTER", "END"}:
            output.append(line)
    missing = selected - found
    if missing:
        raise click.ClickException(
            f"Requested chain(s) not found in {source}: {', '.join(sorted(missing))}. "
            f"Found: {', '.join(sorted(found)) or 'none'}."
        )
    Path(destination).write_text("\n".join(output) + "\nEND\n")

@click.command(help="Advanced PDB preparation (Fix, Protonate, Edit, SSBOND) and CRD generation.")
@click.option('--input', '-i', type=click.Path(exists=True, dir_okay=False), help="Input PDB/MMCIF file.")
@click.option('--mol', type=click.Path(exists=True, dir_okay=False), help="Input molecule file for validation only (works with --check-mol-format).")
@click.option('--psf', type=click.Path(exists=True, dir_okay=False), help="Input PSF file (optional, used for CRD).")
@click.option('--output', '-o', type=click.Path(), help="Output file base, PDB, CRD, or CGenFF input directory.")
@click.option('--fix-structure', is_flag=True, help="Run PDBFixer to repair missing atoms/residues.")
@click.option('--fix-keep-hetatoms', is_flag=True, help="Keep HETATM records during --fix-structure.")
@click.option('--fix-add-hydrogens', is_flag=True, help="Add hydrogens during --fix-structure using --pH.")
@click.option('--internal-only', is_flag=True, default=True, help="If fixing, only repair internal gaps, not terminals.")
@click.option('--pH', 'ph', type=float, help="pH for protonation using pdb2pqr.")
@click.option('--ff-out', type=click.Choice(['CHARMM', 'AMBER']), default='CHARMM', help="Force field nomenclature for output.")
@click.option('--ssbond', is_flag=True, help="Detect disulfide bonds and add SSBOND lines.")
@click.option('--rename-chain', multiple=True, help="Rename chain: 'old:new' (e.g., 'A:B').")
@click.option('--renumber', type=int, help="Renumber residues starting from this value.")
@click.option('--segid', help="Add/Modify segid for all atoms.")
@click.option('--select-atoms', '--selection-atoms', help="Keep atoms matching an MDAnalysis selection.")
@click.option('--write-ext-crd', is_flag=True, help="Generate an extended CHARMM-GUI style .crd file.")
@click.option('--check-mol-format', is_flag=True, help="Validate the input format (PDB, PSF, CRD, MOL2) and exit.")
@click.option('--prepare-cgenff-inputs', is_flag=True, help="Prepare protein PDB and ligand MOL2 for manual CGenFF Web upload.")
@click.option('--pdb-id', help="RCSB PDB ID; can be used alone to download the official PDB file.")
@click.option('--select-chains', default="", show_default=True, help="Protein chains to keep, separated by commas.")
@click.option('--ligand', type=click.Path(exists=True, dir_okay=False, path_type=Path), help="External ligand PDB for --prepare-cgenff-inputs.")
@click.option('--pdb-ligand-resname', help="Ligand resname in the source PDB.")
@click.option('--pdb-ligand-chain', help="Ligand chain in the source PDB.")
@click.option('--pdb-ligand-resid', help="Ligand resid in the source PDB.")
@click.option('--ligand-pH', 'ligand_pH', type=float, default=7.4, show_default=True, help="Ligand pH used by Open Babel.")
@click.option('--overwrite', is_flag=True, help="Overwrite output directory when preparing CGenFF inputs.")
def pdbwriter(input, mol, psf, output, fix_structure, fix_keep_hetatoms, fix_add_hydrogens, internal_only, ph, ff_out, ssbond, rename_chain, renumber, segid, select_atoms, write_ext_crd, check_mol_format, prepare_cgenff_inputs, pdb_id, select_chains, ligand, pdb_ligand_resname, pdb_ligand_chain, pdb_ligand_resid, ligand_pH, overwrite):
    """PDBWriter: Advanced PDB preparation module."""
    uxm = UnixMessage()
    
    if prepare_cgenff_inputs:
        outdir = Path(output) if output else Path("cgenff_inputs")
        config = CGenFFInputConfig(
            output_dir=outdir,
            protein=Path(input) if input else None,
            pdb_id=pdb_id,
            select_chains=select_chains,
            ligand=ligand,
            pdb_ligand_resname=pdb_ligand_resname,
            pdb_ligand_chain=pdb_ligand_chain,
            pdb_ligand_resid=pdb_ligand_resid,
            ligand_pH=ligand_pH,
            overwrite=overwrite,
        )
        outputs = CGenFFInputPreparer(config).prepare()
        uxm.message(message=f"CGenFF input files prepared in {outdir}.", type="info")
        uxm.message(message=f"Protein: {outputs['protein']}", type="info")
        uxm.message(message=f"Ligand MOL2: {outputs['ligand_mol2']}", type="info")
        return

    has_processing = any((fix_structure, ph is not None, ssbond, rename_chain, renumber is not None, segid, select_atoms, write_ext_crd, check_mol_format))
    if pdb_id and not input and not mol and not has_processing:
        destination = Path(output) if output else Path(f"{pdb_id.lower()}.pdb")
        if destination.exists() and not overwrite:
            raise click.ClickException(f"Output already exists: {destination}. Use --overwrite to replace it.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb"
        temporary = None
        download_target = destination
        if select_chains:
            handle = tempfile.NamedTemporaryFile(suffix=".pdb", prefix="mstbx_download_", delete=False)
            temporary = Path(handle.name)
            handle.close()
            download_target = temporary
        try:
            urllib.request.urlretrieve(url, download_target)
            if select_chains:
                _write_selected_chains(download_target, destination, select_chains)
        except Exception as exc:
            raise click.ClickException(f"Could not download {pdb_id.upper()} from RCSB: {exc}") from exc
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)
        uxm.message(message=f"Downloaded {pdb_id.upper()} to {destination}", type="info")
        return

    # Download first when PDB ID is combined with transformations such as
    # MDAnalysis selection, SSBOND detection, protonation, or CRD writing.
    if pdb_id and not input and not mol:
        handle = tempfile.NamedTemporaryFile(suffix=".pdb", prefix="mstbx_download_", delete=False)
        input = handle.name
        handle.close()
        try:
            urllib.request.urlretrieve(
                f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb", input
            )
        except Exception as exc:
            Path(input).unlink(missing_ok=True)
            raise click.ClickException(f"Could not download {pdb_id.upper()} from RCSB: {exc}") from exc

    if mol and not check_mol_format:
        uxm.message(message="Error: --mol option can ONLY be used with --check-mol-format flag.", type="error")
        raise click.Abort()

    input_file = input or mol
    if not input_file and not (fix_structure and pdb_id):
        uxm.message(message="Error: --input (-i), --mol, or --pdb-id with --fix-structure must be provided.", type="error")
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
    
    writer = PDBWriter(input_file, psf_file=psf, pdb_id=pdb_id if fix_structure and not input_file else None)
    
    if fix_structure:
        uxm.message(message="Running PDBFixer...", type="info")
        writer.fix_structure(
            fix_only_internal=internal_only,
            keep_hetatoms=fix_keep_hetatoms,
            add_hydrogens=fix_add_hydrogens,
            select_chains=[c.strip() for c in select_chains.split(",") if c.strip()] or None,
            pH=ph or 7.0,
        )
    
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

    if select_atoms:
        uxm.message(message=f"Applying MDAnalysis selection: {select_atoms}", type="info")
        writer.select_atoms(select_atoms)
    
    if write_ext_crd:
        crd_output = output if output.endswith('.crd') else output.rsplit('.', 1)[0] + '.crd'
        uxm.message(message="Generating extended CRD...", type="info")
        writer.write_ext_crd(crd_output)
    
    if not output.endswith('.crd') or not write_ext_crd:
        pdb_output = output if output.endswith('.pdb') else output.rsplit('.', 1)[0] + '.pdb'
        writer.write_final_pdb(pdb_output)
    
    uxm.message(message=f"Successfully processed inputs.", type="info")
    uxm.message(message="Check 'pdbwriter_report.log' for details.", type="warning")
