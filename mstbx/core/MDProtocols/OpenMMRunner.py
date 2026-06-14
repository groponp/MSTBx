#!/usr/bin/env python3
"""
Chef component of the OpenMM Runner integration in MSTBx.
Consolidates simulation logic and OpenMM/CHARMM-GUI setup.
"""

import sys
import os
import shutil
import glob
import datetime
import warnings
import logging
from math import *

# ==============================================================================
# Classes and Utility Functions
# ==============================================================================

class FlushFile(object):
    def __init__(self, fd):
        self.fd = fd
    def write(self, x):
        self.fd.write(x)
        self.fd.flush()
    def flush(self):
        self.fd.flush()
    def getattr(self, name):
        return getattr(self.fd, name)

sys.stdout = FlushFile(sys.stdout)

# Setup a local warnings.log
logging.basicConfig(filename='warnings.log', level=logging.WARNING, 
                    format='[%(asctime)s] %(message)s', datefmt='%H:%M:%S %d/%m/%Y')

def warn_with_logging(message, category, filename, lineno, file=None, line=None):
    logging.warning(f"{filename}:{lineno}: {category.__name__}: {message}")

warnings.showwarning = warn_with_logging

try:
    import MDAnalysis as mda
except ImportError:
    mda = None

# Attempt to load openmm libraries
try:
    from openmm import *
    from openmm.app import *
    from openmm.unit import *
except ImportError:
    pass

try:
    from mdtraj.reporters import XTCReporter
except ImportError:
    XTCReporter = None

def log_message(level, message, debug_mode=False):
    if level == "DEBUG" and not debug_mode:
        return
    now = datetime.datetime.now()
    timestamp = now.strftime("%H:%M:%S %d/%m/%Y")
    print(f"[{level} {timestamp}] {message}", flush=True)

# ==============================================================================
# Input Reading
# ==============================================================================

