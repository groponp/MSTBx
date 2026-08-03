"""Cobertura de contrato para todas as ferramentas expostas pelo CLI."""

from pathlib import Path

from click.testing import CliRunner

from mstbx.cli import cli


COMMANDS = [
    "topopsfgen",
    "topogmx",
    "topotleap",
    "md-inputs",
    "smd-inputs",
    "metad-inputs",
    "pdbwriter",
    "colabfold",
    "mkdocking-cmplx",
    "md-translate",
    "resetpsf",
    "openmm-run",
]


def test_every_registered_command_has_help_and_examples_or_usage():
    """Every registered command is discoverable without importing optional tools."""
    runner = CliRunner()
    for command in COMMANDS:
        result = runner.invoke(cli, [command, "--help"])
        assert result.exit_code == 0, f"{command}: {result.output}"
        assert "Usage:" in result.output
        assert "Options:" in result.output or command == "topotleap"


def test_nested_topotleap_command_has_help():
    """The AMBER namespace exposes its solution subcommand explicitly."""
    result = CliRunner().invoke(cli, ["topotleap", "sol", "--help"])

    assert result.exit_code == 0
    assert "--pdb" in result.output
    assert "--padding" in result.output


def test_cli_rejects_unknown_commands_without_traceback():
    """Malformed command names fail at Click's boundary."""
    result = CliRunner().invoke(cli, ["does-not-exist"])

    assert result.exit_code != 0
    assert "No such command" in result.output
    assert "Traceback" not in result.output


def test_cli_rejects_incomplete_required_options():
    """Required input contracts are enforced before Chef execution."""
    runner = CliRunner()
    cases = [
        ["topogmx"],
        ["pdbwriter", "--fix-structure"],
        ["resetpsf"],
        ["openmm-run"],
        ["md-inputs", "--env", "solution"],
    ]

    for args in cases:
        result = runner.invoke(cli, args)
        assert result.exit_code != 0, args
        assert (
            "Missing option" in result.output
            or "require" in result.output.lower()
            or "must be provided" in result.output
        )
        assert "Traceback" not in result.output


def test_pdbwriter_help_contains_reproducible_examples():
    """PDBWriter help documents the combinations users commonly need."""
    result = CliRunner().invoke(cli, ["pdbwriter", "--help"])

    assert result.exit_code == 0
    for text in [
        "--pdb-id 7A3S",
        "--select-atoms",
        "chainID B C",
        "PROB,PROC",
        "--ssbond",
        "--write-ext-crd",
    ]:
        assert text in result.output


def test_mkdocking_help_contains_pdb_and_pdbqt_scenarios():
    """Docking help documents both supported ligand sources and the boundary."""
    result = CliRunner().invoke(cli, ["mkdocking-cmplx", "--help"])

    assert result.exit_code == 0
    assert "--dock" in result.output
    assert "--ligand-pdb" in result.output
    assert "topogmx" in result.output


def test_help_defaults_are_exposed_for_gromacs_and_openmm():
    """Stable defaults remain visible for reproducible invocation."""
    runner = CliRunner()
    gmx = runner.invoke(cli, ["topogmx", "--help"])
    md = runner.invoke(cli, ["md-inputs", "--help"])
    openmm = runner.invoke(cli, ["openmm-run", "--help"])

    assert "[default: 1.8]" in gmx.output
    assert "[default: runs]" in md.output
    assert "--mk-inp" in openmm.output


def test_md_inputs_help_groups_options_by_engine():
    """md-inputs --help must render real NAMD/GROMACS sections, not a
    hand-wrapped epilog string (see the pdbwriter epilog regression)."""
    result = CliRunner().invoke(cli, ["md-inputs", "--help"])

    assert result.exit_code == 0
    for title in ["General:", "NAMD (trigger: --engine namd):", "GROMACS (trigger: --engine gromacs):"]:
        assert title in result.output, title
    gromacs_section = result.output.split("GROMACS (trigger: --engine gromacs):")[1]
    assert "--force" in gromacs_section and "2092" in gromacs_section
    namd_section = result.output.split("NAMD (trigger: --engine namd):")[1]
    assert "--dcdfreq" in namd_section and "DCD" in namd_section


def test_gromacs_cli_rejects_membrane_until_supported(tmp_path):
    """The unsupported GROMACS membrane branch fails clearly, not silently."""
    result = CliRunner().invoke(
        cli,
        ["md-inputs", "--engine", "gromacs", "--env", "membrane", "--runs-dir", str(tmp_path / "runs")],
    )

    assert result.exit_code != 0
    assert "supports only" in result.output
    assert "Traceback" not in result.output
    assert not (tmp_path / "runs").exists()


def test_unimplemented_engine_branches_are_explicit():
    """AMBER/OpenMM branches report their current support boundary and fail
    with a non-zero exit code instead of a misleading success."""
    runner = CliRunner()
    md = runner.invoke(cli, ["md-inputs", "--engine", "amber", "--env", "solution"])
    smd = runner.invoke(
        cli,
        ["smd-inputs", "--engine", "gromacs", "--psf", "missing.psf", "--pdb", "missing.pdb",
         "--selpull", "name CA", "--selanchor", "name N", "--target-center", "5"],
    )

    assert md.exit_code != 0
    assert "not yet implemented" in md.output
    assert "Traceback" not in md.output
    assert smd.exit_code != 0


def test_topogmx_rejects_only_one_ligand_file(tmp_path):
    """CGenFF ligand inputs are an atomic MOL2+STR pair."""
    protein = tmp_path / "protein.pdb"
    mol2 = tmp_path / "ligand.mol2"
    protein.write_text("END\n")
    mol2.write_text("@<TRIPOS>MOLECULE\nLIG\n")

    result = CliRunner().invoke(
        cli,
        ["topogmx", "--protein", str(protein), "--ligand-mol2", str(mol2), "--output-dir", str(tmp_path / "runs")],
    )

    assert result.exit_code != 0
    assert "MOL2 and STR" in result.output
    assert "Traceback" not in result.output


def test_topogmx_rejects_pdb2gmx_selection_with_protonation(tmp_path):
    """--pdb2gmx-protonation adds interactive residue prompts on top of the
    terminal prompts; piping --pdb2gmx-selection's short stdin into that
    would silently answer the wrong prompt instead of failing loudly."""
    protein = tmp_path / "protein.pdb"
    protein.write_text("END\n")

    result = CliRunner().invoke(
        cli,
        ["topogmx", "--protein", str(protein), "--output-dir", str(tmp_path / "runs"),
         "--pdb2gmx-selection", "0\n0\n", "--pdb2gmx-protonation"],
    )

    assert result.exit_code != 0
    assert "--pdb2gmx-selection" in result.output
    assert "--pdb2gmx-protonation" in result.output
    assert "Traceback" not in result.output
