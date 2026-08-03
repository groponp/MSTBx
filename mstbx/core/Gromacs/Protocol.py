"""Protocolos GROMACS com a nomenclatura de diretórios do MSTBx."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DT = 0.002
COMMON = """cutoff-scheme = Verlet
nstlist = 20
rlist = 1.2
vdwtype = Cut-off
vdw-modifier = Force-switch
rvdw_switch = 1.0
rvdw = 1.2
coulombtype = PME
rcoulomb = 1.2
constraints = h-bonds
constraint_algorithm = LINCS"""


@dataclass
class GromacsProtocolConfig:
    """Parâmetros de protocolo para GROMACS.

    Parameters
    ----------
    runs_dir
        Diretório raiz com ``rep1``, ``rep2`` etc.
    replicas
        Número de réplicas.
    temperature
        Temperatura em Kelvin.
    mdtime
        Tempo de produção em ns.
    xtc_frequency
        Frequência de escrita de XTC em ps.
    """

    runs_dir: Path
    replicas: int = 1
    temperature: float = 310.0
    mdtime: float = 100.0
    xtc_frequency: float = 50.0


class GromacsProtocol:
    """Escreve MDPs ``em``, ``nvt``, ``npt`` e ``md``."""

    def __init__(self, config: GromacsProtocolConfig):
        """Inicializa o protocolo.

        Parameters
        ----------
        config
            Configuração de escrita dos arquivos.
        """
        self.config = config

    def write_all(self) -> list[Path]:
        """Escreve todos os MDPs em todas as réplicas.

        Returns
        -------
        list[pathlib.Path]
            Arquivos criados.
        """
        written = []
        for rep in range(1, self.config.replicas + 1):
            root = self.config.runs_dir / f"rep{rep}"
            written += self.write_replica(root)
        return written

    def write_replica(self, root: Path) -> list[Path]:
        """Escreve os MDPs de uma réplica.

        Parameters
        ----------
        root
            Diretório da réplica.
        """
        xtc = round(self.config.xtc_frequency / DT)
        define = "-DPOSRES -DPOSRES_LIGAND"
        eq = self._equilibration_block(xtc)
        files = {
            root / "01build/em.mdp": f"define = {define}\nintegrator = steep\nemtol = 1000.0\nnsteps = 50000\n{COMMON}",
            root / "02nvt/nvt.mdp": f"define = {define}\n{eq}\nnsteps = {self._steps(5)}\ncontinuation = no\npcoupl = no\ngen-vel = yes\ngen-temp = {self.config.temperature}\ngen-seed = -1",
            root / "03npt/npt.mdp": f"define = {define}\n{eq}\nnsteps = {self._steps(5)}\ncontinuation = yes\npcoupl = C-rescale\npcoupltype = isotropic\ntau_p = 5.0\ncompressibility = 4.5e-5\nref_p = 1.0\ngen-vel = no",
            root / "04md/md.mdp": f"{eq}\nnsteps = {self._steps(self.config.mdtime)}\ncontinuation = yes\npcoupl = C-rescale\npcoupltype = isotropic\ntau_p = 5.0\ncompressibility = 4.5e-5\nref_p = 1.0",
        }
        for path, text in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text.strip() + "\n")
        return list(files)

    def _equilibration_block(self, xtc: int) -> str:
        """Monta bloco comum para NVT, NPT e produção."""
        return f"""{COMMON}
integrator = md
dt = {DT}
nstxout-compressed = {xtc}
nstxout = 0
nstvout = 0
nstfout = 0
nstenergy = 1000
nstlog = 1000
tcoupl = v-rescale
tc_grps = Protein_ligand Water_and_ions
tau_t = 1.0 1.0
ref_t = {self.config.temperature} {self.config.temperature}
nstcomm = 100
comm_mode = linear
comm_grps = Protein_ligand Water_and_ions"""

    @staticmethod
    def _steps(ns: float) -> int:
        """Converte ns para passos com 2 fs."""
        return round(ns * 1000 / DT)
