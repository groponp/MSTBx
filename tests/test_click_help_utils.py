"""Unit tests for the shared mstbx.core.Utils.ClickHelp helpers, isolated
from any specific mstbx command."""

import click
from click.testing import CliRunner

from mstbx.core.Utils.ClickHelp import explicit, grouped_command


def _sample_command():
    groups = {
        "Alpha": ["one", "two"],
        "Beta": ["three"],
    }

    @click.command(cls=grouped_command(groups))
    @click.option("--one", default="a", show_default=True, help="First alpha option.")
    @click.option("--two", is_flag=True, help="Second alpha option.")
    @click.option("--three", default="b", show_default=True, help="Only beta option.")
    @click.option("--unclassified", is_flag=True, help="Not in any group.")
    def cmd(one, two, three, unclassified):
        click.echo(f"one={one} two={two} three={three} unclassified={unclassified}")

    return cmd


def test_grouped_command_renders_titled_sections_in_declared_order():
    result = CliRunner().invoke(_sample_command(), ["--help"])

    assert result.exit_code == 0
    assert "Alpha" in result.output
    assert "Beta" in result.output
    assert result.output.index("Alpha") < result.output.index("Beta")
    assert "--one" in result.output
    assert "--three" in result.output


def test_grouped_command_puts_unlisted_params_in_other_options():
    result = CliRunner().invoke(_sample_command(), ["--help"])

    assert "Other Options" in result.output
    other_section = result.output.split("Other Options")[1]
    assert "--unclassified" in other_section
    assert "--help" in other_section


def test_grouped_command_custom_other_title():
    @click.command(cls=grouped_command({"Only": ["flag"]}, other_title="Misc"))
    @click.option("--flag", is_flag=True)
    def cmd(flag):
        pass

    result = CliRunner().invoke(cmd, ["--help"])

    assert "Misc" in result.output
    assert "Other Options" not in result.output


def test_grouped_command_still_executes_normally():
    """format_options is a pure rendering override; command dispatch and
    parsing must be unaffected."""
    result = CliRunner().invoke(_sample_command(), ["--one", "x", "--three", "y"])

    assert result.exit_code == 0
    assert "one=x two=False three=y" in result.output


def test_explicit_distinguishes_commandline_value_from_default():
    seen = {}

    @click.command()
    @click.option("--flag", default="fallback")
    def cmd(flag):
        ctx = click.get_current_context()
        seen["explicit"] = explicit(ctx, "flag")

    CliRunner().invoke(cmd, [])
    assert seen["explicit"] is False

    CliRunner().invoke(cmd, ["--flag", "fallback"])
    assert seen["explicit"] is True

    CliRunner().invoke(cmd, ["--flag", "other"])
    assert seen["explicit"] is True