class OpenMMReadInputs():
    def __init__(self):
        self.mini_nstep       = 0
        self.mini_tol         = 1.0
        self.gen_vel          = 'no'
        self.gen_temp         = 300.0
        self.gen_seed         = None
        self.nstep            = 0
        self.dt               = 0.002
        self.nstout           = 100
        self.nstdcd           = 0
        self.coulomb          = None  # Will be set to PME after openmm is imported
        self.ewald_Tol        = 0.0005
        self.vdw              = 'Force-switch'
        self.r_on             = 1.0
        self.r_off            = 1.2
        self.lj_lrc           = 'no'
        self.e14scale         = 1.0
        self.temp             = 300.0
        self.fric_coeff       = 1
        self.integrator       = 'Langevin'
        self.pcouple          = 'no'
        self.p_ref            = 1.0
        self.p_type           = 'isotropic'
        self.p_scale          = True, True, True
        self.p_XYMode         = None
        self.p_ZMode          = None
        self.p_tens           = 0.0
        self.p_freq           = 25
        self.cons             = None
        self.rest             = 'no'
        self.fc_bb            = 0.0
        self.fc_sc            = 0.0
        self.fc_mpos          = 0.0
        self.fc_lpos          = 0.0
        self.fc_hmmm          = 0.0
        self.fc_dcle          = 0.0
        self.fc_ldih          = 0.0
        self.fc_cdih          = 0.0
        self.fbres_rfb        = 1.0
        
        # Extension for custom MDAnalysis selection
        self.rest_atom        = None
        self.rest_k           = 0.0

    def init_openmm_defaults(self):
        try:
            self.coulomb = PME
            self.p_XYMode = MonteCarloMembraneBarostat.XYIsotropic
            self.p_ZMode = MonteCarloMembraneBarostat.ZFree
            self.cons = HBonds
        except NameError:
            pass

    def read(self, inputFile):
        self.init_openmm_defaults()
        if not os.path.exists(inputFile):
            return self
        for line in open(inputFile, 'r'):
            if line.find('#') >= 0: line = line.split('#')[0]
            line = line.strip()
            if len(line) > 0:
                segments = line.split('=')
                input_param = segments[0].upper().strip()
                try:    input_value = segments[1].strip()
                except: input_value = None
                if input_value:
                    if input_param == 'MINI_NSTEP':                     self.mini_nstep       = int(input_value)
                    if input_param == 'MINI_TOL':                       self.mini_tol         = float(input_value)
                    if input_param == 'GEN_VEL':
                        if input_value.upper() == 'YES':                self.gen_vel          = 'yes'
                        if input_value.upper() == 'NO':                 self.gen_vel          = 'no'
                    if input_param == 'GEN_TEMP':                       self.gen_temp         = float(input_value)
                    if input_param == 'GEN_SEED':                       self.gen_seed         = int(input_value)
                    if input_param == 'NSTEP':                          self.nstep            = int(input_value)
                    if input_param == 'DT':                             self.dt               = float(input_value)
                    if input_param == 'NSTOUT':                         self.nstout           = int(input_value)
                    if input_param == 'NSTDCD':                         self.nstdcd           = int(input_value)
                    if input_param == 'COULOMB':
                        try:
                            if input_value.upper() == 'NOCUTOFF':           self.coulomb          = NoCutoff
                            if input_value.upper() == 'CUTOFFNONPERIODIC':  self.coulomb          = CutoffNonPeriodic
                            if input_value.upper() == 'CUTOFFPERIODIC':     self.coulomb          = CutoffPeriodic
                            if input_value.upper() == 'EWALD':              self.coulomb          = Ewald
                            if input_value.upper() == 'PME':                self.coulomb          = PME
                        except NameError:
                            self.coulomb = input_value
                    if input_param == 'EWALD_TOL':                      self.ewald_Tol        = float(input_value)
                    if input_param == 'VDW':
                        if input_value.upper() == 'NOCUTOFF':           self.vdw              = 'NoCutoff'
                        if input_value.upper() == 'CUTOFFPERIODIC':     self.vdw              = 'CutoffPeriodic'
                        if input_value.upper() == 'FORCE-SWITCH':       self.vdw              = 'Force-switch'
                        if input_value.upper() == 'SWITCH':             self.vdw              = 'Switch'
                        if input_value.upper() == 'LJPME':              self.vdw              = 'LJPME'
                    if input_param == 'R_ON':                           self.r_on             = float(input_value)
                    if input_param == 'R_OFF':                          self.r_off            = float(input_value)
                    if input_param == 'LJ_LRC':
                        if input_value.upper() == 'YES':                self.lj_lrc           = 'yes'
                        if input_value.upper() == 'NO':                 self.lj_lrc           = 'no'
                    if input_param == 'E14SCALE':                       self.e14scale         = float(input_value)
                    if input_param == 'TEMP':                           self.temp             = float(input_value)
                    if input_param == 'FRIC_COEFF':                     self.fric_coeff       = float(input_value)
                    if input_param == 'INTEGRATOR':
                        if input_value.upper() == 'LANGEVIN':           self.integrator       = 'Langevin'
                        if input_value.upper() == 'LANGEVINMIDDLE':     self.integrator       = 'LangevinMiddle'
                    if input_param == 'PCOUPLE':
                        if input_value.upper() == 'YES':                self.pcouple          = 'yes'
                        if input_value.upper() == 'NO':                 self.pcouple          = 'no'
                    if input_param == 'P_REF':
                        if input_value.find(',') < 0:
                            self.p_ref = float(input_value)
                        else:
                            Pxx = float(input_value.split(',')[0])
                            Pyy = float(input_value.split(',')[1])
                            Pzz = float(input_value.split(',')[2])
                            self.p_ref = Pxx, Pyy, Pzz
                    if input_param == 'P_TYPE':
                        if input_value.upper() == 'ISOTROPIC':          self.p_type           = 'isotropic'
                        if input_value.upper() == 'MEMBRANE':           self.p_type           = 'membrane'
                        if input_value.upper() == 'ANISOTROPIC':        self.p_type           = 'anisotropic'
                    if input_param == 'P_SCALE':
                        scaleX = True; scaleY = True; scaleZ = True
                        if input_value.upper().find('X') < 0: scaleX = False
                        if input_value.upper().find('Y') < 0: scaleY = False
                        if input_value.upper().find('Z') < 0: scaleZ = False
                        self.p_scale = scaleX, scaleY, scaleZ
                    if input_param == 'P_XYMODE':
                        try:
                            if input_value.upper() == 'XYISOTROPIC':        self.p_XYMode         = MonteCarloMembraneBarostat.XYIsotropic
                            if input_value.upper() == 'XYANISOTROPIC':      self.p_XYMode         = MonteCarloMembraneBarostat.XYAnisotropic
                        except NameError:
                            self.p_XYMode = input_value
                    if input_param == 'P_ZMODE':
                        try:
                            if input_value.upper() == 'ZFREE':              self.p_ZMode          = MonteCarloMembraneBarostat.ZFree
                            if input_value.upper() == 'ZFIXED':             self.p_ZMode          = MonteCarloMembraneBarostat.ZFixed
                            if input_value.upper() == 'CONSTANTVOLUME':     self.p_ZMode          = MonteCarloMembraneBarostat.ConstantVolume
                        except NameError:
                            self.p_ZMode = input_value
                    if input_param == 'P_TENS':                         self.p_tens           = float(input_value)
                    if input_param == 'P_FREQ':                         self.p_freq           = int(input_value)
                    if input_param == 'CONS':
                        try:
                            if input_value.upper() == 'NONE':               self.cons             = None
                            if input_value.upper() == 'HBONDS':             self.cons             = HBonds
                            if input_value.upper() == 'ALLBONDS':           self.cons             = AllBonds
                            if input_value.upper() == 'HANGLES':            self.cons             = HAngles
                        except NameError:
                            self.cons = input_value
                    if input_param == 'REST':
                        if input_value.upper() == 'YES':                self.rest             = 'yes'
                        if input_value.upper() == 'NO':                 self.rest             = 'no'
                    if input_param == 'FC_BB':                          self.fc_bb            = float(input_value)
                    if input_param == 'FC_SC':                          self.fc_sc            = float(input_value)
                    if input_param == 'FC_MPOS':                        self.fc_mpos          = float(input_value)
                    if input_param == 'FC_LPOS':                        self.fc_lpos          = float(input_value)
                    if input_param == 'FC_HMMM':                        self.fc_hmmm          = float(input_value)
                    if input_param == 'FC_DCLE':                        self.fc_dcle          = float(input_value)
                    if input_param == 'FC_LDIH':                        self.fc_ldih          = float(input_value)
                    if input_param == 'FC_CDIH':                        self.fc_cdih          = float(input_value)
                    if input_param == 'FBRES_RFB':                      self.fbres_rfb        = float(input_value)
                    
                    if input_param == 'REST_ATOM':      self.rest_atom = input_value.strip('"').strip("'")
                    if input_param == 'REST_K':         self.rest_k = float(input_value)
        return self

