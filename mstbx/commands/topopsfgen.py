import click
import os
import time
from mstbx.core.Build.PSFGenSol import BuildSolution, BuildSolutionSMD
from mstbx.core.Build.PSFGenMemb import BuildMembrane
from mstbx.core.Utils.ClickHelp import explicit as _explicit
from mstbx.core.Utils.ClickHelp import grouped_command
from mstbx.core.Utils.Utils import UnixMessage

TOPOPSFGEN_OPTION_GROUPS = {
    "Environment": ["env"],
    "Common Options": ["psf", "pdb", "salt", "ofile", "hmr", "padding"],
    "Solution per-axis padding (trigger: --env solution)": [
        "pad_x_pos", "pad_x_neg", "pad_y_pos", "pad_y_neg", "pad_z_pos", "pad_z_neg",
    ],
    "Membrane Options (trigger: --env membrane)": ["mol_outside", "z_distance"],
    "SMD Options (trigger: --env smd)": ["atoms_anchor", "atoms_pull", "extra_space"],
}


def _validate_env_flags(ctx, env, pad_x_pos, pad_x_neg, pad_y_pos, pad_y_neg, pad_z_pos,
                         pad_z_neg, mol_outside, z_distance, atoms_anchor, atoms_pull, extra_space):
    """Reject per-env flags passed under the wrong --env: the builder for
    membrane and SMD systems does not accept per-axis padding at all, and the
    membrane/SMD-only options are simply never read outside their own env,
    so passing them elsewhere used to succeed and silently do nothing."""
    if env != "solution":
        wrong = [
            flag for flag, value in [
                ("--pad-x-pos", pad_x_pos is not None), ("--pad-x-neg", pad_x_neg is not None),
                ("--pad-y-pos", pad_y_pos is not None), ("--pad-y-neg", pad_y_neg is not None),
                ("--pad-z-pos", pad_z_pos is not None), ("--pad-z-neg", pad_z_neg is not None),
            ] if value
        ]
        if wrong:
            raise click.UsageError(
                f"The following flag(s) only apply with --env solution: {', '.join(wrong)}. "
                f"They are not accepted by the --env {env} builder."
            )

    if env != "membrane":
        wrong = [
            flag for flag, value in [
                ("--mol-outside", mol_outside), ("--z-distance", _explicit(ctx, "z_distance")),
            ] if value
        ]
        if wrong:
            raise click.UsageError(
                f"The following flag(s) only apply with --env membrane: {', '.join(wrong)}. "
                f"They have no effect with --env {env}."
            )

    if env != "smd":
        wrong = [
            flag for flag, value in [
                ("--atoms-anchor", atoms_anchor), ("--atoms-pull", atoms_pull),
                ("--extra-space", _explicit(ctx, "extra_space")),
            ] if value
        ]
        if wrong:
            raise click.UsageError(
                f"The following flag(s) only apply with --env smd: {', '.join(wrong)}. "
                f"They have no effect with --env {env}."
            )


