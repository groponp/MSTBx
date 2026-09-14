"""Unit and adversarial tests for GromacsRestraints with N protein chains.

A GROMACS system split by pdb2gmx into several `topol_Protein_chain_<X>.itp`
files (one per original PDB chain letter) needs one restraint file per chain,
each with LOCAL atom numbering restarting at 1 for that chain, included into
that specific file. A single combined, globally-numbered restraint file
patched into only one chain's topology produces out-of-range atom indices in
every other chain, which grompp rejects. This was caught by an actual
`gmx grompp` run on a real two-chain system (1HSG, HIV protease dimer): see
PROJECT.md's "GROMACS Restraints and Multi-Chain Systems" section.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mstbx.core.Gromacs.Restraints import GromacsRestraints, RestraintConfig


def _gro_line(resnum: int, resname: str, atomname: str, atomnum: int, xyz: tuple[float, float, float]) -> str:
    x, y, z = xyz
    return f"{resnum:5d}{resname:<5s}{atomname:>5s}{atomnum:5d}{x:8.3f}{y:8.3f}{z:8.3f}"


def _write_system(build: Path, chains: dict[str, int]) -> None:
    """Write a minimal multi-chain protein-only system (no ligand/water)."""
    build.mkdir(parents=True, exist_ok=True)
    pdb_lines, gro_lines = [], []
    serial = 0
    for chain, count in chains.items():
        for resid in range(1, count + 1):
            serial += 1
            xyz = (float(serial), float(serial) * 2, float(serial) * 3)
            pdb_lines.append(
                f"ATOM  {serial:5d}  CA  ALA {chain}{resid:4d}    "
                f"{xyz[0]:8.3f}{xyz[1]:8.3f}{xyz[2]:8.3f}  1.00  0.00           C  "
            )
            gro_lines.append(_gro_line(resid, "ALA", "CA", serial, tuple(v / 10 for v in xyz)))
    (build / "protein.pdb").write_text("\n".join(pdb_lines) + "\nEND\n")

    total = serial
    gro = ["Test system", f"{total}"] + gro_lines + ["   5.00000   5.00000   5.00000"]
    (build / "ionized.gro").write_text("\n".join(gro) + "\n")

    for chain, count in chains.items():
        lines = ["[ moleculetype ]", f"Protein_chain_{chain}     3", "", "[ atoms ]"]
        lines += [f"{i:5d}   CT1      1    ALA      CA{i:5d}   -0.1  12.011" for i in range(1, count + 1)]
        lines += ["", f"#ifdef POSRES", f'#include "posre_Protein_chain_{chain}.itp"', "#endif", ""]
        (build / f"topol_Protein_chain_{chain}.itp").write_text("\n".join(lines))

    (build / "restraints").parent.mkdir(parents=True, exist_ok=True) if False else None


@pytest.fixture
def restraints_env(tmp_path):
    runs = tmp_path / "runs"
    build = runs / "01build"
    (runs / "restraints").mkdir(parents=True)
    return runs, build


def test_restraints_generalize_to_n_chains(restraints_env):
    """Three chains each get their own restraint file with 1-based local indices."""
    runs, build = restraints_env
    _write_system(build, {"A": 3, "B": 3, "C": 3})

    protein_count, ligand_count = GromacsRestraints(
        RestraintConfig(runs_dir=runs, selection="protein")
    ).apply_all()

    assert protein_count == 9
    assert ligand_count == 0

    for chain in ("A", "B", "C"):
        posre = build / f"posre_Protein_chain_{chain}.itp"
        assert posre.exists(), f"missing restraint file for chain {chain}"
        ids = [int(line.split()[0]) for line in posre.read_text().splitlines() if line.strip() and line.split()[0].isdigit()]
        assert ids == [1, 2, 3], f"chain {chain} local indices should restart at 1, got {ids}"

        topology = (build / f"topol_Protein_chain_{chain}.itp").read_text()
        assert f'#include "posre_Protein_chain_{chain}.itp"' in topology

        copied = runs / "restraints" / f"posre_Protein_chain_{chain}.itp"
        assert copied.exists()


def test_restraints_two_chains_do_not_cross_contaminate(restraints_env):
    """Chain B's restraint indices must not include chain A's global offset (the 1HSG bug)."""
    runs, build = restraints_env
    _write_system(build, {"A": 5, "B": 4})

    GromacsRestraints(RestraintConfig(runs_dir=runs, selection="protein")).apply_all()

    chain_a_ids = [int(line.split()[0]) for line in (build / "posre_Protein_chain_A.itp").read_text().splitlines() if line.strip() and line.split()[0].isdigit()]
    chain_b_ids = [int(line.split()[0]) for line in (build / "posre_Protein_chain_B.itp").read_text().splitlines() if line.strip() and line.split()[0].isdigit()]

    assert chain_a_ids == [1, 2, 3, 4, 5]
    assert chain_b_ids == [1, 2, 3, 4]
    assert max(chain_b_ids) <= 4, "chain B indices must be local (<=4), not global (would reach 9)"


def test_restraints_rejects_atom_outside_known_chain_windows(restraints_env):
    """A restrained atom that cannot be mapped to any chain window is a hard error, not silent."""
    runs, build = restraints_env
    _write_system(build, {"A": 3})
    # Truncate chain A's own atom count so its window no longer covers all 3 real atoms.
    itp = build / "topol_Protein_chain_A.itp"
    lines = itp.read_text().splitlines()
    atoms_idx = lines.index("[ atoms ]")
    del lines[atoms_idx + 3]  # drop the third atom entry, shrinking the declared window to 2 atoms
    itp.write_text("\n".join(lines))

    with pytest.raises(ValueError, match="outside all chain topology windows"):
        GromacsRestraints(RestraintConfig(runs_dir=runs, selection="protein")).apply_all()
