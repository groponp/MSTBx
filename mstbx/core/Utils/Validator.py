import os

class FormatValidator:
    """Validator class for molecular file formats (PDB, PSF, CRD, MOL2)."""

    @staticmethod
    def validate(filepath):
        """Detect format by extension and run the specific validation."""
        if not os.path.exists(filepath):
            return False, f"File not found: {filepath}"
        
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.pdb':
            return FormatValidator._validate_pdb(filepath)
        elif ext == '.psf':
            return FormatValidator._validate_psf(filepath)
        elif ext == '.crd':
            return FormatValidator._validate_crd(filepath)
        elif ext == '.mol2':
            return FormatValidator._validate_mol2(filepath)
        else:
            return False, f"Unsupported file extension: {ext}"

    @staticmethod
    def _validate_pdb(filepath):
        """Validate PDB format: ATOM/HETATM line length and coordinates."""
        errors = []
        has_atoms = False
        with open(filepath, 'r') as f:
            for i, line in enumerate(f):
                if line.startswith(('ATOM  ', 'HETATM')):
                    has_atoms = True
                    # Standard PDB record should be at least 54 chars long for coords
                    if len(line.rstrip('\n')) < 54:
                        errors.append(f"Line {i+1}: ATOM/HETATM record too short.")
                        continue
                    try:
                        float(line[30:38]) # X
                        float(line[38:46]) # Y
                        float(line[46:54]) # Z
                    except ValueError:
                        errors.append(f"Line {i+1}: Invalid coordinate values.")
        
        if not has_atoms:
            errors.append("No ATOM or HETATM records found.")
            
        if errors:
            return False, "; ".join(errors[:5]) + (f" (... total {len(errors)} errors)" if len(errors) > 5 else "")
        return True, "Valid PDB format."

    @staticmethod
    def _validate_psf(filepath):
        """Validate PSF format: PSF header and atom count."""
        errors = []
        has_psf_header = False
        natoms = -1
        atom_count = 0
        in_atom_section = False
        
        with open(filepath, 'r') as f:
            for i, line in enumerate(f):
                stripped = line.strip()
                if i == 0 and stripped.startswith('PSF'):
                    has_psf_header = True
                if '!NATOM' in stripped:
                    try:
                        natoms = int(stripped.split()[0])
                        in_atom_section = True
                        continue
                    except (ValueError, IndexError):
                        errors.append(f"Line {i+1}: Invalid !NATOM header.")
                
                if in_atom_section:
                    if not stripped:
                        continue
                    # Any header line starting with ! marks the end of atom section
                    if '!' in stripped:
                        in_atom_section = False
                        continue
                    atom_count += 1
        
        if not has_psf_header:
            errors.append("Missing 'PSF' header.")
        if natoms == -1:
            errors.append("Missing '!NATOM' section.")
        elif atom_count != natoms:
            errors.append(f"Atom count mismatch: expected {natoms}, found {atom_count}.")
            
        if errors:
            return False, "; ".join(errors)
        return True, "Valid PSF format."

    @staticmethod
    def _validate_crd(filepath):
        """Validate CHARMM CRD format: EXT tag, line lengths, and atom counts."""
        errors = []
        has_ext = False
        natoms = -1
        atom_count = 0
        
        with open(filepath, 'r') as f:
            for i, line in enumerate(f):
                stripped = line.strip()
                if not stripped: continue
                if stripped.startswith('*'): continue # Comment lines
                
                if 'EXT' in line:
                    has_ext = True
                    try:
                        natoms = int(stripped.split()[0])
                    except (ValueError, IndexError):
                        errors.append(f"Line {i+1}: Invalid CRD NATOM header.")
                    continue
                
                if has_ext:
                    atom_count += 1
                    # Extended CRD records are quite long (~130 chars)
                    if len(line.rstrip('\n')) < 100:
                        errors.append(f"Line {i+1}: Extended CRD record too short.")
        
        if not has_ext:
            # We only enforce EXT format for now as it is what we write
            errors.append("Missing 'EXT' tag in CRD header.")
        if natoms != -1 and atom_count != natoms:
            errors.append(f"Atom count mismatch: expected {natoms}, found {atom_count}.")
            
        if errors:
            return False, "; ".join(errors[:5]) + (f" (... total {len(errors)} errors)" if len(errors) > 5 else "")
        return True, "Valid Extended CRD format."

    @staticmethod
    def _validate_mol2(filepath):
        """Validate MOL2 sections, counts, atom records, and coordinates."""
        with open(filepath, 'r') as handle:
            lines = handle.read().splitlines()
        sections = {}
        current = None
        for line in lines:
            if line.startswith('@<TRIPOS>'):
                current = line.strip()
                sections[current] = []
            elif current:
                sections[current].append(line)

        required = ('@<TRIPOS>MOLECULE', '@<TRIPOS>ATOM', '@<TRIPOS>BOND')
        missing = [section for section in required if section not in sections]
        if missing:
            return False, "Missing MOL2 section(s): " + ", ".join(missing)

        molecule = [line.strip() for line in sections['@<TRIPOS>MOLECULE'] if line.strip()]
        if len(molecule) < 2:
            return False, "Incomplete MOL2 MOLECULE section."
        counts = molecule[1].split()
        if len(counts) < 2:
            return False, "Missing MOL2 atom/bond counts."
        try:
            atom_count, bond_count = int(counts[0]), int(counts[1])
        except ValueError:
            return False, "Invalid MOL2 atom/bond counts."
        if atom_count < 1 or bond_count < 0:
            return False, "MOL2 atom/bond counts are out of range."

        atoms = [line.split() for line in sections['@<TRIPOS>ATOM'] if line.strip()]
        bonds = [line.split() for line in sections['@<TRIPOS>BOND'] if line.strip()]
        if len(atoms) != atom_count:
            return False, f"MOL2 atom count mismatch: expected {atom_count}, found {len(atoms)}."
        if len(bonds) != bond_count:
            return False, f"MOL2 bond count mismatch: expected {bond_count}, found {len(bonds)}."
        for index, atom in enumerate(atoms, start=1):
            if len(atom) < 6:
                return False, f"MOL2 atom record {index} is incomplete."
            if atom[0] != str(index):
                return False, f"MOL2 atom numbering is invalid at record {index}."
            try:
                float(atom[2]); float(atom[3]); float(atom[4])
            except ValueError:
                return False, f"MOL2 atom record {index} has invalid coordinates."
        for index, bond in enumerate(bonds, start=1):
            if len(bond) < 4:
                return False, f"MOL2 bond record {index} is incomplete."
            try:
                int(bond[0]); atom_a = int(bond[1]); atom_b = int(bond[2])
            except ValueError:
                return False, f"MOL2 bond record {index} has invalid atom indices."
            if not (1 <= atom_a <= atom_count and 1 <= atom_b <= atom_count):
                return False, f"MOL2 bond record {index} references an unknown atom."
        return True, "Valid MOL2 format."