def read_inputs(inputFile):
    return OpenMMReadInputs().read(inputFile)

# ==============================================================================
# Force Fields and System Setup
# ==============================================================================

def vfswitch(system, psf, inputs):
    """ Correct implementation of CHARMM Force-switch with NBFIX support """
    r_on = inputs.r_on
    r_off = inputs.r_off

    # Check for NBFIX (Special CHARMM term)
    chknbfix = False
    for force in system.getForces():
        if isinstance(force, NonbondedForce):
            nonbonded = force
        if isinstance(force, CustomNonbondedForce) and force.getNumTabulatedFunctions() == 2:
            nbfix     = force
            chknbfix  = True

    if not chknbfix:
        # standard vfswitch
        vfswitch_force = CustomNonbondedForce('select(step(r-Ron),(cr12*rjunk12 - cr6*rjunk6),'
                                              '(ccnba/r^12-ccnbb/r^6-ccnba/onoff^6+ccnbb/onoff^3));'
                                              'cr12 = ccnba*ofdif6; cr6 = ccnbb*ofdif3;'
                                              'rjunk12 = (1.0/r^6-1.0/Roff6)^2; rjunk6 = (1.0/r^3-1.0/Roff3)^2;'
                                              'ccnba = 4.0*epsilon*sigma^12; ccnbb = 4.0*epsilon*sigma^6;'
                                              'sigma = sigma1+sigma2; epsilon = epsilon1*epsilon2;'
                                              'ofdif6 = Roff6/(Roff6 - Ron^6); ofdif3 = Roff3/(Roff3 - Ron^3);'
                                              'onoff = Roff * Ron; Roff6 = Roff^6; Roff3 = Roff^3;'
                                              'Ron = %f; Roff = %f;' % (r_on, r_off))
        vfswitch_force.addPerParticleParameter('sigma')
        vfswitch_force.addPerParticleParameter('epsilon')
        vfswitch_force.setNonbondedMethod(vfswitch_force.CutoffPeriodic)
        vfswitch_force.setCutoffDistance(nonbonded.getCutoffDistance())
        for i in range(nonbonded.getNumParticles()):
            chg, sig, eps = nonbonded.getParticleParameters(i)
            nonbonded.setParticleParameters(i, chg, 0.0, 0.0) # Zero out LJ in original NonbondedForce
            vfswitch_force.addParticle([sig*0.5, eps**0.5])
        for i in range(nonbonded.getNumExceptions()):
            atom1, atom2 = nonbonded.getExceptionParameters(i)[:2]
            vfswitch_force.addExclusion(atom1, atom2)
        
        # Set Force Group to synchronize with NonbondedForce
        if hasattr(psf, 'NONBONDED_FORCE_GROUP'):
            vfswitch_force.setForceGroup(psf.NONBONDED_FORCE_GROUP)
            
        system.addForce(vfswitch_force)
    else:
        # vfswitch with NBFIX support
        nbfix.setEnergyFunction('select(step(r-Ron),(cr12*rjunk12 - cr6*rjunk6),'
                                '(ccnba/r^12-ccnbb/r^6-ccnba/onoff^6+ccnbb/onoff^3));'
                                'cr12 = ccnba*ofdif6; cr6  = ccnbb*ofdif3;'
                                'rjunk12 = (1.0/r^6-1.0/Roff6)^2; rjunk6 = (1.0/r^3-1.0/Roff3)^2;'
                                'ccnbb = bcoef(type1, type2); ccnba = acoef(type1, type2)^2;'
                                'ofdif6 = Roff6/(Roff6 - Ron^6); ofdif3 = Roff3/(Roff3 - Ron^3);'
                                'onoff = Roff * Ron; Roff6 = Roff^6; Roff3 = Roff^3;'
                                'Ron  = %f; Roff = %f;' % (r_on, r_off))
        nbfix.setUseLongRangeCorrection(False) # As per CHARMM-GUI issues #2353

    # Add 1-4 scaling support (vfswitch14)
    vfswitch14 = CustomBondForce('select(step(r-Ron),(cr12*rjunk12 - cr6*rjunk6),'
                                 '(ccnba/r^12-ccnbb/r^6-ccnba/onoff^6+ccnbb/onoff^3));'
                                 'cr12 = ccnba*ofdif6; cr6 = ccnbb*ofdif3;'
                                 'rjunk12 = (1.0/r^6-1.0/Roff6)^2; rjunk6 = (1.0/r^3-1.0/Roff3)^2;'
                                 'ccnba = 4.0*epsilon*sigma^12; ccnbb = 4.0*epsilon*sigma^6;'
                                 'ofdif6 = Roff6/(Roff6 - Ron^6); ofdif3 = Roff3/(Roff3 - Ron^3);'
                                 'onoff = Roff * Ron; Roff6 = Roff^6; Roff3 = Roff^3;'
                                 'Ron = %f; Roff = %f;' % (r_on, r_off))
    vfswitch14.addPerBondParameter('sigma')
    vfswitch14.addPerBondParameter('epsilon')
    for i in range(nonbonded.getNumExceptions()):
        atom1, atom2, chg, sig, eps = nonbonded.getExceptionParameters(i)
        nonbonded.setExceptionParameters(i, atom1, atom2, chg, 0.0, 0.0) # Zero out LJ14
        vfswitch14.addBond(atom1, atom2, [sig, eps])
    system.addForce(vfswitch14)
    return system

