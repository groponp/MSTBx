import click
from mstbx.commands import autopsfgen, namdinputs, pdbwriter, colabfold, mkdocking_cmplx

@click.group(help="MSTBx: Molecular Simulation ToolBox. Un ecosistema modular para la preparación de simulaciones de Dinámica Molecular.")
@click.version_option(version="0.7.2")
def cli():
    """Portal principal de MSTBx."""
    pass

# Registramos los módulos con nombres claros y descripciones
cli.add_command(autopsfgen.autopsfgen, name="autopsfgen")
cli.add_command(namdinputs.namdinputs, name="namdinputs")
cli.add_command(pdbwriter.pdbwriter, name="pdbwriter")
cli.add_command(colabfold.colabfold, name="colabfold")
cli.add_command(mkdocking_cmplx.mkdocking_cmplx, name="mkdocking-cmplx")

if __name__ == "__main__":
    cli()
