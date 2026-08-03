"""Testes unitários do protocolo GROMACS."""

from mstbx.core.Gromacs.Protocol import GromacsProtocol, GromacsProtocolConfig
from mstbx.core.Gromacs.Runner import GromacsRunner


def test_protocol_uses_mstbx_stage_layout(tmp_path):
    """Gera MDPs em ``01build``, ``02nvt``, ``03npt`` e ``04md``."""
    config = GromacsProtocolConfig(
        runs_dir=tmp_path / "runs",
        temperature=310.0,
        mdtime=1.0,
        xtc_frequency=50.0,
    )

    written = GromacsProtocol(config).write_all()

    assert len(written) == 4
    assert (tmp_path / "runs/01build/em.mdp").exists()
    assert (tmp_path / "runs/02nvt/nvt.mdp").exists()
    assert (tmp_path / "runs/03npt/npt.mdp").exists()
    assert (tmp_path / "runs/04md/md.mdp").exists()
    assert not (tmp_path / "runs/02em").exists()


def test_protocol_regression_defaults(tmp_path):
    """Protege tempos em ns no esquema NAMD solution."""
    config = GromacsProtocolConfig(runs_dir=tmp_path / "runs", mdtime=1.0)

    GromacsProtocol(config).write_all()

    em = (tmp_path / "runs/01build/em.mdp").read_text()
    nvt = (tmp_path / "runs/02nvt/nvt.mdp").read_text()
    npt = (tmp_path / "runs/03npt/npt.mdp").read_text()
    md = (tmp_path / "runs/04md/md.mdp").read_text()
    assert "nsteps = 50000" in em
    assert "dt = 0.002" in nvt
    assert "nsteps = 1000000" in nvt
    assert "nsteps = 2500000" in npt
    assert "nstxout-compressed = 25000" in nvt
    assert "tc_grps = Protein_ligand Water_and_ions" in nvt
    assert "nsteps = 500000" in md


def test_protocol_accepts_custom_equilibration_times(tmp_path):
    """Converte tempos customizados de NVT/NPT em ns para passos."""
    config = GromacsProtocolConfig(
        runs_dir=tmp_path / "runs",
        mdtime=1.0,
        nvt_time=0.5,
        npt_time=1.5,
    )

    GromacsProtocol(config).write_all()

    assert "nsteps = 250000" in (tmp_path / "runs/02nvt/nvt.mdp").read_text()
    assert "nsteps = 750000" in (tmp_path / "runs/03npt/npt.mdp").read_text()


def test_runner_writes_all_stages_and_gpu_safe_defaults(tmp_path):
    """Confirma ordem EM->NVT->NPT->MD e fallback seguro de GPU update."""
    root = tmp_path / "runs"

    [script] = GromacsRunner(root, gmx="gmx").write_all()

    text = script.read_text()
    assert "MDRUN_FLAGS=\"${MDRUN_FLAGS:--update cpu -pin on}\"" in text
    assert "run_stage 01build em" in text
    assert "run_stage 02nvt nvt" in text
    assert "run_stage 03npt npt" in text
    assert "run_stage 04md md" in text
    assert script.stat().st_mode & 0o111