def barostat(system, inputs):
    if inputs.p_type == 'isotropic':
        baro = MonteCarloBarostat( inputs.p_ref*bar, inputs.temp*kelvin, inputs.p_freq )
    elif inputs.p_type == 'membrane':
        p_tens_conv = inputs.p_tens*10.0
        baro = MonteCarloMembraneBarostat( inputs.p_ref*bar, p_tens_conv*bar*nanometers, inputs.temp*kelvin, inputs.p_XYMode, inputs.p_ZMode, inputs.p_freq )
    elif inputs.p_type == 'anisotropic':
        baro = MonteCarloAnisotropicBarostat( inputs.p_ref*bar, inputs.temp*kelvin, inputs.p_scale[0], inputs.p_scale[1], inputs.p_scale[2], inputs.p_freq )
    system.addForce(baro)
    return system

def restraints(system, crd, inputs):
    """ Strict CHARMM-GUI restraint logic """
    if inputs.fc_bb > 0 or inputs.fc_sc > 0:
        posresPROT = CustomExternalForce('k*periodicdistance(x, y, z, x0, y0, z0)^2;')
        posresPROT.addPerParticleParameter('k'); posresPROT.addPerParticleParameter('x0'); posresPROT.addPerParticleParameter('y0'); posresPROT.addPerParticleParameter('z0')
        count = 0
        if os.path.exists('restraints/prot_pos.txt'):
            for line in open('restraints/prot_pos.txt', 'r'):
                segments = line.strip().split()
                atom1 = int(segments[0]); state = segments[1]
                xpos, ypos, zpos = crd.positions[atom1].value_in_unit(nanometers)
                if state == 'BB' and inputs.fc_bb > 0: 
                    posresPROT.addParticle(atom1, [inputs.fc_bb, xpos, ypos, zpos]); count += 1
                if state == 'SC' and inputs.fc_sc > 0: 
                    posresPROT.addParticle(atom1, [inputs.fc_sc, xpos, ypos, zpos]); count += 1
            system.addForce(posresPROT)
            log_message("INFO", f"Applied CHARMM-GUI positional restraints: {count} protein atoms.")
    
    if inputs.fc_lpos > 0:
        posresMEMB = CustomExternalForce('k*periodicdistance(0, 0, z, 0, 0, z0)^2;')
        posresMEMB.addGlobalParameter('k', inputs.fc_lpos); posresMEMB.addPerParticleParameter('z0')
        if os.path.exists('restraints/lipid_pos.txt'):
            for line in open('restraints/lipid_pos.txt', 'r'):
                segments = line.strip().split(); atom1 = int(segments[0])
                zpos  = crd.positions[atom1].value_in_unit(nanometers)[2]
                posresMEMB.addParticle(atom1, [zpos])
            system.addForce(posresMEMB)
    return system

