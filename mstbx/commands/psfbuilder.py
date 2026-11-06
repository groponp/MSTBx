"""Comando CLI para o PSFBuilder: constrói arquivos PSF/PDB a partir de um PDB bruto."""

from __future__ import annotations

from pathlib import Path
import click

from mstbx.core.Build.PSFBuilder import PSFBuilder, PSFBuilderConfig


class PSFBuilderCommand(click.Command):
    """Click Command permitindo sintaxe padrão com opções e argumento posicional."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        if args and not args[0].startswith("-") and "--pdb" not in args and "-p" not in args:
            args = ["--pdb", args[0]] + args[1:]
        return super().parse_args(ctx, args)


@click.command(cls=PSFBuilderCommand, help="Builds PSF and protonated PDB files from a raw PDB structure.")
@click.option("--pdb", "-p", type=click.Path(exists=True, dir_okay=False), required=True, help="Input PDB file.")
@click.option("--output", "-o", default=None, help="Prefix for output files (default: PDB basename).")
@click.option("--outdir", "-d", type=click.Path(file_okay=False), default=None, help="Output directory (default: current directory).")
@click.option("--chains", "-c", default=None, help="Protein chains to include, comma-separated (e.g. 'A,B').")
@click.option("--vmd", default="vmd", show_default=True, help="VMD executable or path.")
def psfbuilder(
    pdb: str,
    output: str | None,
    outdir: str | None,
    chains: str | None,
    vmd: str,
):
    """Entry point do comando psfbuilder no CLI do MSTBx."""
    p = Path(pdb)
    prefix = output if output else p.stem
    out_dir = Path(outdir).resolve() if outdir else Path.cwd()

    config = PSFBuilderConfig(
        input_pdb=p,
        output_prefix=prefix,
        output_dir=out_dir,
        chains=chains,
        vmd_exec=vmd,
    )
    builder = PSFBuilder(config)
    builder.build()
