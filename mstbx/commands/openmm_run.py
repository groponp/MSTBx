import click
import os
import sys
from mstbx.core.Utils.Utils import UnixMessage
from mstbx.core.MDProtocols.OpenMMRunner import run_simulation, generate_default_inps

@click.command(help="Strict Manual OpenMM Runner for CHARMM-GUI systems.")
@click.option('-i', '--inp', type=click.Path(exists=True, dir_okay=False), help="Input file (.inp)")
@click.option('-p', '--psf', type=click.Path(exists=True, dir_okay=False), help="Topology file (.psf)")
@click.option('-c', '--pdb', type=click.Path(exists=True, dir_okay=False), help="Coordinates file (.pdb)")
@click.option('--mk-inp', is_flag=True, help="Generate default .inp templates (min.inp, eq1.inp, prod.inp)")
@click.option('-irst', '--irst', type=click.Path(exists=True, dir_okay=False), help="Input restart (.rst)")
@click.option('-orst', '--orst', default="output", help="Output prefix")
@click.option('--toppar', default="toppar/", help="Toppar directory")
@click.option('--pbc', default=None, help="PBC str file")
@click.option('--platform', help="Force platform (CUDA, OpenCL, CPU)")
@click.option('--ns', type=float, help="Override duration in nanoseconds")
@click.option('--rewrap', is_flag=True, help="Apply centering (Original CHARMM-GUI logic)")
@click.option('--debug', is_flag=True, help="Enable debug mode")
def openmm_run(inp, psf, pdb, mk_inp, irst, orst, toppar, pbc, platform, ns, rewrap, debug):
    uxm = UnixMessage()
    
    if mk_inp:
        generate_default_inps()
        return

    # Check if user EXPLICITLY passed pbc along with irst
    # We inspect sys.argv for both '--pbc' and '-irst' / '--irst'
    pbc_passed = any(arg.startswith('--pbc') for arg in sys.argv)
    
    if irst and pbc_passed:
        uxm.message("You cannot provide both a restart file (--irst) and an explicit PBC file (--pbc) at the same time. The PBC is strictly taken from the restart file to ensure continuity.", "error")
        sys.exit(1)
        
    if not pbc:
        pbc = '01build/step3_pbcsetup.str'

    if not inp or not psf or not pdb:
        uxm.message("Missing required options. You must specify -i/--inp, -p/--psf, and -c/--pdb.", "error")
        # Print help
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        sys.exit(1)

    uxm.message(f"Starting OpenMM simulation run with input={inp}, psf={psf}, pdb={pdb}...", "info")
    
    # Run the core simulation logic (Chef)
    run_simulation(
        args_psf=psf,
        args_pdb=pdb,
        args_inp=inp,
        args_irst=irst,
        args_orst=orst,
        args_toppar=toppar,
        args_pbc=pbc,
        args_platform=platform,
        args_ns=ns,
        args_rewrap=rewrap,
        args_debug=debug
    )
    
    uxm.message("Simulation finished successfully.", "info")