def apply_mdanalysis_restraints(system, psf_path, pdb_path, inputs, debug_mode=False):
    """ Strict CHARMM-GUI logic applied to custom MDAnalysis selection """
    if not inputs.rest_atom or inputs.rest_k <= 0 or mda is None:
        return system
    u = mda.Universe(psf_path, pdb_path)
    selection = u.select_atoms(inputs.rest_atom)
    if len(selection) == 0:
        log_message("ERROR", f"Selection '{inputs.rest_atom}' matched ZERO atoms!")
        return system
        
    # Formula k*r^2 (Strict CHARMM-GUI)
    force = CustomExternalForce("k*periodicdistance(x, y, z, x0, y0, z0)^2")
    force.addGlobalParameter("k", inputs.rest_k * kilojoules_per_mole/nanometer**2)
    force.addPerParticleParameter("x0"); force.addPerParticleParameter("y0"); force.addPerParticleParameter("z0")
    for atom in selection:
        pos = atom.position / 10.0
        force.addParticle(int(atom.index), pos)
    system.addForce(force)
    log_message("INFO", f"Applied strict restraints (k*r^2) to {len(selection)} atoms with k={inputs.rest_k} kJ/mol/nm^2")
    return system

def rewrap(simulation):
    """ VERBATIM Original CHARMM-GUI omm_rewrap.py logic """
    bonds = simulation.topology.bonds()
    positions = simulation.context.getState(getPositions=True).getPositions()
    box = simulation.context.getState().getPeriodicBoxVectors()
    boxlx = box[0][0]/angstrom
    boxly = box[1][1]/angstrom
    boxlz = box[2][2]/angstrom

    min_crds = [positions[0][0]/angstrom, positions[0][1]/angstrom, positions[0][2]/angstrom]
    max_crds = [positions[0][0]/angstrom, positions[0][1]/angstrom, positions[0][2]/angstrom]

    for position in positions:
        min_crds[0] = min(min_crds[0], position[0]/angstrom)
        min_crds[1] = min(min_crds[1], position[1]/angstrom)
        min_crds[2] = min(min_crds[2], position[2]/angstrom)
        max_crds[0] = max(max_crds[0], position[0]/angstrom)
        max_crds[1] = max(max_crds[1], position[1]/angstrom)
        max_crds[2] = max(max_crds[2], position[2]/angstrom)

    xcen = (max_crds[0] + min_crds[0]) / 2.0
    ycen = (max_crds[1] + min_crds[1]) / 2.0
    zcen = (max_crds[2] + min_crds[2]) / 2.0

    for bond in bonds:
        atom1 = bond[0]
        atom2 = bond[1]
        atom1id = atom1.index
        atom2id = atom2.index
        res1 = atom1.residue
        res2 = bond[1].residue # Safe fallback for bond structures

        x1, y1, z1 = positions[atom1id]
        x2, y2, z2 = positions[atom2id]
        dx = fabs(x1/angstrom - x2/angstrom)
        dy = fabs(y1/angstrom - y2/angstrom)
        dz = fabs(z1/angstrom - z2/angstrom)

        if dx > boxlx/2 or dy > boxly/2 or dz > boxlz/2:
            for atom in res2.atoms():
                oldx = positions[atom.index][0]/angstrom
                oldy = positions[atom.index][1]/angstrom
                oldz = positions[atom.index][2]/angstrom
                if dx > boxlx/2.0:
                    if oldx < xcen: newx = oldx + boxlx
                    else: newx = oldx - boxlx
                else:
                    newx = oldx
                if dy > boxly/2.0:
                    if oldy < ycen: newy = oldy + boxly
                    else: newy = oldy - boxly
                else:
                    newy = oldy
                if dz > boxlz/2.0:
                    if oldz < zcen: newz = oldz + boxlz
                    else: newz = oldz - boxlz
                else:
                    newz = oldz

                new_position = Vec3(newx, newy, newz)
                positions[atom.index] = Quantity(new_position, angstroms)

    simulation.context.setPositions(positions)
    return simulation

# ==============================================================================
# Input Generation
# ==============================================================================

