"""Testes de regressão para a arquitetura CLI do MSTBx."""

from click.testing import CliRunner

from mstbx.cli import cli


def test_topology_and_protocol_commands_are_separated():
    """Garante que GROMACS usa ``topogmx`` e ``md-inputs``."""
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "topogmx" in result.output
    assert "md-inputs" in result.output
    assert "gmx-build" not in result.output
    assert "gmx-inputs" not in result.output


def test_topogmx_help_exposes_default_forcefield_and_converter():
    """Confirma defaults empacotados para campo de força e conversor."""
    result = CliRunner().invoke(cli, ["topogmx", "--help"])

    assert result.exit_code == 0
    assert "--forcefield-dir" in result.output
    assert "charmm36-feb2026_cgenff-5.0.ff" in result.output
    assert "--cgenff-converter" in result.output
    assert "cgenff_charmm2gmx_py3.py" in result.output
    assert "--replicas" not in result.output


def test_md_inputs_help_exposes_gromacs_branch_defaults():
    """Confirma opções específicas de GROMACS dentro de ``md-inputs``."""
    result = CliRunner().invoke(cli, ["md-inputs", "--help"])

    assert result.exit_code == 0
    assert "--engine [namd|amber|gromacs|openmm]" in result.output
    assert "--runs-dir" in result.output
    assert "--replicas" not in result.output
    assert "--nvt-time" in result.output
    assert "--npt-time" in result.output
    assert "--select-atoms-to-restraint" in result.output
    assert "Protein_ligand" in result.output
