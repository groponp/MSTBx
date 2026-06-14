import click
from mstbx.commands import topopsfgen, topotleap, md_inputs, smd_inputs, metad_inputs, pdbwriter, colabfold, mkdocking_cmplx, md_translate, resetpsf, openmm_run

@click.group(help="MSTBx: Molecular Simulation ToolBox. Un ecosistema modular para la preparación de simulaciones de Dinámica Molecular.")
@click.version_option(version="0.8.10-beta")
def cli():

    """Portal principal de MSTBx."""
    pass

# Registramos los módulos con nombres claros y descripciones
cli.add_command(topopsfgen.topopsfgen, name="topopsfgen")
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
