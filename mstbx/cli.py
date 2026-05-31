import click
from mstbx.commands import autopsfgen, namdinputs, pdbwriter, colabfold, mkdocking_cmplx

@click.group()
@click.version_option(version="0.6.0")
def cli():
    """MSTBx: Molecular Simulation ToolBox"""
    pass

cli.add_command(autopsfgen.autopsfgen)
cli.add_command(namdinputs.namdinputs)
cli.add_command(pdbwriter.pdbwriter)
cli.add_command(colabfold.colabfold)
cli.add_command(mkdocking_cmplx.mkdocking_cmplx)

if __name__ == "__main__":
    cli()