@click.command(cls=grouped_command(TOPOPSFGEN_OPTION_GROUPS), help="System generation (PSF/PDB) for different environments.")
@click.option('--env', type=click.Choice(['solution', 'membrane', 'smd']), required=True, help="Environment of the system to build.")
# Common Options
@click.option('--psf', type=click.Path(exists=True, dir_okay=False), required=True, help="Input PSF file.")
@click.option('--pdb', type=click.Path(exists=True, dir_okay=False), required=True, help="Input PDB file.")
@click.option('--salt', default=0.150, help="NaCl concentration (mol/L). Default 0.150.")
@click.option('--ofile', default="macromol150mM", help="Prefix for output files.")
@click.option('--hmr', is_flag=True, help="Enable Hydrogen Mass Repartition.")
@click.option('--padding', type=float, help="Global padding (A). Defaults: 18.0 (Solution/SMD), 25.0 (Membrane).")
@click.option('--pad-x-pos', type=float, help="Specific padding for X+ axis.")
@click.option('--pad-x-neg', type=float, help="Specific padding for X- axis.")
@click.option('--pad-y-pos', type=float, help="Specific padding for Y+ axis.")
@click.option('--pad-y-neg', type=float, help="Specific padding for Y- axis.")
@click.option('--pad-z-pos', type=float, help="Specific padding for Z+ axis.")
@click.option('--pad-z-neg', type=float, help="Specific padding for Z- axis.")
# Membrane Options
@click.option('--mol-outside', is_flag=True, help="Place protein outside the membrane.")
@click.option('--z-distance', default=10.0, help="Distance in Z (A) from the membrane surface.")
# SMD Options
@click.option('--atoms-anchor', help="VMD selection for the fixed group.")
@click.option('--atoms-pull', help="VMD selection for the pulling group.")
@click.option('--extra-space', default=50.0, help="Extra space in Z+ for SMD.")
def topopsfgen(env, psf, pdb, salt, ofile, hmr, padding, pad_x_pos, pad_x_neg, pad_y_pos, pad_y_neg, pad_z_pos, pad_z_neg, mol_outside, z_distance, atoms_anchor, atoms_pull, extra_space):
    """Module to build solvated, membrane, or SMD systems."""
    hmrbool = 1 if hmr else 0
    uxm = UnixMessage()

    _validate_env_flags(
        click.get_current_context(), env, pad_x_pos, pad_x_neg, pad_y_pos, pad_y_neg,
        pad_z_pos, pad_z_neg, mol_outside, z_distance, atoms_anchor, atoms_pull, extra_space,
    )

    if env == 'solution':
        sol_padding = padding if padding is not None else 18.0
        builder = BuildSolution()
        builder.build(psf=psf, pdb=pdb, salt=salt, ofile=ofile, hmr=hmrbool, padding=sol_padding,
                      pad_x_pos=pad_x_pos, pad_x_neg=pad_x_neg, pad_y_pos=pad_y_pos, 
                      pad_y_neg=pad_y_neg, pad_z_pos=pad_z_pos, pad_z_neg=pad_z_neg)
        script_tcl = "PSFGenSol.tcl"

    elif env == 'membrane':
        builder = BuildMembrane()
        peptide = 1 if mol_outside else 0
        memb_padding = padding if padding is not None else 25.0
        builder.build(psf=psf, pdb=pdb, salt=salt, ofile=ofile, hmr=hmrbool, peptide=peptide, 
                      moveZ=z_distance, padding=memb_padding)
        script_tcl = "PSFGenMemb.tcl"

    elif env == 'smd':
        if not atoms_anchor or not atoms_pull:
            message = "--atoms-anchor and --atoms-pull are required for --env smd."
            uxm.message(message, "error")
            raise click.UsageError(message)
        builder = BuildSolutionSMD()
        smd_padding = padding if padding is not None else 18.0
        builder.build(psf=psf, pdb=pdb, salt=salt, ofile=ofile, hmr=hmrbool, atomsvec1=atoms_anchor, 
                      atomsvec2=atoms_pull, extrapadz=extra_space, padding=smd_padding)
        script_tcl = "PSFGenSolSMD.tcl"

    # Common Execution
    uxm.makedir(dirs=["01build"])
    os.chdir("01build")
    uxm.message(f"Working inside: {os.path.abspath('.')}", "info")
    
    if env == 'membrane' and os.path.exists("../step4_lipid.psf"):
        os.system("cp ../step4_*psf .")
        os.system("cp ../step4_*pdb .")
    else:
        os.system("cp ../*psf .")
        os.system("cp ../*pdb .")
        
    os.system(f"mv ../{script_tcl} .")
    os.system(f"vmd -dispdev text -e {script_tcl} 2>&1 | tee psfgen.log")
    time.sleep(2)
    uxm.message(f"{env.capitalize()} system ready in 01build/", "info")
