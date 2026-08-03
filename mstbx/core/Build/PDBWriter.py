from datetime import datetime
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import MDAnalysis as mda
from mstbx.core.Utils.Validator import FormatValidator
from mstbx.core.Utils.Utils import MSTBxLogger

# Try importing optional dependencies
try:
    from pdbfixer import PDBFixer
    from openmm.app import PDBFile
    PDBFIXER_AVAILABLE = True
except ImportError:
    PDBFIXER_AVAILABLE = False

class PDBWriter:
    def __init__(self, input_file=None, psf_file=None, pdb_id=None):
        """Inicializa o escritor/reparador de estruturas.

        Parameters
        ----------
        input_file : str, optional
            Estrutura local em PDB/mmCIF.
        psf_file : str, optional
            Topologia PSF usada para escrita CRD.
        pdb_id : str, optional
            Identificador RCSB PDB usado diretamente por PDBFixer.
        """
        self.input_file = input_file
        self.psf_file = psf_file
        self.pdb_id = pdb_id
        self.log_messages = []
        self.ssbonds = []
        source = input_file or f"RCSB:{pdb_id}"
        self._add_log(f"Initializing PDBWriter with file: {source}" + (f" and PSF: {psf_file}" if psf_file else ""))

    def _add_log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {message}")
        MSTBxLogger.setup_logger().info(message)

    def _validate_output(self, output_file):
        """Internal helper to validate written files."""
        valid, report = FormatValidator.validate(output_file)
        if not valid:
            self._add_log(f"WARNING: Internal validation failed for {output_file}: {report}")
        else:
            self._add_log(f"Internal validation success for {output_file}: {report}")

    def fix_structure(
        self,
        replace_nonstandard=True,
        add_missing_atoms=True,
        add_missing_residues=True,
        fix_only_internal=True,
        keep_hetatoms=False,
        add_hydrogens=False,
        select_chains=None,
        pH=7.0,
    ):
        """Repara a estrutura usando PDBFixer com política conservadora.

        Parameters
        ----------
        replace_nonstandard : bool, default=True
            Substitui resíduos não padrão reconhecidos por equivalentes padrão.
        add_missing_atoms : bool, default=True
            Preenche átomos pesados ausentes em resíduos já presentes.
        add_missing_residues : bool, default=True
            Permite reconstruir resíduos ausentes quando o gap é interno.
        fix_only_internal : bool, default=True
            Mantém apenas gaps estritamente internos. Gaps nos terminais não
            são reconstruídos.
        keep_hetatoms : bool, default=False
            Mantém HETATM não poliméricos. Por padrão remove águas, íons e
            ligandos antes do reparo.
        add_hydrogens : bool, default=False
            Adiciona hidrogênios via PDBFixer.
        select_chains : list of str, optional
            Cadeias a manter antes do reparo.
        pH : float, default=7.0
            pH usado apenas quando ``add_hydrogens`` é verdadeiro.

        Returns
        -------
        bool
            ``True`` quando a estrutura foi reparada e escrita no arquivo
            temporário interno; ``False`` quando PDBFixer/OpenMM não está
            disponível.

        Raises
        ------
        RuntimeError
            Se a estrutura não tem SEQRES e a reconstrução de gaps internos
            foi solicitada, pois PDBFixer não pode detectar gaps de forma
            confiável sem sequência de referência.
        """
        if not PDBFIXER_AVAILABLE:
            self._add_log("ERROR: PDBFixer or OpenMM not found. Skipping fixing step.")
            return False

        self._add_log("Starting PDBFixer process...")
        fixer = PDBFixer(filename=self.input_file) if self.input_file else PDBFixer(pdbid=self.pdb_id)

        if select_chains:
            present = {chain.id for chain in fixer.topology.chains()}
            requested = set(select_chains)
            missing = requested - present
            if missing:
                raise RuntimeError(f"Requested chain(s) not found: {sorted(missing)}. Present chains: {sorted(present)}")
            to_remove = present - requested
            if to_remove:
                fixer.removeChains(chainIds=list(to_remove))
                self._add_log(f"Removed chains before repair: {sorted(to_remove)}")

        if replace_nonstandard:
            fixer.findNonstandardResidues()
            self._add_log(f"Found non-standard residues: {fixer.nonstandardResidues}")
            fixer.replaceNonstandardResidues()

        removed_hetatoms = 0
        if not keep_hetatoms:
            atoms_before = sum(1 for _ in fixer.topology.atoms())
            fixer.removeHeterogens(keepWater=False)
            atoms_after = sum(1 for _ in fixer.topology.atoms())
            removed_hetatoms = atoms_before - atoms_after
            self._add_log(f"Atoms removed by PDBFixer heterogen cleanup: {removed_hetatoms}")

        if add_missing_residues:
            if not fixer.sequences:
                raise RuntimeError(
                    "No SEQRES records found. Internal gaps cannot be detected safely; "
                    "use an official RCSB PDB source or disable missing-residue repair."
                )
            fixer.findMissingResidues()
            chain_lengths = {i: len(list(chain.residues())) for i, chain in enumerate(fixer.topology.chains())}
            terminal_gaps = {
                key: value for key, value in fixer.missingResidues.items()
                if not (0 < key[1] < chain_lengths[key[0]])
            }
            if fix_only_internal:
                fixer.missingResidues = {
                    key: value for key, value in fixer.missingResidues.items()
                    if 0 < key[1] < chain_lengths[key[0]]
                }
            self._add_log(f"Internal missing residues kept: {sum(len(v) for v in fixer.missingResidues.values())}")
            if terminal_gaps:
                self._add_log(f"Terminal gaps left untouched: {terminal_gaps}")
        else:
            fixer.missingResidues = {}
        
        if add_missing_atoms:
            fixer.findMissingAtoms()
            self._add_log(f"Missing atoms found: {len(fixer.missingAtoms)} groups")
            fixer.addMissingAtoms()

        if add_hydrogens:
            fixer.addMissingHydrogens(pH=pH)
            self._add_log(f"Hydrogens added at pH {pH}")

        handle = tempfile.NamedTemporaryFile("w", suffix=".pdb", prefix="mstbx_fixed_", delete=False)
        fixed_tmp = handle.name
        with handle as f:
            PDBFile.writeFile(fixer.topology, fixer.positions, f, keepIds=True)
        
        self.input_file = fixed_tmp
        self._add_log("Structure fixed and saved to intermediate file.")
        return True

    def find_ssbonds(self, threshold=3.0):
        self._add_log(f"Searching for S-S bonds with threshold {threshold} A...")
        u = mda.Universe(self.input_file)
        cys_sg = u.select_atoms("resname CYS and name SG")
        
        found = 0
        for i, atom1 in enumerate(cys_sg):
            for atom2 in cys_sg[i+1:]:
                if atom1.residue == atom2.residue:
                    continue
                
                dist = mda.lib.distances.distance_array(atom1.position, atom2.position)[0][0]
                if dist <= threshold:
                    self.ssbonds.append((atom1, atom2, dist))
                    self._add_log(f"SSBOND found: {atom1.residue.resname} {atom1.residue.resid} ({atom1.segid}) - {atom2.residue.resname} {atom2.residue.resid} ({atom2.segid}) : {dist:.2f} A")
                    found += 1
        
        self._add_log(f"Total SSBONDs detected: {found}")
        return self.ssbonds

    def protonate(self, pH=7.0, ff="CHARMM", executable="pdb2pqr"):
        """Aplica estados de protonação e nomenclatura de um campo de força.

        Parameters
        ----------
        pH : float, default=7.0
            pH usado pelo cálculo PROPKA de estados tituláveis.
        ff : {"CHARMM", "AMBER"}, default="CHARMM"
            Campo de força de origem e esquema de nomes da estrutura escrita.
            ``CHARMM`` produz nomes como ``HSD``, ``HSE``, ``HSP``, ``ASPP``
            e ``GLUP``, compatíveis com CHARMM/NAMD e com CHARMM36 no GROMACS.
        executable : str, default="pdb2pqr"
            Executável PDB2PQR.

        Returns
        -------
        pathlib.Path
            Arquivo PDB protonado usado nas etapas seguintes.

        Raises
        ------
        RuntimeError
            Se PDB2PQR não estiver instalado ou não gerar o PDB de saída.
        """
        ff = ff.upper()
        if ff not in {"CHARMM", "AMBER"}:
            raise ValueError("ff must be CHARMM or AMBER")
        command = shutil.which(executable)
        if command is None:
            sibling = Path(sys.executable).with_name(executable)
            command = str(sibling) if sibling.is_file() else executable
        pqr = tempfile.NamedTemporaryFile(suffix=".pqr", prefix="mstbx_pdb2pqr_", delete=False)
        pdb = tempfile.NamedTemporaryFile(suffix=".pdb", prefix="mstbx_protonated_", delete=False)
        pqr.close()
        pdb.close()
        args = [
            command,
            "--ff", ff,
            "--ffout", ff,
            "--with-ph", str(pH),
            "--titration-state-method", "propka",
            "--keep-chain",
            "--pdb-output", pdb.name,
            str(self.input_file),
            pqr.name,
        ]
        self._add_log(f"Protonating at pH {pH} with {ff} nomenclature.")
        self._add_log("Running command: " + " ".join(args))
        try:
            subprocess.run(args, check=True)
        except FileNotFoundError as exc:
            raise RuntimeError(
                "PDB2PQR was not found. Install it with `pip install pdb2pqr` "
                "or use the MSTBx Conda environment."
            ) from exc
        finally:
            Path(pqr.name).unlink(missing_ok=True)
        if not Path(pdb.name).is_file() or not Path(pdb.name).stat().st_size:
            raise RuntimeError("PDB2PQR completed without producing a PDB output.")
        self.input_file = pdb.name
        self._add_log(f"Protonated PDB written with {ff} nomenclature: {pdb.name}")
        return Path(pdb.name)

    def edit_structure(self, rename_chains=None, renumber_residues=None, add_segid=None):
        u = mda.Universe(self.input_file)
        
        if rename_chains:
            self._add_log(f"Renaming chains: {rename_chains}")
            for old_id, new_id in rename_chains.items():
                u.select_atoms(f"chainID {old_id}").chainIDs = new_id

        if renumber_residues:
            start_res = renumber_residues
            self._add_log(f"Renumbering residues starting from {start_res}")
            for chain in u.segments:
                for i, res in enumerate(chain.residues):
                    res.resid = start_res + i

        if add_segid:
            self._add_log(f"Adding/Modifying segid: {add_segid}")
            segids = [value.strip() for value in str(add_segid).split(",") if value.strip()]
            if len(segids) == 1:
                u.segments.segids = segids * len(u.segments)
            elif len(segids) == len(u.segments):
                u.segments.segids = segids
            else:
                raise ValueError(
                    f"--segid received {len(segids)} values, but the structure has "
                    f"{len(u.segments)} segments. Use one value for all segments or "
                    "one comma-separated value per segment."
                )

        u.atoms.write("edited_temp.pdb")
        self.input_file = "edited_temp.pdb"
        self._add_log("Structural edits completed.")

    def select_atoms(self, selection):
        """Mantém somente os átomos de uma seleção MDAnalysis.

        Parameters
        ----------
        selection : str
            Expressão MDAnalysis, por exemplo ``"protein or resname LIG"``
            ou ``"chainID A B and not name H*"``.

        Returns
        -------
        int
            Número de átomos selecionados.

        Raises
        ------
        ValueError
            Se a expressão for inválida ou não selecionar átomos.
        """
        try:
            universe = mda.Universe(self.input_file)
            atoms = universe.select_atoms(selection)
        except Exception as exc:
            hint = " Use 'chainID' for PDB chains and 'name H*' for hydrogen names."
            raise ValueError(
                f"Invalid MDAnalysis selection: {selection!r}: {exc}.{hint}"
            ) from exc
        if not len(atoms):
            raise ValueError(f"Empty MDAnalysis selection: {selection}")
        handle = tempfile.NamedTemporaryFile("w", suffix=".pdb", prefix="mstbx_selected_", delete=False)
        selected_file = Path(handle.name)
        handle.close()
        atoms.write(selected_file)
        self.input_file = str(selected_file)
        self._add_log(f"Selected {len(atoms)} atoms with MDAnalysis: {selection}")
        return len(atoms)

    def write_final_pdb(self, output_file):
        # We read the final state and write it with SSBOND lines if any
        with open(self.input_file, 'r') as f:
            lines = f.readlines()
        
        ssbond_lines = []
        for idx, (a1, a2, d) in enumerate(self.ssbonds, 1):
            # Format: SSBOND serNum "CYS" chainID1 seqNum1 icode1 "CYS" chainID2 seqNum2 icode2 sym1 sym2 Length
            line = ("SSBOND {:3d} CYS {:1s} {:4d}    CYS {:1s} {:4d}                               "
                    "1555   1555 {:5.2f}\n").format(idx, a1.residue.segid[:1], a1.residue.resid, a2.residue.segid[:1], a2.residue.resid, d)
            ssbond_lines.append(line)
        
        # Find where to insert SSBOND (before ATOM lines)
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("ATOM") or line.startswith("HETATM"):
                insert_idx = i
                break
        
        final_lines = lines[:insert_idx] + ssbond_lines + lines[insert_idx:]
        
        with open(output_file, 'w') as f:
            f.writelines(final_lines)
        
        self._add_log(f"Final PDB written to: {output_file}")
        self._validate_output(output_file)
        self.save_log()

    def write_ext_crd(self, output_file):
        self._add_log(f"Writing extended CRD to {output_file}")
        
        if self.psf_file is None:
            u = mda.Universe(self.input_file)
        else:
            u = mda.Universe(self.psf_file, self.input_file)
            
        with open(output_file, 'w') as f:
            f.write("* GENERATED BY CHARMM-GUI FF-Converter\n")
            date_str = datetime.now().strftime("%m/%d/%y   %H:%M:%S")
            f.write(f"* DATE:   {date_str}\n")
            f.write("*\n")
            f.write(f"{u.atoms.n_atoms:10d}  EXT\n")
            
            for i, atom in enumerate(u.atoms):
                atomno = i + 1
                resno = atom.resindex + 1
                resname = atom.resname
                atomname = atom.name
                x, y, z = atom.position
                segname = (getattr(atom, "segid", "") or "PROA")[:8]
                resid = str(atom.resid)
                weight = float(getattr(atom, "mass", 0.0) or 0.0)
                
                line = "{:10d}{:10d}  {:<8s}  {:<8s}{:20.10f}{:20.10f}{:20.10f}  {:<8s}  {:<8s}{:20.10f}\n".format(
                    atomno, resno, resname, atomname, x, y, z, segname, resid, weight
                )
                f.write(line)
        
        self._add_log(f"Extended CRD written successfully to {output_file}.")
        self._validate_output(output_file)
        self.save_log()

    def save_log(self):
        with open("pdbwriter_report.log", "w") as f:
            f.write("\n".join(self.log_messages))
        MSTBxLogger.setup_logger().info("Detailed log saved to pdbwriter_report.log")
