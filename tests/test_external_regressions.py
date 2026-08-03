"""Regressões que exercitam executáveis externos sem iniciar MD longa."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from mstbx.core.Build.PDBWriter import PDBWriter
from mstbx.core.Gromacs.Build import GromacsBuildConfig, GromacsBuilder
from mstbx.core.Gromacs.Index import GromacsIndex, IndexGroup, SOLUTE, SOLVENT_IONS
from mstbx.core.Gromacs.Protocol import GromacsProtocol, GromacsProtocolConfig
from mstbx.core.Gromacs.Restraints import GromacsRestraints, RestraintConfig
from mstbx.core.Gromacs.Runner import GromacsRunner
from mstbx.core.Utils.Validator import FormatValidator


ROOT = Path(__file__).resolve().parents[1]
CHIGNOLIN = ROOT / "mstbx/testing/openmm-runner/01build_folded/chignolin.pdb"
AKI = ROOT / "mstbx/testing/openmm-runner/tmp/charmm-gui-7980518961/1aki_proa.pdb"


def _executable(name: str, env_name: str) -> str | None:
    """Resolve an executable from an explicit environment override or PATH."""
    return os.environ.get(env_name) or shutil.which(name)


@pytest.mark.external
def test_pdbwriter_real_pdb2pqr_regression(tmp_path, monkeypatch):
    """PDBWriter produces valid CHARMM-named PDB output with PDB2PQR."""
    executable = _executable("pdb2pqr", "MSTBX_PDB2PQR")
    if executable is None:
        pytest.skip("pdb2pqr is not installed")
    monkeypatch.chdir(tmp_path)

    writer = PDBWriter(str(AKI))
    writer.protonate(pH=7.0, ff="CHARMM", executable=executable)
    output = tmp_path / "protonated.pdb"
    writer.write_final_pdb(output)

    valid, report = FormatValidator.validate(output)
    assert valid, report
    text = output.read_text()
    assert " HSD " in text or " HSE " in text or " HSP " in text
    assert "ATOM" in text


@pytest.mark.external
def test_gromacs_build_protocol_and_grompp_regression(tmp_path):
    """Build, restraints, index, MDPs, and all GROMACS TPR inputs compile."""
    gmx = _executable("gmx", "MSTBX_GMX")
    if gmx is None:
        pytest.skip("gmx is not installed; set MSTBX_GMX to run this regression")

    runs = tmp_path / "runs"
    GromacsBuilder(
        GromacsBuildConfig(
            protein=CHIGNOLIN,
            output_dir=runs,
            gmx=gmx,
            overwrite=True,
        )
    ).build_system()
    GromacsProtocol(GromacsProtocolConfig(runs_dir=runs, mdtime=0.004, nvt_time=0.004, npt_time=0.004)).write_all()
    GromacsIndex(
        runs,
        [
            IndexGroup("Protein_ligand", SOLUTE),
            IndexGroup("Water_and_ions", SOLVENT_IONS),
        ],
    ).write_all()
    protein_count, ligand_count = GromacsRestraints(RestraintConfig(runs)).apply_all()
    GromacsRunner(runs, gmx=gmx).write_all()

    assert protein_count > 0
    assert ligand_count == 0
    assert (runs / "run_all.sh").exists()

    build = runs / "01build"
    subprocess.run(
        [gmx, "grompp", "-f", "em.mdp", "-c", "ionized.gro", "-p", "topol.top", "-r", "ionized.gro", "-o", "em.tpr", "-maxwarn", "2"],
        cwd=build,
        check=True,
        capture_output=True,
        text=True,
    )
    for stage, name, coordinate in [
        ("02nvt", "nvt", "../01build/ionized.gro"),
        ("03npt", "npt", "../01build/ionized.gro"),
        ("04md", "md", "../01build/ionized.gro"),
    ]:
        subprocess.run(
            [gmx, "grompp", "-f", f"{name}.mdp", "-c", coordinate, "-p", "../01build/topol.top", "-r", coordinate, "-n", "../01build/index.ndx", "-o", f"{name}.tpr", "-maxwarn", "2"],
            cwd=runs / stage,
            check=True,
            capture_output=True,
            text=True,
        )
        assert (runs / stage / f"{name}.tpr").exists()
