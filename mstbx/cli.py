import click
from mstbx.commands import autopsfgen, namdinputs

@click.group()
@click.version_option(version="0.6.0")
def cli():
    """MSTBx: Molecular Simulation ToolBox"""
    pass

cli.add_command(autopsfgen.autopsfgen)
cli.add_command(namdinputs.namdinputs)

if __name__ == "__main__":
    cli()
