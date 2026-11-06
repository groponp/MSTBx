"""Testes unitários e de regressão para o gerador modular de PSF (PSFBuilder)."""

from pathlib import Path
import pytest

from mstbx.core.Build.PSFBuilder import PSFBuilder, PSFBuilderConfig, BuildRawPSF


def _write_minimal_dimer_pdb(path: Path) -> None:
    """Gera um PDB sintético com duas cadeias (A e B)."""
    lines = [
        "ATOM      1  N   ALA A   1       1.000   1.000   1.000  1.00 20.00           N  \n",
        "ATOM      2  CA  ALA A   1       2.000   1.000   1.000  1.00 20.00           C  \n",
        "ATOM      3  C   ALA A   1       2.500   2.000   1.000  1.00 20.00           C  \n",
        "ATOM      4  O   ALA A   1       2.000   3.000   1.000  1.00 20.00           O  \n",
        "TER\n",
        "ATOM      5  N   GLY B   1      10.000  10.000  10.000  1.00 20.00           N  \n",
        "ATOM      6  CA  GLY B   1      11.000  10.000  10.000  1.00 20.00           C  \n",
        "ATOM      7  C   GLY B   1      11.500  11.000  10.000  1.00 20.00           C  \n",
        "ATOM      8  O   GLY B   1      11.000  12.000  10.000  1.00 20.00           O  \n",
        "TER\n",
        "END\n",
    ]
    path.write_text("".join(lines))


def test_detect_protein_chains(tmp_path):
    """Detecta cadeias A e B em um PDB dimérico."""
    pdb = tmp_path / "dimer.pdb"
    _write_minimal_dimer_pdb(pdb)

    config = PSFBuilderConfig(input_pdb=pdb)
    builder = PSFBuilder(config)
    chains = builder.detect_protein_chains()

    assert chains == ["A", "B"]


def test_psf_builder_rejects_missing_pdb(tmp_path):
    """Lança FileNotFoundError se o PDB não existir."""
    missing = tmp_path / "nao_existe.pdb"
    config = PSFBuilderConfig(input_pdb=missing)
    builder = PSFBuilder(config)

    with pytest.raises(FileNotFoundError):
        builder.detect_protein_chains()


def test_psf_builder_script_generation_and_execution(tmp_path, monkeypatch):
    """Testa geração de script TCL e execução sem depender do binário do VMD."""
    pdb = tmp_path / "dimer.pdb"
    _write_minimal_dimer_pdb(pdb)

    out_prefix = "dimer_out"
    config = PSFBuilderConfig(
        input_pdb=pdb,
        output_prefix=out_prefix,
        output_dir=tmp_path,
        vmd_exec="fake_vmd",
    )
    builder = PSFBuilder(config)

    # Simula resolução de VMD e Toppar
    monkeypatch.setattr(builder, "_resolve_vmd", lambda: "fake_vmd")
    monkeypatch.setattr(builder, "_resolve_toppar", lambda: tmp_path / "top_fake.rtf")

    # Simula a execução do subprocess.run gerando arquivos simulados
    def _fake_run(cmd, capture_output, text, check):
        (tmp_path / f"{out_prefix}.psf").write_text("PSF\n\n       8 !NATOM\n")
        (tmp_path / f"{out_prefix}.pdb").write_text("ATOM      1  N   ALA A   1\n")

    monkeypatch.setattr("mstbx.core.Build.PSFBuilder.subprocess.run", _fake_run)

    result = builder.build()
    assert result["psf"].exists()
    assert result["pdb"].exists()
    assert result["psf"].name == f"{out_prefix}.psf"


def test_build_raw_psf_facade_interface(tmp_path, monkeypatch):
    """Verifica se a fachada BuildRawPSF constrói corretamente."""
    pdb = tmp_path / "dimer.pdb"
    _write_minimal_dimer_pdb(pdb)

    def _fake_build(self):
        return {"psf": tmp_path / "system.psf", "pdb": tmp_path / "system.pdb"}

    monkeypatch.setattr(PSFBuilder, "build", _fake_build)

    facade = BuildRawPSF()
    res = facade.build(pdb=pdb, ofile="system", output_dir=tmp_path)
    assert "psf" in res
    assert "pdb" in res


def test_psfbuilder_cli_help_and_invocation():
    """Verifica se o --help do psfbuilder segue o padrão dos comandos MSTBx com [required]."""
    from click.testing import CliRunner
    from mstbx.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["psfbuilder", "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "Options:" in result.output
    assert "--pdb" in result.output
    assert "[required]" in result.output
    assert "--output" in result.output
    assert "--outdir" in result.output
    assert "--chains" in result.output
    assert "--vmd" in result.output
    assert "--logfile" not in result.output



def test_psfbuilder_cli_accepts_both_positional_and_flag(tmp_path, monkeypatch):
    """Verifica se tanto sintaxe posicional quanto --pdb são aceitas pelo CLI."""
    from click.testing import CliRunner
    from mstbx.cli import cli

    pdb = tmp_path / "test.pdb"
    _write_minimal_dimer_pdb(pdb)

    called_with = []

    def _fake_build(self):
        called_with.append(self.config.input_pdb)
        return {"psf": tmp_path / "test.psf", "pdb": tmp_path / "test.pdb"}

    monkeypatch.setattr(PSFBuilder, "build", _fake_build)

    runner = CliRunner()
    res1 = runner.invoke(cli, ["psfbuilder", str(pdb)])
    assert res1.exit_code == 0
    assert called_with[-1] == pdb

    res2 = runner.invoke(cli, ["psfbuilder", "--pdb", str(pdb)])
    assert res2.exit_code == 0
    assert called_with[-1] == pdb


