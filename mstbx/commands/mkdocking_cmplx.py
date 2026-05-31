import click
from mstbx.core.Docking.ComplexBuilder import ComplexBuilder
from mstbx.core.Utils.Utils import UnixMessage

@click.command()
@click.option('--protein', '-p', required=True, help="Protein PDB file.")
@click.option('--dock', '-d', help="PDBQT file from docking (MODEL 1 will be used).")
@click.option('--ligand-pdb', help="Ligand PDB file (if not using PDBQT).")
@click.option('--ph', type=float, default=7.4, help="pH for ligand protonation (default 7.4).")
@click.option('--output', '-o', required=True, help="Final complex PDB name.")
def mkdocking_cmplx(protein, dock, ligand_pdb, ph, output):
    """mkdocking-cmplx: Generate protein-ligand complex from docking poses."""
    uxm = UnixMessage()
    
    if not dock and not ligand_pdb:
        uxm.message(message="Error: Either --dock or --ligand-pdb must be provided.", type="error")
        return

    uxm.message(message=f"Building complex for {protein}", type="info")
    builder = ComplexBuilder(protein, output)
    
    is_pdbqt = True if dock else False
    ligand_input = dock if dock else ligand_pdb
    
    if builder.build(ligand_input, ligand_pH=ph, is_pdbqt=is_pdbqt):
        uxm.message(message=f"Complex successfully created: {output}", type="info")
    else:
        uxm.message(message="Failed to build complex.", type="error")
