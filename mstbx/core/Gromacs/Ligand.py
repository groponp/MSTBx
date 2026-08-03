"""Utilidades para ligandos CGenFF em sistemas GROMACS."""

from __future__ import annotations

from pathlib import Path


def cgenff_resi_name(str_file: Path) -> str:
    """Extrai o nome ``RESI`` de um arquivo CGenFF.

    Parameters
    ----------
    str_file
        Arquivo ``.str`` baixado do CGenFF.
    """
    for line in str_file.read_text().splitlines():
        if line.startswith("RESI "):
            return line.split()[1]
    raise ValueError(f"Could not find RESI in {str_file}")


def molecule_type(itp: Path) -> str:
    """Extrai o nome de ``[ moleculetype ]`` de um ITP."""
    active = False
    for line in itp.read_text().splitlines():
        text = line.strip()
        if text.startswith("["):
            active = text.strip("[] ").lower() == "moleculetype"
        elif active and text and not text.startswith(";"):
            return text.split()[0]
    raise ValueError(f"Could not find moleculetype in {itp}")


def normalize_mol2_name(mol2: Path, name: str) -> None:
    """Sincroniza o nome da molécula e resíduo do MOL2 com o CGenFF."""
    lines = mol2.read_text().splitlines()
    marker = next(i for i, line in enumerate(lines) if line.strip().upper() == "@<TRIPOS>MOLECULE")
    lines[marker + 1] = name
    in_atoms = False
    for i, line in enumerate(lines):
        if line.startswith("@<TRIPOS>"):
            in_atoms = line.strip().upper() == "@<TRIPOS>ATOM"
        elif in_atoms and line.strip():
            parts = line.split()
            if len(parts) >= 8:
                parts[7] = name
                lines[i] = "{:>7s} {:<4s} {:>10s} {:>10s} {:>10s} {:<6s} {:>4s} {:<8s} {:>10s}".format(*parts[:9])
    mol2.write_text("\n".join(lines) + "\n")


def set_ligand_resname(itp: Path, resname: str) -> None:
    """Reescreve o resname do ligando na seção ``[ atoms ]``."""
    section, out = "", []
    for line in itp.read_text().splitlines():
        text = line.strip()
        if text.startswith("["):
            section = text.strip("[] ").lower()
        if section == "atoms" and text and not text.startswith(";"):
            body, sep, comment = line.partition(";")
            parts = body.split()
            if len(parts) >= 5:
                parts[3] = resname
                line = " ".join(parts) + (f" ;{comment}" if sep else "")
        out.append(line)
    itp.write_text("\n".join(out) + "\n")


def write_ligand_pdb(src: Path, dst: Path, resname: str) -> None:
    """Converte a pose inicial do conversor CGenFF para PDB simples."""
    lines = []
    atoms = (line for line in src.read_text().splitlines() if line.startswith(("ATOM", "HETATM")))
    for serial, line in enumerate(atoms, 1):
        parts = line.split()
        atom, x, y, z = parts[2], *map(float, parts[5:8])
        element = "".join(c for c in atom if c.isalpha())[:1]
        lines.append(f"HETATM{serial:5d} {atom:>4s} {resname:>3s} L{1:4d}    {x:8.3f}{y:8.3f}{z:8.3f}{1:6.2f}{0:6.2f}          {element:>2s}")
    dst.write_text("\n".join(lines) + "\nTER\nEND\n")
