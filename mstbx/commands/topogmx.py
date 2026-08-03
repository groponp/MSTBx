"""Comando MSTBx para montar topologias e sistemas GROMACS."""

from pathlib import Path

import click

from mstbx.core.Gromacs.Build import DEFAULT_CGENFF_CONVERTER, DEFAULT_FORCEFIELD_DIR, GromacsBuildConfig, GromacsBuilder
from mstbx.core.Utils.Utils import UnixMessage


@click.command(help="Builds one GROMACS topology/system using the MSTBx layout.")
@click.option("--protein", type=click.Path(exists=True, dir_okay=False, path_type=Path), required=True, help="Prepared protein PDB.")
@click.option("--ligand-mol2", type=click.Path(exists=True, dir_okay=False, path_type=Path), help="Ligand MOL2 used for CGenFF.")
@click.option("--ligand-str", type=click.Path(exists=True, dir_okay=False, path_type=Path), help="Ligand STR downloaded from CGenFF.")
@click.option("--ligand-resname", default="LIG", show_default=True, help="Final ligand residue name.")
@click.option("--forcefield-dir", type=click.Path(exists=True, file_okay=False, path_type=Path), default=DEFAULT_FORCEFIELD_DIR, show_default=True, help="CHARMM/CGenFF force-field directory.")
@click.option("--cgenff-converter", type=click.Path(exists=True, dir_okay=False, path_type=Path), default=DEFAULT_CGENFF_CONVERTER, show_default=True, help="cgenff_charmm2gmx_py3 converter.")
@click.option("--output-dir", type=click.Path(path_type=Path), default=Path("runs"), show_default=True, help="Output runs directory.")
@click.option("--box-distance", type=float, default=1.8, show_default=True, help="Solute-box distance in nm.")
@click.option("--gmx", default="gmx", show_default=True, help="GROMACS executable.")
@click.option("--pdb2gmx-ter", is_flag=True, help="Ask pdb2gmx for NTER/CTER states.")
@click.option("--pdb2gmx-selection", help="Text sent to pdb2gmx stdin, for example $'1\\n1\\n'.")
@click.option("--pdb2gmx-protonation", is_flag=True, help="Ask pdb2gmx for HIS/ASP/GLU/LYS/ARG states.")
@click.option("--overwrite", is_flag=True, help="Overwrite the output directory.")
def topogmx(**kwargs):
    """Executa o comando ``topogmx``.

    Parameters
    ----------
    **kwargs
        Argumentos coletados pelo ``click``.
    """
    uxm = UnixMessage()
    try:
        uxm.message("Building GROMACS system...", "info")
        config = GromacsBuildConfig(**kwargs)
        GromacsBuilder(config).build_system()
        uxm.message("GROMACS system built successfully.", "info")
    except Exception as exc:
        uxm.message(str(exc), "error")
        raise click.Abort() from exc
