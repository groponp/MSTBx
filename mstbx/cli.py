import click
from mstbx.commands import (
    colabfold,
    md_inputs,
    md_translate,
    metad_inputs,
    mkdocking_cmplx,
    openmm_run,
    pdbwriter,
    resetpsf,
    smd_inputs,
    topogmx,
    topopsfgen,
    topotleap,
)

@click.group(help="MSTBx: Molecular Simulation ToolBox. A modular ecosystem for molecular dynamics workflows.")
@click.version_option(version="0.8.10-beta")
def cli():

    """Portal principal do MSTBx."""
    pass

# Registramos los módulos con nombres claros y descripciones
cli.add_command(topopsfgen.topopsfgen, name="topopsfgen")
cli.add_command(topogmx.topogmx, name="topogmx")
cli.add_command(topotleap.topotleap, name="topotleap")
cli.add_command(md_inputs.md_inputs, name="md-inputs")
cli.add_command(smd_inputs.smd_inputs, name="smd-inputs")
cli.add_command(metad_inputs.metad_inputs, name="metad-inputs")
cli.add_command(pdbwriter.pdbwriter, name="pdbwriter")
cli.add_command(colabfold.colabfold, name="colabfold")
cli.add_command(mkdocking_cmplx.mkdocking_cmplx, name="mkdocking-cmplx")
cli.add_command(md_translate.md_translate, name="md-translate")
cli.add_command(resetpsf.resetpsf, name="resetpsf")
cli.add_command(openmm_run.openmm_run, name="openmm-run")



if __name__ == "__main__":
    cli()
