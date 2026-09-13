"""Unit, regression, and adversarial tests for docking complex construction."""

from pathlib import Path

import pytest

from mstbx.core.Docking.ComplexBuilder import ComplexBuilder
from mstbx.core.Utils.Validator import FormatValidator


def _pdb(record="ATOM  ", atom="CA", resname="ALA", chain="A", resid=1):
    return f"{record}{1:5d} {atom:^4s} {resname:>3s} {chain}{resid:4d}    {1.0:8.3f}{2.0:8.3f}{3.0:8.3f}{1.00:6.2f}{20.0:6.2f}          C  \nEND\n"


def _mol2(name="LIG", atom_line="      1 C1 1.0 2.0 3.0 C.3 1 LIG 0.0"):
    return (
        f"@<TRIPOS>MOLECULE\n{name}\n 1 0 1 0 0\nSMALL\nGASTEIGER\n"
        f"@<TRIPOS>ATOM\n{atom_line}\n@<TRIPOS>BOND\n"
    )


def test_extract_pose1_isolates_the_first_docking_model(tmp_path):
    """The PDBQT parser extracts only MODEL 1, not a later docking pose."""
    source = tmp_path / "poses.pdbqt"
    output = tmp_path / "pose1.pdbqt"
    source.write_text("MODEL        1\nATOM pose-one\nENDMDL\nMODEL        2\nATOM pose-two\nENDMDL\n")

    ComplexBuilder.extract_pose1(source, output)

    assert "pose-one" in output.read_text()
    assert "pose-two" not in output.read_text()


def test_build_writes_a_valid_complex_and_checks_generated_mol2(tmp_path, monkeypatch):
    """A successful build creates a PDB and a persisted, validated ligand MOL2."""
    protein = tmp_path / "protein.pdb"
    ligand = tmp_path / "ligand.pdb"
    output = tmp_path / "nested" / "complex.pdb"
    protein.write_text(_pdb())
    ligand.write_text(_pdb("HETATM", "C1", "UNK", "X", 9))
    builder = ComplexBuilder(protein, output)

    monkeypatch.setattr(builder, "pdb_to_mol2", lambda source, destination, ph: destination.write_text(_mol2()))
    result = builder.build(ligand, is_pdbqt=False)
    assert result

    valid, report = FormatValidator.validate(output)
    assert valid, report
    assert "HETATM" in output.read_text()
    assert " LIG " in output.read_text()

    ligand_mol2 = result["ligand_mol2"]
    assert ligand_mol2 == builder.ligand_mol2_path()
    assert ligand_mol2.exists()
    mol2_valid, mol2_report = FormatValidator.validate(ligand_mol2)
    assert mol2_valid, mol2_report


def test_build_rejects_invalid_generated_mol2(tmp_path, monkeypatch):
    """A truncated converter output must stop before writing a complex."""
    protein = tmp_path / "protein.pdb"
    ligand = tmp_path / "ligand.pdb"
    output = tmp_path / "complex.pdb"
    protein.write_text(_pdb())
    ligand.write_text(_pdb("HETATM", "C1", "UNK", "X", 9))
    builder = ComplexBuilder(protein, output)
    monkeypatch.setattr(builder, "pdb_to_mol2", lambda source, destination, ph: destination.write_text("@<TRIPOS>MOLECULE\nLIG\n"))

    with pytest.raises(ValueError, match="invalid MOL2"):
        builder.build(ligand, is_pdbqt=False)
    assert not output.exists()
    assert not builder.ligand_mol2_path().exists()


def test_mol2_validator_rejects_bad_counts_and_coordinates(tmp_path):
    """MOL2 validation rejects malformed records instead of header-only files."""
    bad_counts = tmp_path / "bad_counts.mol2"
    bad_counts.write_text(_mol2().replace(" 1 0 1 0 0", " 2 0 1 0 0"))
    bad_coordinates = tmp_path / "bad_coordinates.mol2"
    bad_coordinates.write_text(_mol2(atom_line="      1 C1 no 2.0 3.0 C.3 1 LIG 0.0"))
    bad_bond = tmp_path / "bad_bond.mol2"
    bad_bond.write_text(_mol2().replace("@<TRIPOS>BOND\n", "@<TRIPOS>BOND\n      1 1 2 1\n"))

    assert FormatValidator.validate(bad_counts)[0] is False
    assert FormatValidator.validate(bad_coordinates)[0] is False
    assert FormatValidator.validate(bad_bond)[0] is False


def test_build_preserves_charmm_4letter_resnames_and_original_chain(tmp_path, monkeypatch):
    """The protein is spliced as text, never reparsed through MDAnalysis.

    pdb2pqr --ffout CHARMM writes 4-letter residue names (ASPP, GLUP, CTER,
    NTER) starting one column early, in the PDB altLoc slot. A strict
    fixed-column reader (MDAnalysis) truncates the leading letter (ASPP ->
    SPP), and re-writing that reparsed universe bakes the corruption into the
    final complex, which CHARMM-GUI then reports as an unrecognized/
    engineered residue. This also covers that a real chain ID (here "B") is
    kept instead of being forced to "A".
    """
    protein = tmp_path / "protein.pdb"
    ligand = tmp_path / "ligand.pdb"
    output = tmp_path / "complex.pdb"
    aspp_line = "ATOM      1  CB ASPP B  10      32.124  16.566  62.485  1.00  0.00           C  "
    protein.write_text(aspp_line + "\n")
    ligand.write_text(_pdb("HETATM", "C1", "UNK", "X", 9))
    builder = ComplexBuilder(protein, output)

    monkeypatch.setattr(builder, "pdb_to_mol2", lambda source, destination, ph: destination.write_text(_mol2()))
    assert builder.build(ligand, is_pdbqt=False)

    complex_text = output.read_text()
    assert aspp_line in complex_text
    assert "SPP" not in complex_text.replace(aspp_line, "")
    assert "\nTER" in complex_text or complex_text.startswith("TER")


def test_build_appends_ter_before_ligand_when_protein_lacks_one(tmp_path, monkeypatch):
    """A protein PDB without a trailing TER still gets one before the ligand."""
    protein = tmp_path / "protein.pdb"
    ligand = tmp_path / "ligand.pdb"
    output = tmp_path / "complex.pdb"
    protein.write_text(_pdb())
    ligand.write_text(_pdb("HETATM", "C1", "UNK", "X", 9))
    builder = ComplexBuilder(protein, output)

    monkeypatch.setattr(builder, "pdb_to_mol2", lambda source, destination, ph: destination.write_text(_mol2()))
    assert builder.build(ligand, is_pdbqt=False)

    lines = output.read_text().splitlines()
    ter_index = next(i for i, line in enumerate(lines) if line.startswith("TER"))
    ligand_index = next(i for i, line in enumerate(lines) if " LIG " in line)
    assert ter_index < ligand_index


def test_extract_pose1_rejects_pdbqt_without_model_one(tmp_path):
    """An empty extraction cannot silently produce a ligand-less complex."""
    source = tmp_path / "poses.pdbqt"
    output = tmp_path / "pose1.pdbqt"
    source.write_text("MODEL        2\nATOM pose-two\nENDMDL\n")

    with pytest.raises(ValueError, match="MODEL 1"):
        ComplexBuilder.extract_pose1(source, output)
