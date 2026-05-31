import click
from mstbx.core.Utils.Utils import UnixMessage

@click.group(help="Generación de sistemas para AMBER (prmtop/inpcrd).")
def topotleap():
    """Módulo para construir sistemas usando tLeap (AMBER)."""
    pass

@topotleap.command(name="sol", help="Construye un sistema en solución usando tLeap.")
@click.option('--pdb', type=click.Path(exists=True), required=True, help="Archivo PDB de entrada.")
@click.option('--padding', default=15.0, help="Padding para la caja de agua.")
def sol(pdb, padding):
    uxm = UnixMessage()
    uxm.message("Módulo topotleap sol en desarrollo...", "warning")
    # TODO: Implementar lógica de tLeap