def generate_default_inps():
    """ Generates default .inp files following the unified protocol (Min+EQ1) """
    legacy_folders = ['min', 'eq1', 'eq2', 'prod', '02min', '03eq1', '04eq2', '05prod', '02eq1', '03eq2', '04prod']
    for folder in legacy_folders:
        if os.path.exists(folder):
            log_message("INFO", f"Removing legacy folder: {folder}")
            shutil.rmtree(folder)

    # Value equivalent to 5.0 kcal/mol/A^2 in kJ/mol/nm^2
    k_strict = 2092.0

    structure = {
        '02eq1':  ('eq1.inp', (
            "mini_nstep  = 100000                            # Number of steps for minimization\n"
            "mini_tol    = 100.0                             # Minimization energy tolerance\n"
            "\n"
            "gen_vel     = yes                               # Generate initial velocities after minimization\n"
            "gen_temp    = 310                               # Temperature for generating initial velocities (K)\n"
            "gen_seed    = -1                                # Seed for generating initial velocities\n"
            "\n"
            "nstep       = 1000000                           # Number of steps to run (2 ns)\n"
            "dt          = 0.002                             # Time-step (ps)\n"
            "\n"
            "nstout      = 5000                              # Writing output frequency (steps)\n"
            "nstdcd      = 5000                              # Writing coordinates trajectory frequency (steps)\n"
            "\n"
            "coulomb     = PME                               # Electrostatic cut-off method\n"
            "ewald_tol   = 0.0005                            # Ewald error tolerance\n"
            "vdw         = Force-switch                      # vdW cut-off method\n"
            "r_on        = 1.0                               # Switch-on distance (nm)\n"
            "r_off       = 1.2                               # Switch-off distance (nm)\n"
            "lj_lrc      = no                                # Turn on/off LJ long-range correction\n"
            "e14scale    = 1.0                               # 1-4 electrostatic scaling\n"
            "\n"
            "temp        = 310                               # Temperature (K)\n"
            "fric_coeff  = 1                                 # Friction coefficient for Langevin dynamics (ps^-1)\n"
            "integrator  = Langevin                          # Integrator (Langevin or LangevinMiddle)\n"
            "\n"
            "pcouple     = no                                # Turn on/off pressure coupling\n"
            "p_ref       = 1.0                               # Pressure (bar)\n"
            "p_type      = isotropic                         # Barostat type\n"
            "p_freq      = 25                                # Pressure coupling frequency (steps)\n"
            "\n"
            "cons        = HBonds                            # Constraints method\n"
            "\n"
            "rest        = yes                               # Turn on/off restraints\n"
            "rest_atom   = \"protein and backbone\"            # MDAnalysis selection for custom restraints\n"
            f"rest_k      = {k_strict}                            # Force constant for custom selection (kJ/mol/nm^2)\n"
        )),
        '03eq2':  ('eq2.inp', (
            "nstep       = 2500000                           # Number of steps to run (5 ns)\n"
            "dt          = 0.002                             # Time-step (ps)\n"
            "\n"
            "nstout      = 5000                              # Writing output frequency (steps)\n"
            "nstdcd      = 5000                              # Writing coordinates trajectory frequency (steps)\n"
            "\n"
            "gen_vel     = no                                # Use velocities from previous stage\n"
            "\n"
            "coulomb     = PME\n"
            "ewald_tol   = 0.0005\n"
            "vdw         = Force-switch\n"
            "r_on        = 1.0\n"
            "r_off       = 1.2\n"
            "lj_lrc      = no\n"
            "e14scale    = 1.0\n"
            "\n"
            "temp        = 310\n"
            "fric_coeff  = 1\n"
            "integrator  = Langevin\n"
            "\n"
            "pcouple     = yes                               # Turn on pressure coupling (NPT)\n"
            "p_ref       = 1.0                               # Pressure (bar)\n"
            "p_type      = isotropic                         # Barostat type\n"
            "p_freq      = 25                                # Pressure coupling frequency (steps)\n"
            "\n"
            "cons        = HBonds\n"
            "rest        = yes\n"
            "rest_atom   = \"protein and backbone\"\n"
            f"rest_k      = {k_strict}\n"
        )),
        '04prod': ('prod.inp', (
            "nstep       = 5000000                           # Number of steps to run (10 ns)\n"
            "dt          = 0.002\n"
            "\n"
            "nstout      = 25000\n"
            "nstdcd      = 25000\n"
            "\n"
            "gen_vel     = no\n"
            "\n"
            "coulomb     = PME\n"
            "ewald_tol   = 0.0005\n"
            "vdw         = Force-switch\n"
            "r_on        = 1.0\n"
            "r_off       = 1.2\n"
            "lj_lrc      = no\n"
            "e14scale    = 1.0\n"
            "\n"
            "temp        = 310\n"
            "fric_coeff  = 1\n"
            "integrator  = Langevin\n"
            "\n"
            "pcouple     = yes\n"
            "p_ref       = 1.0\n"
            "p_type      = isotropic\n"
            "p_freq      = 100\n"
            "\n"
            "cons        = HBonds\n"
            "rest        = no                                # No restraints in production\n"
         ))
    }

    if not os.path.exists('01build'):
        os.makedirs('01build')
        log_message("INFO", "Created directory: 01build")

    for folder, data in structure.items():
        os.makedirs(folder, exist_ok=True)
        if data:
            filename, content = data
            path = os.path.join(folder, filename)
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    f.write(content)
                log_message("SUCCESS", f"Generated: {path}")
            else:
                log_message("WARNING", f"File {path} already exists. Skipping.")

# ==============================================================================
# Simulation Core Execution
# ==============================================================================

def read_top(filename):
    if filename.endswith('.psf'): return CharmmPsfFile(filename)
    elif filename.endswith('.prmtop'): return AmberPrmtopFile(filename)
    return None

