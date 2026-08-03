"""Comando MSTBx para gerar entradas GROMACS."""

from pathlib import Path

import click

from mstbx.core.Gromacs.Index import IndexGroup, SOLUTE, SOLVENT_IONS, GromacsIndex
from mstbx.core.Gromacs.Protocol import GromacsProtocol, GromacsProtocolConfig
from mstbx.core.Gromacs.Restraints import DEFAULT_FORCE, DEFAULT_SELECTION, GromacsRestraints, RestraintConfig
from mstbx.core.Gromacs.Runner import GromacsRunner
from mstbx.core.Utils.Utils import UnixMessage


@click.command(help="Writes GROMACS MDPs, index groups, restraints, and run_all.sh.")
@click.option("--runs-dir", type=click.Path(path_type=Path), default=Path("runs"), show_default=True, help="Runs directory.")
@click.option("--replicas", type=int, default=1, show_default=True, help="Number of replicas.")
@click.option("--temperature", type=float, default=310.0, show_default=True, help="Temperature in K.")
@click.option("--mdtime", "--md-time", type=float, default=100.0, show_default=True, help="Production time in ns.")
@click.option("--xtc-frequency", type=float, default=50.0, show_default=True, help="XTC frame frequency in ps.")
@click.option("--name-group-index-1", default="Protein_ligand", show_default=True, help="First tc-grps index name.")
@click.option("--select-group-index-1", default=SOLUTE, show_default=True, help="First MDAnalysis index selection.")
@click.option("--name-group-index-2", default="Water_and_ions", show_default=True, help="Second tc-grps index name.")
@click.option("--select-group-index-2", default=SOLVENT_IONS, show_default=True, help="Second MDAnalysis index selection.")
@click.option("--select-atoms-to-restraint", default=DEFAULT_SELECTION, show_default=True, help="MDAnalysis selection for position restraints.")
@click.option("--force", type=int, default=DEFAULT_FORCE, show_default=True, help="Restraint force in kJ mol-1 nm-2.")
@click.option("--gmx", default="gmx", show_default=True, help="GROMACS executable used in run_all.sh.")
def gmx_inputs(**kwargs):
    """Executa o comando ``gmx-inputs``.

    Parameters
    ----------
    **kwargs
        Argumentos coletados pelo ``click``.
    """
    uxm = UnixMessage()
    try:
        runs_dir = kwargs["runs_dir"]
        replicas = kwargs["replicas"]
        protocol = GromacsProtocolConfig(runs_dir, replicas, kwargs["temperature"], kwargs["mdtime"], kwargs["xtc_frequency"])
        GromacsProtocol(protocol).write_all()
        groups = [
            IndexGroup(kwargs["name_group_index_1"], kwargs["select_group_index_1"]),
            IndexGroup(kwargs["name_group_index_2"], kwargs["select_group_index_2"]),
        ]
        GromacsIndex(runs_dir, replicas, groups).write_all()
        restraint = RestraintConfig(runs_dir, replicas, kwargs["select_atoms_to_restraint"], kwargs["force"])
        protein_count, ligand_count = GromacsRestraints(restraint).apply_all()
        GromacsRunner(runs_dir, replicas, kwargs["gmx"]).write_all()
        uxm.message(f"GROMACS inputs generated. Restrained atoms: protein={protein_count}, ligand={ligand_count}.", "info")
    except Exception as exc:
        uxm.message(str(exc), "error")
        raise click.Abort() from exc
