"""Unit, regression, and adversarial tests for CGenFF Web inputs."""

from pathlib import Path

import pytest

from mstbx.core.Build.CGenFFInputs import CGenFFInputConfig, CGenFFInputPreparer


def _source_pdb(path: Path) -> None:
    """Write a minimal protein plus the 2OI0-style ligand record."""
    path.write_text(
        "ATOM      1  N   ALA A   1       1.000   2.000   3.000  1.00 20.00           N  \n"
        "ATOM      2  CA  ALA A   1       2.000   2.000   3.000  1.00 20.00           C  \n"
        "HETATM    3  C1  283 A 500       4.000   5.000   6.000  1.00 20.00           C  \n"
        "HETATM    4  O1  283 A 500       5.000   5.000   6.000  1.00 20.00           O  \n"
        "END\n"
    )


def _fake_obabel(monkeypatch):
    """Replace Open Babel with a deterministic MOL2 writer."""
    def run(command, check):
        output = Path(command[command.index("-O") + 1])
        output.write_text(
            "@<TRIPOS>MOLECULE\nLIGAND\n2 0 0 0 0\nSMALL\nNO_CHARGES\n"
            "@<TRIPOS>ATOM\n"
            "      1 C1 4.0 5.0 6.0 C.3 1 LIG 0.0\n"
            "      2 O1 5.0 5.0 6.0 O.2 1 LIG 0.0\n"
        )

    monkeypatch.setattr("mstbx.core.Build.CGenFFInputs.subprocess.run", run)


def test_cgenff_inputs_regression_generates_web_upload_files(tmp_path, monkeypatch):
    """The 2OI0-style input produces protein, ligand pose, MOL2, and log."""
    source = tmp_path / "2oi0.pdb"
    _source_pdb(source)
    _fake_obabel(monkeypatch)

    output = tmp_path / "cgenff_inputs"
    config = CGenFFInputConfig(
        output_dir=output,
        protein=source,
        select_chains="A",
        pdb_ligand_resname="283",
        pdb_ligand_chain="A",
    )
    files = CGenFFInputPreparer(config).prepare()

    assert files["protein"].read_text().count("ATOM") == 2
    assert files["ligand_pdb"].read_text().count("HETATM") == 2
    assert files["ligand_mol2"].exists()
    assert (output / "cgenff_inputs_log.json").exists()


def test_cgenff_inputs_requires_exactly_one_source(tmp_path):
    """Rejects ambiguous local-plus-RCSB sources."""
    source = tmp_path / "protein.pdb"
    source.write_text("END\n")
    config = CGenFFInputConfig(
        output_dir=tmp_path / "out",
        protein=source,
        pdb_id="2OI0",
        ligand=source,
    )

    with pytest.raises(ValueError, match="exactly one source"):
        CGenFFInputPreparer(config).prepare()


def test_cgenff_inputs_refuses_nonempty_output_without_overwrite(tmp_path):
    """Never replaces an existing CGenFF result implicitly."""
    output = tmp_path / "out"
    output.mkdir()
    (output / "ligand_for_cgenff.str").write_text("RESI OLD 0.0\n")
    source = tmp_path / "protein.pdb"
    _source_pdb(source)
    config = CGenFFInputConfig(
        output_dir=output,
        protein=source,
        pdb_ligand_resname="283",
    )

    with pytest.raises(FileExistsError, match="Use --overwrite"):
        CGenFFInputPreparer(config).prepare()


def test_cgenff_inputs_rejects_truncated_pdb_record(tmp_path, monkeypatch):
    """Reports malformed fixed-width PDB records clearly."""
    source = tmp_path / "bad.pdb"
    source.write_text("ATOM\nEND\n")
    config = CGenFFInputConfig(
        output_dir=tmp_path / "out",
        protein=source,
        pdb_ligand_resname="283",
    )
    _fake_obabel(monkeypatch)

    with pytest.raises(ValueError, match="Malformed PDB ATOM"):
        CGenFFInputPreparer(config).prepare()
