from pathlib import Path
import subprocess

import click
from mstbx.core.Docking.ComplexBuilder import ComplexBuilder
from mstbx.core.Utils.Utils import UnixMessage

@click.command(
    help="Build a protein-ligand PDB complex from a docking pose.",
    epilog="""Examples:
  mstbx mkdocking-cmplx --protein receptor.pdb --dock vina_out.pdbqt -o complex.pdb
  mstbx mkdocking-cmplx --protein receptor.pdb --ligand-pdb ligand.pdb -o complex.pdb
  mstbx pdbwriter --input complex.pdb --select-atoms \"protein or resname LIG\" -o complex_clean.pdb

The command writes a PDB complex only. Use topogmx or topopsfgen afterwards to
create the simulation topology and solvated system.""",
)
@click.option('--protein', '-p', required=True, help="Protein PDB file.")
@click.option('--dock', '-d', help="PDBQT file from docking (MODEL 1 will be used).")
@click.option('--ligand-pdb', help="Ligand PDB file (if not using PDBQT).")
@click.option('--pH', 'ph', type=float, default=7.4, show_default=True, help="pH for ligand protonation during MOL2 conversion.")
@click.option('--output', '-o', required=True, help="Final complex PDB name.")
def mkdocking_cmplx(protein, dock, ligand_pdb, ph, output):
    """mkdocking-cmplx: Generate protein-ligand complex from docking poses."""
    uxm = UnixMessage()
    
    if not dock and not ligand_pdb:
        message = "Either --dock or --ligand-pdb must be provided."
        uxm.message(message=message, type="error")
        raise click.UsageError(message)
    if dock and ligand_pdb:
        message = "Use only one ligand source: --dock or --ligand-pdb."
        uxm.message(message=message, type="error")
        raise click.UsageError(message)

    Path(output).parent.mkdir(parents=True, exist_ok=True)

    uxm.message(message=f"Building complex for {protein}", type="info")
    builder = ComplexBuilder(protein, output)
    
    is_pdbqt = True if dock else False
    ligand_input = dock if dock else ligand_pdb
    
    try:
        built = builder.build(ligand_input, ligand_pH=ph, is_pdbqt=is_pdbqt)
    except (FileNotFoundError, OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        uxm.message(message=str(error), type="error")
        raise click.ClickException(str(error)) from error
    if not built:
        message = "Failed to build complex."
        uxm.message(message=message, type="error")
        raise click.ClickException(message)
    uxm.message(message=f"Complex successfully created: {output}", type="info")