def read_crd(filename, psf_path=None):
    if filename.endswith('.pdb'):
        crd_filename = filename.replace('.pdb', '.crd')
        if os.path.exists(crd_filename):
            log_message("INFO", f"Using existing internal CHARMM CRD: {crd_filename}")
            return CharmmCrdFile(crd_filename)

        if mda is not None:
            try:
                log_message("INFO", f"Internally converting {filename} to {crd_filename} (CHARMM EXT format)...")
                if psf_path and os.path.exists(psf_path):
                    u = mda.Universe(psf_path, filename)
                else:
                    u = mda.Universe(filename)
                u.atoms.write(crd_filename, extended=True)
                return CharmmCrdFile(crd_filename)
            except Exception as e:
                log_message("WARNING", f"Internal CRD conversion failed: {e}. Falling back to standard PDBFile.")
                return PDBFile(filename)
        return PDBFile(filename)
    if filename.endswith('.crd'): return CharmmCrdFile(filename)
    if filename.endswith('.inpcrd'): return AmberInpcrdFile(filename)
    return None

def read_params_from_dir(topdir):
    rtfs = glob.glob(os.path.join(topdir, '*.rtf'))
    prms = glob.glob(os.path.join(topdir, '*.prm'))
    strs = glob.glob(os.path.join(topdir, '*.str'))
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        params = CharmmParameterSet(*(rtfs + prms + strs))
    return params

def read_box_from_str(filename, psf):
    box = [0.0, 0.0, 0.0]
    if not os.path.exists(filename):
        log_message("WARNING", f"PBC file {filename} not found.")
        return psf
    for line in open(filename, 'r'):
        line = line.upper()
        if 'SET A =' in line: box[0] = float(line.split('=')[1])
        if 'SET B =' in line: box[1] = float(line.split('=')[1])
        if 'SET C =' in line: box[2] = float(line.split('=')[1])
    psf.setBox(box[0]*angstroms, box[1]*angstroms, box[2]*angstroms)
    log_message("INFO", f"Taking PBC from {filename}: {box[0]:.3f} x {box[1]:.3f} x {box[2]:.3f}")
    return psf

