"""Geração do script geral de execução GROMACS."""

from __future__ import annotations

from pathlib import Path


class GromacsRunner:
    """Escreve ``run_all.sh`` na raiz do sistema."""

    def __init__(self, runs_dir: Path, gmx: str = "gmx"):
        """Inicializa o escritor do runner."""
        self.runs_dir = runs_dir
        self.gmx = gmx

    def write_all(self) -> list[Path]:
        """Escreve o runner do sistema."""
        path = self.runs_dir / "run_all.sh"
        self.write(path)
        return [path]

    def write(self, path: Path) -> None:
        """Escreve um runner compatível com GPU e CPU."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n\n"
            f"GMX=\"${{GMX:-{self.gmx}}}\"\n"
            "MAXWARN=\"${MAXWARN:-2}\"\n"
            "NTMPI=\"${NTMPI:-1}\"\n"
            "NTOMP=\"${NTOMP:-16}\"\n"
            "MDRUN_FLAGS=\"${MDRUN_FLAGS:--update cpu -pin on}\"\n"
            "export OMP_NUM_THREADS=\"$NTOMP\"\n\n"
            "run_stage() {\n"
            "  local stage=\"$1\" name=\"$2\"\n"
            "  shift 2\n"
            "  cd \"$stage\"\n"
            "  \"$GMX\" grompp -f \"${name}.mdp\" \"$@\" -o \"${name}.tpr\" -maxwarn \"$MAXWARN\"\n"
            "  \"$GMX\" mdrun -deffnm \"$name\" -v -ntmpi \"$NTMPI\" -ntomp \"$NTOMP\" $MDRUN_FLAGS\n"
            "  cd ..\n"
            "}\n\n"
            "run_stage 01build em -c ionized.gro -p topol.top -r ionized.gro\n"
            "run_stage 02nvt nvt -c ../01build/em.gro -p ../01build/topol.top -r ../01build/em.gro -n ../01build/index.ndx\n"
            "run_stage 03npt npt -c ../02nvt/nvt.gro -t ../02nvt/nvt.cpt -p ../01build/topol.top -r ../02nvt/nvt.gro -n ../01build/index.ndx\n"
            "run_stage 04md md -c ../03npt/npt.gro -t ../03npt/npt.cpt -p ../01build/topol.top -n ../01build/index.ndx\n"
        )
        path.chmod(0o755)
