"""CLI-level coverage for topopsfgen: valid dispatch and env/flag validation."""

from click.testing import CliRunner

from mstbx.commands.topopsfgen import topopsfgen


class FakeBuilder:
    """Records the arguments passed to build() without touching VMD."""

    calls = []

    def build(self, **kwargs):
        FakeBuilder.calls.append(kwargs)


def _inputs(tmp_path):
    psf = tmp_path / "input.psf"
    pdb = tmp_path / "input.pdb"
    psf.write_text("PSF\n")
    pdb.write_text("END\n")
    return psf, pdb


def _run(monkeypatch, tmp_path, args):
    import mstbx.commands.topopsfgen as command

    FakeBuilder.calls = []
    monkeypatch.setattr(command, "BuildSolution", FakeBuilder)
    monkeypatch.setattr(command, "BuildMembrane", FakeBuilder)
    monkeypatch.setattr(command, "BuildSolutionSMD", FakeBuilder)
    monkeypatch.setattr(command.os, "system", lambda cmd: 0)
    monkeypatch.setattr(command.time, "sleep", lambda seconds: None)
    monkeypatch.chdir(tmp_path)
    return CliRunner().invoke(topopsfgen, args)


def test_topopsfgen_solution_forwards_per_axis_padding(tmp_path, monkeypatch):
    """The one env that actually accepts per-axis padding gets it."""
    psf, pdb = _inputs(tmp_path)
    result = _run(
        monkeypatch, tmp_path,
        ["--env", "solution", "--psf", str(psf), "--pdb", str(pdb),
         "--pad-z-pos", "30.0"],
    )

    assert result.exit_code == 0, result.output
    assert FakeBuilder.calls[0]["pad_z_pos"] == 30.0


def test_topopsfgen_smd_requires_anchor_and_pull(tmp_path, monkeypatch):
    """The existing SMD required-flags check must actually fail, not just log."""
    psf, pdb = _inputs(tmp_path)
    result = _run(
        monkeypatch, tmp_path,
        ["--env", "smd", "--psf", str(psf), "--pdb", str(pdb)],
    )

    assert result.exit_code != 0
    assert "--atoms-anchor and --atoms-pull are required" in result.output
    assert "Traceback" not in result.output
    assert not FakeBuilder.calls


def test_topopsfgen_rejects_solution_padding_flags_outside_solution(tmp_path, monkeypatch):
    """--pad-z-pos etc. are silently dropped by the membrane/SMD builders;
    the CLI must reject them instead of pretending they applied."""
    psf, pdb = _inputs(tmp_path)
    result = _run(
        monkeypatch, tmp_path,
        ["--env", "membrane", "--psf", str(psf), "--pdb", str(pdb), "--pad-z-pos", "30.0"],
    )

    assert result.exit_code != 0
    assert "--pad-z-pos" in result.output
    assert "--env solution" in result.output
    assert not FakeBuilder.calls


def test_topopsfgen_rejects_membrane_flags_outside_membrane(tmp_path, monkeypatch):
    psf, pdb = _inputs(tmp_path)
    result = _run(
        monkeypatch, tmp_path,
        ["--env", "solution", "--psf", str(psf), "--pdb", str(pdb), "--mol-outside"],
    )

    assert result.exit_code != 0
    assert "--mol-outside" in result.output
    assert not FakeBuilder.calls


def test_topopsfgen_rejects_smd_flags_outside_smd(tmp_path, monkeypatch):
    psf, pdb = _inputs(tmp_path)
    result = _run(
        monkeypatch, tmp_path,
        ["--env", "solution", "--psf", str(psf), "--pdb", str(pdb),
         "--atoms-anchor", "protein", "--atoms-pull", "resname LIG"],
    )

    assert result.exit_code != 0
    assert "--atoms-anchor" in result.output
    assert "--atoms-pull" in result.output
    assert not FakeBuilder.calls


def test_topopsfgen_help_groups_options_by_env():
    result = CliRunner().invoke(topopsfgen, ["--help"])

    assert result.exit_code == 0
    for title in [
        "Common Options", "Solution per-axis padding (trigger: --env solution)",
        "Membrane Options (trigger: --env membrane)", "SMD Options (trigger: --env smd)",
    ]:
        assert title in result.output, title