def run_simulation(args_psf, args_pdb, args_inp, args_irst=None, args_orst='output', args_toppar='toppar/', args_pbc=None, args_platform=None, args_ns=None, args_rewrap=False, args_debug=False):
    # Extension stripping
    output_prefix = args_orst
    for ext in ['.rst', '.dcd', '.xtc', '.log', '.pdb']:
        if output_prefix.lower().endswith(ext):
            output_prefix = output_prefix[: -len(ext)]; break

    out_dir = os.path.dirname(output_prefix)
    if out_dir: os.makedirs(out_dir, exist_ok=True)

    log_message("INFO", f"Loading topology/coords: {args_psf}, {args_pdb}")
    psf = read_top(args_psf)
    
    state = None
    if args_irst:
        if os.path.exists(args_irst):
            log_message("INFO", f"Reading restart file for PBC and state: {args_irst}")
            with open(args_irst, 'r') as f:
                state = XmlSerializer.deserialize(f.read())
            box_vectors = state.getPeriodicBoxVectors()
            a = box_vectors[0][0].value_in_unit(nanometers) * 10.0
            b = box_vectors[1][1].value_in_unit(nanometers) * 10.0
            c = box_vectors[2][2].value_in_unit(nanometers) * 10.0
            psf.setBox(a*angstroms, b*angstroms, c*angstroms)
            log_message("INFO", f"Taking PBC from restart file: {a:.3f} x {b:.3f} x {c:.3f}")
        else:
            log_message("ERROR", f"Restart file {args_irst} NOT FOUND! Cannot continue safely.")
            sys.exit(1)
    else:
        if not args_pbc:
            args_pbc = '01build/step3_pbcsetup.str'
        psf = read_box_from_str(args_pbc, psf)
        
    crd = read_crd(args_pdb, args_psf)
    params = read_params_from_dir(args_toppar)
    
    inputs = read_inputs(args_inp)
    if args_ns: inputs.nstep = int(args_ns * 1000 / inputs.dt)
    
    system = psf.createSystem(params, nonbondedMethod=inputs.coulomb, nonbondedCutoff=inputs.r_off*nanometers,
                             constraints=inputs.cons, ewaldErrorTolerance=inputs.ewald_Tol)
    
    if inputs.vdw == 'Force-switch': system = vfswitch(system, psf, inputs)
    
    if inputs.lj_lrc == 'yes':
        for force in system.getForces():
            if isinstance(force, NonbondedForce): force.setUseDispersionCorrection(True)
            if isinstance(force, CustomNonbondedForce) and force.getNumTabulatedFunctions() != 1:
                force.setUseLongRangeCorrection(True)
                
    if inputs.pcouple == 'yes': system = barostat(system, inputs)
    if inputs.rest == 'yes':
        has_classic_restraints = os.path.exists('restraints/prot_pos.txt') or os.path.exists('restraints/lipid_pos.txt')
        if has_classic_restraints and (inputs.fc_bb > 0 or inputs.fc_sc > 0 or inputs.fc_lpos > 0 or inputs.fc_mpos > 0):
            log_message("INFO", "Applying Classic CHARMM-GUI Restraints.")
            system = restraints(system, crd, inputs)
        elif inputs.rest_atom and inputs.rest_k > 0:
            log_message("INFO", "Applying MDAnalysis-based Restraints.")
            system = apply_mdanalysis_restraints(system, args_psf, args_pdb, inputs, args_debug)
        else:
            log_message("WARNING", "Restraints turned ON (rest=yes) but no valid configuration (Classic or MDA) found.")
            
    if inputs.integrator == 'LangevinMiddle':
        integrator = LangevinMiddleIntegrator(inputs.temp*kelvin, inputs.fric_coeff/picosecond, inputs.dt*picoseconds)
    else:
        integrator = LangevinIntegrator(inputs.temp*kelvin, inputs.fric_coeff/picosecond, inputs.dt*picoseconds)
    
    log_message("INFO", f"Integrator: {inputs.integrator} ({type(integrator).__name__})")
    log_message("INFO", f"Time step (dt): {inputs.dt} ps ({int(inputs.dt*1000)} fs)")
    
    platform = Platform.getPlatformByName(args_platform) if args_platform else None
    if not platform:
        for p in ['CUDA', 'OpenCL', 'CPU']:
            try: platform = Platform.getPlatformByName(p); break
            except: continue
    
    prop = {'Precision': 'mixed'} if platform and platform.getName() in ['CUDA', 'OpenCL'] else {}
    
    try:
        sim = Simulation(psf.topology, system, integrator, platform, prop)
    except Exception as e:
        if platform and platform.getName() != 'CPU':
            log_message("WARNING", f"Falling back to CPU: {e}")
            sim = Simulation(psf.topology, system, integrator, Platform.getPlatformByName('CPU'), {})
        else: raise e

    sim.context.setPositions(crd.positions)
    if state:
        log_message("INFO", f"Applying state from restart: {args_irst}")
        try: sim.context.setState(state)
        except:
            sim.context.setPositions(state.getPositions()); sim.context.setVelocities(state.getVelocities()); sim.context.setTime(state.getTime())
    
    if inputs.mini_nstep > 0:
        log_message("INFO", f"Starting minimization ({inputs.mini_nstep} steps max)...")
        e_init = sim.context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(kilojoules_per_mole)
        log_message("INFO", f"Initial Energy: {e_init:.4f} kJ/mol")
        
        n_blocks = 10
        steps_per_block = max(1, inputs.mini_nstep // n_blocks)
        for i in range(n_blocks):
            sim.minimizeEnergy(tolerance=inputs.mini_tol*kilojoule/mole/nanometers, maxIterations=steps_per_block)
            e_current = sim.context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(kilojoules_per_mole)
            log_message("INFO", f"Minimization Block {i+1}/{n_blocks} | Energy: {e_current:.4f} kJ/mol")
        
        e_final = sim.context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(kilojoules_per_mole)
        log_message("INFO", f"Final Minimization Energy: {e_final:.4f} kJ/mol")

    if inputs.gen_vel == 'yes':
        log_message("INFO", f"Generating initial velocities at {inputs.gen_temp} K...")
        if inputs.gen_seed:
            sim.context.setVelocitiesToTemperature(inputs.gen_temp*kelvin, inputs.gen_seed)
        else:
            sim.context.setVelocitiesToTemperature(inputs.gen_temp*kelvin)
            
        if not args_irst:
            sim.context.setTime(0.0)
    
    rep_args = {
        'step': True,
        'time': True,
        'potentialEnergy': True,
        'kineticEnergy': True,
        'totalEnergy': True,
        'temperature': True,
        'volume': True,
        'density': True,
        'progress': True,
        'remainingTime': True,
        'speed': True,
        'totalSteps': sim.currentStep + inputs.nstep,
        'separator': '\t'
    }
    
    if inputs.nstep > 0:
        sim.reporters.append(StateDataReporter(sys.stdout, inputs.nstout, **rep_args))
        sim.reporters.append(StateDataReporter(f"{output_prefix}.log", inputs.nstout, **rep_args))
        if inputs.nstdcd > 0: sim.reporters.append(DCDReporter(f"{output_prefix}.dcd", inputs.nstdcd))
        
        log_message("INFO", f"Running dynamics: {inputs.nstep} steps...")
        sim.step(inputs.nstep)
    
    if args_rewrap: rewrap(sim)
    
    with open(f"{output_prefix}.rst", 'w') as f:
        f.write(XmlSerializer.serialize(sim.context.getState(getPositions=True, getVelocities=True)))
    
    log_message("INFO", "Done.")
