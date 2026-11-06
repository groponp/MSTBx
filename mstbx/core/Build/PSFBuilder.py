"""Construção modular de arquivos de topologia (PSF) e coordenadas (PDB) a partir de PDBs brutos."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import click

from mstbx.core.Utils.Utils import UnixMessage

STANDARD_AMINO_ACIDS = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS",
    "HSD", "HSE", "HSP", "ILE", "LEU", "LYS", "MET", "PHE", "PRO",
    "SER", "THR", "TRP", "TYR", "VAL",
}


@dataclass
class PSFBuilderConfig:
    """Configuração para geração de PSF e PDB com psfgen.

    Parameters
    ----------
    input_pdb
        Arquivo PDB de entrada (estrutura bruta ou reparada).
    output_prefix
        Prefixo dos arquivos gerados (ex: 'system' -> 'system.psf', 'system.pdb').
    output_dir
        Diretório onde os arquivos de saída serão salvos. Se None, usa o diretório do PDB.
    chains
        Lista ou string de cadeias a incluir (ex: ['A', 'B'] ou "A,B").
        Se vazio ou None, todas as cadeias proteicas são detectadas automaticamente.
    toppar_dir
        Diretório contendo os arquivos RTF do CHARMM (default: mstbx/core/toppar).
    vmd_exec
        Executável ou caminho do VMD (default: 'vmd').
    auto_aliases
        Habilita aliases padrão de resíduos e átomos (HIS -> HSD, ILE CD1 -> CD, etc.).
    first_patch
        Patch N-terminal (default: 'NTER').
    last_patch
        Patch C-terminal (default: 'CTER').
    """

    input_pdb: Path
    output_prefix: str = "system"
    output_dir: Path | None = None
    chains: list[str] | str | None = None
    toppar_dir: Path | None = None
    vmd_exec: str = "vmd"
    auto_aliases: bool = True
    first_patch: str = "NTER"
    last_patch: str = "CTER"
    log_file: str | Path | None = None


class PSFBuilder:
    """Gera arquivos PSF e PDB protonados para simulação usando o psfgen do VMD."""

    def __init__(self, config: PSFBuilderConfig):
        self.config = config
        self.uxm = UnixMessage(log_file=config.log_file)

    def _resolve_vmd(self) -> str:
        """Encontra o binário do VMD no PATH ou em locais padrão."""
        if shutil.which(self.config.vmd_exec):
            return self.config.vmd_exec

        # Busca em caminhos comuns de conda e locais do usuário
        home = Path.home()
        candidates = [
            home / ".local/bin/vmd",
            home / "miniconda3/envs/molywood/bin/vmd",
            Path("/usr/local/bin/vmd"),
            Path("/usr/bin/vmd"),
        ]
        for candidate in candidates:
            if candidate.exists() and os.access(candidate, os.X_OK):
                return str(candidate)

        raise FileNotFoundError(
            f"VMD executável '{self.config.vmd_exec}' não foi encontrado. "
            "Certifique-se de que o VMD está instalado e disponível no seu PATH."
        )

    def _resolve_toppar(self) -> Path:
        """Localiza o arquivo de topologia RTF do CHARMM."""
        if self.config.toppar_dir and self.config.toppar_dir.exists():
            top = self.config.toppar_dir / "top_all36_prot.rtf"
            if top.exists():
                return top

        # Padrão: mstbx/core/toppar
        pkg_root = Path(__file__).resolve().parents[2]
        default_top = pkg_root / "core/toppar/top_all36_prot.rtf"
        if default_top.exists():
            return default_top

        # Alternativa de teste dentro de mstbx
        test_top = pkg_root / "testing/aqp/charmm-gui-2071415745/toppar/top_all36_prot.rtf"
        if test_top.exists():
            return test_top

        raise FileNotFoundError(
            "Arquivo de topologia CHARMM ('top_all36_prot.rtf') não foi encontrado."
        )

    def detect_protein_chains(self) -> list[str]:
        """Detecta as cadeias proteicas presentes no PDB."""
        if not self.config.input_pdb.exists():
            raise FileNotFoundError(f"Arquivo PDB não encontrado: {self.config.input_pdb}")

        found_chains = []
        with open(self.config.input_pdb, "r") as f:
            for line in f:
                if line.startswith(("ATOM  ", "HETATM")):
                    resname = line[17:20].strip()
                    chain_id = line[21].strip()
                    if resname in STANDARD_AMINO_ACIDS:
                        chain = chain_id if chain_id else "A"
                        if chain not in found_chains:
                            found_chains.append(chain)

        if not found_chains:
            raise ValueError(f"Nenhuma cadeia proteica detectada em {self.config.input_pdb}")

        return found_chains

    def build(self) -> dict[str, Path]:
        """Executa a construção da topologia PSF e PDB."""
        input_pdb = self.config.input_pdb.resolve()
        if not input_pdb.exists():
            raise FileNotFoundError(f"PDB de entrada não encontrado: {input_pdb}")

        out_dir = self.config.output_dir.resolve() if self.config.output_dir else input_pdb.parent
        out_dir.mkdir(parents=True, exist_ok=True)

        vmd = self._resolve_vmd()
        top_rtf = self._resolve_toppar()

        # Determina quais cadeias usar
        available_chains = self.detect_protein_chains()
        if self.config.chains:
            if isinstance(self.config.chains, str):
                requested = [c.strip() for c in self.config.chains.split(",") if c.strip()]
            else:
                requested = list(self.config.chains)
            chains_to_process = [c for c in requested if c in available_chains]
            if not chains_to_process:
                raise ValueError(
                    f"Cadeias requisitadas {requested} não foram encontradas em {available_chains}"
                )
        else:
            chains_to_process = available_chains

        self.uxm.message(
            f"Construindo PSF para {input_pdb.name} (cadeias: {', '.join(chains_to_process)})...",
            "info"
        )

        out_psf = out_dir / f"{self.config.output_prefix}.psf"
        out_pdb = out_dir / f"{self.config.output_prefix}.pdb"
        tcl_script_path = out_dir / f"psfgen_{self.config.output_prefix}.tcl"

        # Monta o script TCL para o psfgen do VMD
        tcl_lines = [
            "package require psfgen",
            f"topology \"{top_rtf}\"",
        ]

        if self.config.auto_aliases:
            tcl_lines.extend([
                "pdbalias residue HIS HSD",
                "pdbalias atom ILE CD1 CD",
            ])

        # Extrai cada cadeia e adiciona segmento
        tcl_lines.append(f"mol new \"{input_pdb}\"")
        chain_files = []
        for chain in chains_to_process:
            seg_name = f"PRO{chain}" if len(chain) == 1 else chain[:4].upper()
            chain_pdb = out_dir / f"tmp_chain_{chain}.pdb"
            chain_files.append(chain_pdb)

            tcl_lines.append(f"set sel [atomselect top \"protein and chain {chain}\"]")
            tcl_lines.append(f"$sel writepdb \"{chain_pdb}\"")
            tcl_lines.append("$sel delete")

            tcl_lines.append(f"segment {seg_name} {{")
            tcl_lines.append(f"    first {self.config.first_patch}")
            tcl_lines.append(f"    last {self.config.last_patch}")
            tcl_lines.append(f"    pdb \"{chain_pdb}\"")
            tcl_lines.append("}")
            tcl_lines.append(f"coordpdb \"{chain_pdb}\" {seg_name}")

        tcl_lines.extend([
            "mol delete top",
            "guesscoord",
            f"writepsf \"{out_psf}\"",
            f"writepdb \"{out_pdb}\"",
            "quit",
        ])

        with open(tcl_script_path, "w") as f:
            f.write("\n".join(tcl_lines) + "\n")

        # Executa o VMD em modo texto
        try:
            res = subprocess.run(
                [vmd, "-dispdev", "text", "-e", str(tcl_script_path)],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Falha ao executar o psfgen no VMD: {exc.stderr}") from exc
        finally:
            # Limpa arquivos temporários
            if tcl_script_path.exists():
                tcl_script_path.unlink()
            for cf in chain_files:
                if cf.exists():
                    cf.unlink()

        if not out_psf.exists() or not out_pdb.exists():
            raise RuntimeError("psfgen falhou em gerar os arquivos finais .psf ou .pdb")

        # Verifica contagem de átomos no PSF gerado
        natoms = 0
        with open(out_psf, "r") as f:
            for line in f:
                if "!NATOM" in line:
                    natoms = int(line.split()[0])
                    break

        self.uxm.message(
            f"Sucesso: {out_psf.name} e {out_pdb.name} gerados ({natoms} átomos).",
            "info"
        )

        return {"psf": out_psf, "pdb": out_pdb}


class BuildRawPSF:
    """Interface compatível com o estilo de outros builders em mstbx.core.Build."""

    def __init__(self) -> None:
        pass

    def build(
        self,
        pdb: str | Path,
        ofile: str = "system",
        chains: list[str] | str | None = None,
        output_dir: str | Path | None = None,
    ) -> dict[str, Path]:
        config = PSFBuilderConfig(
            input_pdb=Path(pdb),
            output_prefix=ofile,
            output_dir=Path(output_dir) if output_dir else None,
            chains=chains,
        )
        return PSFBuilder(config).build()


@click.command(help="Gera arquivos PSF e PDB protonados a partir de um PDB bruto.")
@click.argument(
    "pdb_arg",
    required=False,
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "--pdb", "-p", "pdb_opt",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Arquivo PDB de entrada (ex: 1HSG.pdb)."
)
@click.option(
    "--output", "-o", "output_prefix",
    default=None,
    help="Prefixo dos arquivos gerados (default: mesmo nome do arquivo PDB)."
)
@click.option(
    "--outdir", "-d", "output_dir",
    type=click.Path(file_okay=False),
    default=None,
    help="Diretório onde salvar os arquivos (default: pasta atual)."
)
@click.option(
    "--chains", "-c",
    default=None,
    help="Cadeias proteicas a incluir separadas por vírgula (ex: 'A,B')."
)
@click.option(
    "--vmd", "vmd_exec",
    default="vmd",
    help="Executável ou caminho para o VMD (default: 'vmd')."
)
@click.option(
    "--logfile", "-l", "log_file",
    default=None,
    help="Nome do arquivo de log (default: psf_builder.log)."
)
def main(
    pdb_arg: str | None,
    pdb_opt: str | None,
    output_prefix: str | None,
    output_dir: str | None,
    chains: str | None,
    vmd_exec: str,
    log_file: str | None,
):
    """Entry point de linha de comando para o PSFBuilder."""
    input_file = pdb_arg or pdb_opt
    if not input_file:
        raise click.UsageError(
            "É obrigatório informar o arquivo PDB. Exemplo:\n"
            "  $MSTBx/PSFBuilder.py 1HSG.pdb\n"
            "  $MSTBx/PSFBuilder.py --pdb 1HSG.pdb"
        )

    p = Path(input_file)
    prefix = output_prefix if output_prefix else p.stem
    out_dir = Path(output_dir).resolve() if output_dir else Path.cwd()

    config = PSFBuilderConfig(
        input_pdb=p,
        output_prefix=prefix,
        output_dir=out_dir,
        chains=chains,
        vmd_exec=vmd_exec,
        log_file=log_file,
    )
    builder = PSFBuilder(config)
    builder.build()


if __name__ == "__main__":
    main()
