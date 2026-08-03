"""Regression tests for the reproducible GROMACS tutorials."""

from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_2oi0_tutorial_covers_manual_cgenff_web_step():
    """The ligand tutorial starts with inputs and stops for manual CGenFF."""
    script = (ROOT / "mstbx/testing/gromacs-2oi0/PrepareCGenFFInputs.sh").read_text()
    readme = (ROOT / "mstbx/testing/gromacs-2oi0/README.md").read_text()

    assert "--prepare-cgenff-inputs" in script
    assert "CGenFF Web" in readme
    assert "ligand_for_cgenff.str" in readme
    assert "Include parameters that are already in CGenFF" in readme


def test_2oi0_run_tutorial_has_single_system_order():
    """The continuation tutorial preserves topology-before-protocol order."""
    script = (ROOT / "mstbx/testing/gromacs-2oi0/RunTest.sh").read_text()

    assert script.index("topogmx") < script.index("md-inputs")
    assert "--replicas" not in script
    assert "run_all.sh" in script or "md-inputs" in script


def test_tutorials_are_shell_scripts():
    """Both executable tutorial entry points retain their bash shebang."""
    for path in [
        ROOT / "mstbx/testing/gromacs-protein/RunTest.sh",
        ROOT / "mstbx/testing/gromacs-2oi0/PrepareCGenFFInputs.sh",
        ROOT / "mstbx/testing/gromacs-2oi0/RunTest.sh",
    ]:
        assert path.read_text().startswith("#!/usr/bin/env bash")


def test_protein_tutorial_is_explicitly_ligand_free():
    """The protein tutorial documents a complete protein-only path."""
    readme = (ROOT / "mstbx/testing/gromacs-protein/README.md").read_text()
    script = (ROOT / "mstbx/testing/gromacs-protein/RunTest.sh").read_text()

    assert "protein-only" in readme
    assert "pdbwriter" in readme
    assert "--ligand" not in script
    assert "--ligand-mol2" not in script
    assert "--prepare-cgenff-inputs" not in script
    assert '--select-group-index-1 "protein"' in script
    assert '--select-group-index-2 "not protein"' in script
    assert '--select-atoms-to-restraint "protein and backbone"' in script


def test_main_readme_has_clickable_gromacs_tutorials_seven_and_eight():
    """The main tutorial index exposes separate protein and ligand links."""
    readme = (ROOT / "README.md").read_text()

    assert "[7. GROMACS Protein-Only](#7-gromacs-protein-only)" in readme
    assert "[8. GROMACS Protein-Ligand with CGenFF](#8-gromacs-protein-ligand-with-cgenff)" in readme
    assert "### 7. GROMACS Protein-Only" in readme
    assert "### 8. GROMACS Protein-Ligand with CGenFF" in readme
    assert readme.index("### 7. GROMACS Protein-Only") < readme.index("### 8. GROMACS Protein-Ligand with CGenFF")


def test_main_readme_has_complete_pdbwriter_tutorial():
    """Tutorial 0 exposes every PDBWriter option family explicitly."""
    readme = (ROOT / "README.md").read_text()
    start = readme.index("### 0. PDBWriter Structure Preparation")
    end = readme.index("### 1. Ubiquitin in Solution")
    tutorial = readme[start:end]

    for option in [
        "--input", "--output", "--pdb-id", "--select-chains", "--fix-structure",
        "--fix-keep-hetatoms", "--fix-add-hydrogens", "--internal-only", "--pH",
        "--ff-out", "--ssbond", "--rename-chain", "--renumber", "--segid",
        "--write-ext-crd", "--check-mol-format", "--mol", "--prepare-cgenff-inputs",
        "--ligand", "--pdb-ligand-resname", "--pdb-ligand-chain", "--ligand-pH",
        "--overwrite",
    ]:
        assert option in tutorial, option


def test_cgenff_tutorial_delegates_rcsb_download_to_pdbwriter():
    """CGenFF preparation uses pdbwriter's --pdb-id download path once."""
    readme = (ROOT / "mstbx/testing/gromacs-2oi0/README.md").read_text()
    script = (ROOT / "mstbx/testing/gromacs-2oi0/PrepareCGenFFInputs.sh").read_text()

    assert "--pdb-id 2OI0" in readme
    assert "--pdb-id 2OI0" in script
    assert "curl -L" not in readme
    assert "curl -L" not in script


def test_tutorials_document_missing_atom_repair_without_hydrogen_duplication():
    """Tutorials explain heavy-atom repair and preserve ligand HETATM records."""
    protein = (ROOT / "mstbx/testing/gromacs-protein/README.md").read_text()
    ligand = (ROOT / "mstbx/testing/gromacs-2oi0/README.md").read_text()
    main = (ROOT / "README.md").read_text()

    assert "--fix-structure" in protein
    assert "Do not add hydrogens" in protein
    assert "--fix-keep-hetatoms" in ligand
    assert "--fix-add-hydrogens" in main
    assert "pdb2gmx" in main
    assert "--pdb2gmx-protonation" in protein
    assert "Interactive protonation" in protein
    assert "--pdb2gmx-protonation" in main


def test_docking_tutorial_covers_pose_sources_and_engine_boundaries():
    """The docking tutorial covers PDBQT, PDB, PDBWriter, GROMACS, and NAMD."""
    readme = (ROOT / "mstbx/testing/mkdocking/README.md").read_text()
    main = (ROOT / "README.md").read_text()

    for option in ["--dock", "--ligand-pdb", "--select-atoms", "--ssbond", "--segid", "--pH"]:
        assert option in readme
    assert "MODEL 1" in readme
    assert "topogmx" in readme
    assert "topopsfgen" in readme
    assert "## Choose the matching case" in readme
    assert "Case Study 1: Receptor Preparation" in readme
    assert "--select-group-index-1" in readme
    assert "--input-dir" not in readme
    assert "### 9. Docking Pose to a Protein-Ligand System" in main
    assert "mstbx/testing/mkdocking/README.md" in main
