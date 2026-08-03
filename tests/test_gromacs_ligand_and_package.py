"""Testes de ligando CGenFF e empacotamento."""

from pathlib import Path

from mstbx.core.Gromacs.Build import DEFAULT_CGENFF_CONVERTER, DEFAULT_FORCEFIELD_DIR
from mstbx.core.Gromacs.Ligand import cgenff_resi_name, molecule_type, set_ligand_resname


def test_default_forcefield_and_converter_are_packaged():
    """Garante que a instalação fornece os defaults GROMACS."""
    assert DEFAULT_FORCEFIELD_DIR.exists()
    assert (DEFAULT_FORCEFIELD_DIR / "forcefield.itp").exists()
    assert DEFAULT_CGENFF_CONVERTER.exists()


def test_shared_charmm_toppar_is_present_for_installed_package():
    """The wheel must retain shared CHARMM parameters used by NAMD workflows."""
    toppar = Path(__file__).parents[1] / "mstbx/core/toppar"
    assert (toppar / "par_all36m_prot.prm").exists()
    assert (toppar / "toppar_water_ions.str").exists()


def test_cgenff_resi_and_moleculetype_parsing(tmp_path):
    """Extrai nomes internos sem exigir argumentos manuais redundantes."""
    str_file = tmp_path / "ligand.str"
    itp_file = tmp_path / "ligand.itp"
    str_file.write_text("* test\nRESI C123 0.000\n")
    itp_file.write_text("[ moleculetype ]\n; name nrexcl\nC123 3\n")

    assert cgenff_resi_name(str_file) == "C123"
    assert molecule_type(itp_file) == "C123"


def test_set_ligand_resname_updates_atoms_section_only(tmp_path):
    """Troca resname no ITP mantendo outras seções intactas."""
    itp = tmp_path / "ligand.itp"
    itp.write_text(
        "[ atoms ]\n"
        "1 CG2R61 1 C123 C1 1 0.0 12.0 ; comment\n"
        "\n[ bonds ]\n"
        "1 2 1\n"
    )

    set_ligand_resname(itp, "LIG")

    text = itp.read_text()
    assert "1 CG2R61 1 LIG C1 1 0.0 12.0 ; comment" in text
    assert "[ bonds ]\n1 2 1" in text


def test_cgenff_resi_missing_is_adversarial_error(tmp_path):
    """Falha explicitamente quando o STR não contém ``RESI``."""
    str_file = tmp_path / "bad.str"
    str_file.write_text("* no residue here\n")

    try:
        cgenff_resi_name(str_file)
    except ValueError as exc:
        assert "Could not find RESI" in str(exc)
    else:
        raise AssertionError("missing RESI should fail")
