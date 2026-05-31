# -*- coding: utf-8 -*-

#//*****************************************************************************************//# 
# MDSolProtocol : Este módulo escreve o protcolo estandar para realizar simulações de         #
#                moléculas, em solução, tais como: Proteínas ou proteina e ligando            #
#                                                                                             #
# autor     : Ropón-Palacios G., BSc - MSc estudante em Física Biomolecular.                  #
# afiliação : Departamento de Física, IBILCE/UNESP, São Jośe do Rio Preto, São Paulo.         #                                                  
# e-mail    : georcki.ropon@unesp.br                                                          #
# data      : Quarta-feira 3 de Julho do 2024.                                               #
# $rev$     : Rev Quarta-feira 3 de Julho de 2024                                              #                    
#//*****************************************************************************************//#

#// ****************************************************************************************//#
# Log mudanças no código:                                                                     #
#  1. Adicionando uma classe para o protocolo de md em agua - Quarta-feira 3 de Julho 2024.   #
#// ****************************************************************************************//#

import os 
import shutil

class MDProtocolSol:
    def __init__(self, psf, pdb, temperature, mdtime, dcdfreq=10.0):
        self.psf = psf
        self.pdb = pdb
        self.temperature = temperature
        self.mdtime = mdtime
        # Convert dcdfreq from ps to steps (assuming 2fs timestep)
        # 1 ps = 1000 fs. freq_steps = (ps * 1000) / 2
        self.dcdfreq = int((dcdfreq * 1000) / 2)
        self.mdsteps = int((self.mdtime * 1000)/0.002) # mdtime is in nanoseconds and converts to mdsteps.


    def nvt(self):
        f = open("02nvt/nvt.confg", "w")
        nvt = """\
################### Structure ###################
structure               ../%s
coordinates             ../%s

################### Variables ###################
set temp  %s
temperature $temp
set outputname nvt 
outputName              $outputname

################### Output Parameters ###################
binaryoutput    no
outputenergies  500
outputtiming    500
outputpressure  500
binaryrestart   yes
dcdfile         $outputname.dcd
dcdfreq         %s
XSTFreq         5000

restartfreq     5000
restartname     $outputname.restart

################### Harmonic constriants ###################

constraints     on
consref         ../restraints/prot_posres.ref	
conskfile       ../restraints/prot_posres.ref	
constraintScaling 1.0
conskcol         B

################### Thermostat and Barostat ###################
langevin        on
langevintemp    $temp
langevinHydrogen off
langevindamping  1.0

################### Integrator ###################
timestep    2.0
firstTimestep 0

fullElectFrequency 1
nonbondedfreq 1

cutoff      12.0
pairlistdist 14.0

switching   on
vdwForceSwitching on
switchdist  10.0

PME         on
PMEGridspacing 1
wrapAll     on
wrapWater   on
exclude scaled1-4
1-4scaling 1.0
rigidbonds all

################### FF ###################
paraTypeCharmm          on;                 # We're using charmm type parameter file(s)
set files [glob "../toppar/*"]
foreach file $files {
   parameters		$file 
}

################### Running Script ###################
exec tr "[:upper:]" "[:lower:]" < ../01build/step3_pbcsetup.str | sed -e "s/ =//g" > step3_input.str
source                  step3_input.str

cellBasisVector1     $a   0.0   0.0;        # vector to the next image
cellBasisVector2    0.0    $b   0.0;
cellBasisVector3    0.0   0.0    $c;
cellOrigin          $xcen $ycen $zcen;        # the *center* of the cell

minimize 50000
reinitvels $temp 

run 1000000    ;# 2 ns
""" %(self.psf, self.pdb, self.temperature, self.dcdfreq)
 
        f.write(nvt)
        f.close()
       
    def npt(self): 
        f = open("03npt/npt.confg", "w")
        npt = """\
################### Structure ###################
structure               ../%s
coordinates             ../%s

################### Variables ###################
set temp  %s
set outputname npt
outputName              $outputname

################### Output Parameters ###################
binaryoutput    no
outputenergies  500
outputtiming    500
outputpressure  500
binaryrestart   yes
dcdfile         $outputname.dcd
dcdfreq         %s
XSTFreq         5000

restartfreq     5000
restartname     $outputname.restart

################### Harmonic constriants ###################

constraints     on
consref         ../restraints/prot_posres.ref		
conskfile       ../restraints/prot_posres.ref		
constraintScaling 1.0
conskcol         B

################### Thermostat and Barostat ###################
langevin        on
langevintemp    $temp
langevinHydrogen off
langevindamping  1.0

usegrouppressure    yes
useflexiblecell     no
useConstantArea     no

langevinpiston      on
langevinpistontarget 1.01325
langevinpistonperiod 200.0
langevinpistondecay  100.0
langevinpistontemp  $temp

################### Integrator ###################
timestep    2

fullElectFrequency 1
nonbondedfreq 1
cutoff      12.0
pairlistdist 14.0
switching   on

vdwForceSwitching on

switchdist  10.0
PME         on
PMEGridspacing 1
wrapAll     on
wrapWater   on
exclude scaled1-4
1-4scaling 1.0
rigidbonds all

################### FF ###################
# Nota: Se você tem um ligando, coloque em toppar pasta o archivo prm ou str de seu 
#       ligando, para evitar erros. 
paraTypeCharmm          on;                 # We're using charmm type parameter file(s)
set files [glob "../toppar/*"]
foreach file $files {
   parameters		$file 
}

################### Running Script ###################
set inputname  ../02nvt/nvt
binCoordinates $inputname.restart.coor
extendedSystem $inputname.restart.xsc
binvelocities  $inputname.restart.vel

# equilibration with constraint during 5 ns 
run 2500000
""" %(self.psf, self.pdb, self.temperature, self.dcdfreq)

        f.write(npt)
        f.close()

    def md(self): 
        f = open("04md/md.confg", "w")
        md = """\
################### Structure ###################
structure               ../%s
coordinates             ../%s

################### Variables ###################
set temp  %s
set dotemp $temp
set outputname md0
outputName              $outputname

################### Output Parameters ###################
binaryoutput    no
outputenergies  500
outputtiming    500
outputpressure  500
binaryrestart   yes
dcdfile         $outputname.dcd
dcdfreq         %s
XSTFreq         5000

restartfreq     5000
restartname     $outputname.restart

################### Thermostat and Barostat ###################
langevin        on
langevintemp    $temp
langevinHydrogen off
langevindamping  1.0

usegrouppressure    yes
useflexiblecell     no
useConstantArea     no

langevinpiston      on
langevinpistontarget 1.01325
langevinpistonperiod 200.0
langevinpistondecay  100.0
langevinpistontemp  $temp

################### Integrator ###################
timestep    2

fullElectFrequency 1
nonbondedfreq 1
cutoff      12.0
pairlistdist 14.0
switching   on

vdwForceSwitching on

switchdist  10.0
PME         on
PMEGridspacing 1
wrapAll     on
wrapWater   on
exclude scaled1-4
1-4scaling 1.0
rigidbonds all

################### FF ###################
paraTypeCharmm          on;                 # We're using charmm type parameter file(s)
set files [glob "../toppar/*"]
foreach file $files {
   parameters		$file 
}

################### Running ###################
# Continuing a job from the restart files
set npt 1
set restart off
set num 0
set count [expr $num - 1]

if {$npt} {
    set inputname ../03npt/npt
    binCoordinates $inputname.restart.coor
    extendedSystem $inputname.restart.xsc
    binvelocities  $inputname.restart.vel
}

proc get_first_ts { xscfile } {
    set fd [open $xscfile r]
    gets $fd
    gets $fd
    gets $fd line
    set ts [lindex $line 0]
    close $fd
    return $ts
}

if { $restart == "on" } {
    firsttimestep       [get_first_ts md$count.restart.xsc]
    set ft              [get_first_ts md$count.restart.xsc]
} else {
    set ft 0
    firsttimestep $ft
}

set totaltime   %s
set currenttime [expr $totaltime - $ft]

# run
if {$npt} {
    reinitvels $dotemp
} 
numsteps                $totaltime
run                     $currenttime;     # %s ns
""" % (self.psf, self.pdb, self.temperature, self.dcdfreq, self.mdsteps, self.mdtime) 
        f.write(md)
        f.close()

    def restraint(self):
        f = open("makerest.tcl", "w")
        rest = """\
set psf %s 
set pdb %s 

mol new $psf
mol addfile $pdb 

set all [atomselect top "all"] 
$all set beta 0 
set restraints [atomselect top "protein and backbone or (segid HETA and noh) or (segname \\"CAR.*\\" and noh)"]
$restraints set beta 5 ;# Set force constant k=5 kcal/mol for restraint atoms
$all writepdb restraints/prot_posres.ref
quit
""" % (self.psf, self.pdb) 
        f.write(rest)
        f.close()
        os.system("mkdir -p restraints")
        os.system("vmd -dispdev text -e makerest.tcl 2>&1 | tee rest.log")

    def runner_script(self):
        f = open("runner.sh", "w")
        script = """#!/bin/bash
# Generated by MSTBx Runner Generator v0.8.5

# --- CONTROL FLAGS ---
eq=on
md_init=off
md_continue=off
# ----------------------

# --- NAMD CONFIG ---
NAMD="namd2" # Or namd3
OPTS="+p8"    # Number of cores or GPU flags
# --------------------

# Colors for output
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m'

echo -e "${GREEN}MSTBx Runner initiated${NC}"

if [ "$eq" == "on" ]; then
    echo -e "${YELLOW}Starting Equilibration (NVT)...${NC}"
    cd 02nvt && $NAMD $OPTS nvt.confg > nvt.log || exit 1
    cd ..
    
    echo -e "${YELLOW}Starting Equilibration (NPT)...${NC}"
    cd 03npt && $NAMD $OPTS npt.confg > npt.log || exit 1
    cd ..
fi

if [ "$md_init" == "on" ]; then
    echo -e "${YELLOW}Starting Initial Production MD...${NC}"
    cd 04md && $NAMD $OPTS md.confg > md.log || exit 1
    cd ..
fi

if [ "$md_continue" == "on" ]; then
    echo -e "${YELLOW}Continuing Production MD...${NC}"
    # This logic assumes NAMD writes restart files. 
    # For a generic script, we just run the same config if it handles restarts internally
    # Or you can edit the script to point to a specific restart.
    cd 04md && $NAMD $OPTS md.confg >> md.log || exit 1
    cd ..
fi

echo -e "${GREEN}Simulation steps completed successfully.${NC}"
"""
        f.write(script)
        f.close()
        os.system("chmod +x runner.sh")

    def copytoppar(self):
        # Encontrar la ruta de la carpeta 'toppar' relativa a este archivo
        current_dir = os.path.dirname(os.path.abspath(__file__))
        toppar_path = os.path.abspath(os.path.join(current_dir, "..", "toppar"))

        if os.path.exists(toppar_path):
            os.system(f"cp -r {toppar_path} .")
        else:
            # Fallback a la variable de entorno por si acaso
            os.system("cp -r $MSTBx/mstbx/core/toppar .")
#-------------------------------------------------------------------#
# STEERED MOLECULAR DYNAMICS                                        #
#-------------------------------------------------------------------#
class SMDProtocolSol:
    def __init__(self, psf, pdb, temperature, mdtime, selpull, selanchor, targetCenter,
                 kforce=1.5, dcdfreq=5000, velocity=10.0, colvar_input=None):
        self.psf = psf 
        self.pdb = pdb 
        self.temperature = temperature
        self.dcdfreq = dcdfreq
        self.kforce = kforce
        self.selpull = selpull
        self.selanchor = selanchor
        self.targetCenter = targetCenter
        self.velocity = velocity
        self.colvar_input = colvar_input

        # Calculate time and steps based on distance and velocity
        # mdtime (ns) = distance (A) / velocity (A/ns)
        self.mdtime = float(self.targetCenter) / float(self.velocity)
        self.mdsteps = int((self.mdtime * 1000)/0.002) # total steps at 2fs timestep

    def smd(self):
        f = open("04md/smd.confg", "w")
        smd = """\
################### Structure ###################
structure               ../%s
coordinates             ../%s

################### Variables ###################
set dotemp %s
set outputname smd0
outputName              $outputname

################### Output Parameters ###################
binaryoutput    no
outputenergies  500
outputtiming    500
outputpressure  500
binaryrestart   yes
dcdfile         $outputname.dcd
dcdfreq         %s
XSTFreq         500
restartfreq     500
restartname     $outputname.restart

################### Thermostat and Barostat ###################
langevin        on
langevintemp    $dotemp
langevinHydrogen off
langevindamping  1.0

usegrouppressure    yes
useflexiblecell     no
useConstantArea     no

langevinpiston      on
langevinpistontarget 1.01325
langevinpistonperiod 200.0
langevinpistondecay  100.0
langevinpistontemp  $dotemp

################### Integrator ###################
timestep    2

fullElectFrequency 1
nonbondedfreq 1
cutoff      12.0
pairlistdist 14.0
switching   on

vdwForceSwitching on

switchdist  10.0
PME         on
PMEGridspacing 1
wrapAll     on
wrapWater   on
exclude scaled1-4
1-4scaling 1.0
rigidbonds all

################### FF ###################
# Nota: Se você tem um ligando, coloque em toppar pasta o archivo prm ou str de seu 
#       ligando, para evitar erros. 
paraTypeCharmm          on;                 # We're using charmm type parameter file(s)
set files [glob "../toppar/*"]
foreach file $files {
   parameters		$file 
}

############ SMD ################
colvars on 
colvarsConfig smd.in 

constraints     on
consref         AnchorAtom.pdb
conskfile       AnchorAtom.pdb
constraintScaling 1.0
conskcol         B
selectConstraints on
selectConstrX off
selectConstrY  off
selectConstrZ on

################### Running ###################
# Continuing a job from the restart files
set npt 1
set restart off
set num 0
set count [expr $num - 1]

if {$npt} {
    set inputname  ../03npt/npt
    binCoordinates $inputname.restart.coor
    extendedSystem $inputname.restart.xsc
    binvelocities  $inputname.restart.vel
} else {
    set inputname  smd$count
    binCoordinates $inputname.restart.coor
    extendedSystem $inputname.restart.xsc
    binvelocities  $inputname.restart.vel
    colvarsIput    $inputname.colvars.state
}

proc get_first_ts {xscfile} {
    set fd [open $xscfile r]
    gets $fd
    gets $fd
    gets $fd line
    set ts [lindex $line 0]
    close $fd
    return $ts
}

if { $restart == "on" } {
    firsttimestep       [get_first_ts md$count.restart.xsc]
    set ft              [get_first_ts md$count.restart.xsc]
} else {
    set ft 0
    firsttimestep $ft
}

set totaltime   %s
set currenttime [expr $totaltime - $ft]

# run
if {$npt} {
    reinitvels $dotemp
} 
numsteps                $totaltime
run                     $currenttime;     #  %s ns
""" % (self.psf, self.pdb, self.temperature, self.dcdfreq, self.mdsteps, self.mdtime)
        f.write(smd)
        f.close()

    def colvars(self):
        if self.colvar_input and os.path.isdir(self.colvar_input):
            config_name = "smd.in"
            config_path = os.path.join(self.colvar_input, config_name)
            
            if not os.path.exists(config_path):
                # Check for alternative naming just in case
                if os.path.exists(os.path.join(self.colvar_input, "colvars.in")):
                    config_name = "colvars.in"
                    config_path = os.path.join(self.colvar_input, config_name)
                else:
                    raise FileNotFoundError(f"Main config file (smd.in) not found in {self.colvar_input}")

            # Validation: Check for files mentioned in the colvars config
            import re
            with open(config_path, 'r') as f:
                content = f.read()
                # Find patterns like atomsFile filename.pdb
                files_mentioned = re.findall(r'atomsFile\s+([^\s]+)', content)
                for fm in files_mentioned:
                    # Clean potential quotes
                    fm = fm.strip('"').strip("'")
                    if not os.path.exists(os.path.join(self.colvar_input, fm)):
                        print(f"[WARNING] File '{fm}' mentioned in {config_name} was not found in the custom folder.")

            # Copy everything from the custom folder to 04md/
            for item in os.listdir(self.colvar_input):
                s = os.path.join(self.colvar_input, item)
                d = os.path.join("04md", item)
                if os.path.isfile(s):
                    shutil.copy2(s, d)
            
            # Ensure the main config is named smd.in in the target folder
            if config_name != "smd.in":
                shutil.move(os.path.join("04md", config_name), "04md/smd.in")
            return

        f = open("04md/smd.in", "w")
        colvars = """\
Colvarstrajfrequency    100

colvar {
        name PullAtom
        width 1.0
        outputAppliedForce yes

        distanceZ {
                main {
                        atomsFile PullAtom.pdb
                        atomsCol B
                        atomsColValue 1
                }
                ref {
                       dummyAtom (0.0, 0.0, 0.0)
                }
	            axis (0.0, 0.0, 1.0)

        }
}

harmonic {
    name SMD 
    colvars  PullAtom        #! in Angstroms 
    centers  xcenter         #! Centro dos carbonos alpha ou heavy atoms para fazer pulling.
    targetCenters xtarget    #! Centro taget até a onde se quer fazer pulling.
    forceConstant %s         #! Força constante para o pulling em kcal/mol/A² 
    targetNumSteps %s        #! Total número de steps, calculado pela velocidade.  
    outputCenters   on       #! Print o centers do atoms pulling durante a simulação. 
    outputAccumulatedWork yes #! Print o trabajo acumulado, necessário para o jarzynski.
}
""" % (self.kforce, self.mdsteps)
        f.write(colvars)
        f.close()

    def makecolvarspdb(self):
        f = open("makePDBcolvars.tcl", "w")
        script = """\
set psf %s 
set pdb %s 
set selpull \"%s\"
set selanchor \"%s\"  
set targetcenter %s 

mol new $psf
mol addfile $pdb 

set all [atomselect top \"all\"] 
$all set beta 0 
set pullAtom [atomselect top \"$selpull\"]
$pullAtom set beta 1.0
$all writepdb 04md/PullAtom.pdb 

set all [atomselect top \"all\"]
$all set beta 0 
set AnchorAtom [atomselect top \"$selanchor\"]
$AnchorAtom set beta 5.0       ;# kcal/mol/A² 
$all writepdb 04md/AnchorAtom.pdb 

set centerpull [lindex [measure center [atomselect top \"$selpull\"] ] 2]
set restraintcenter [lindex [measure center [atomselect top \"$selanchor\"]] 2]
set targetcom [expr $centerpull + $targetcenter]

exec sed -i -e \"s/xcenter/$centerpull/g\" 04md/smd.in 
exec sed -i -e \"s/xtarget/$targetcom/g\" 04md/smd.in 

quit 
""" % (self.psf, self.pdb, self.selpull, self.selanchor, self.targetCenter)
        f.write(script)
        f.close()
        os.system("vmd -dispdev text -e makePDBcolvars.tcl 2>&1 | tee colvars.log")

    def runner_script(self):
        f = open("runner.sh", "w")
        script = """#!/bin/bash
# Generated by MSTBx Runner Generator v0.8.5

# --- CONTROL FLAGS ---
eq=on
md_init=off
md_continue=off
# ----------------------

# --- NAMD CONFIG ---
NAMD="namd2"
OPTS="+p8"
# --------------------

GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m'

echo -e "${GREEN}MSTBx Runner initiated (SMD Protocol)${NC}"

if [ "$eq" == "on" ]; then
    echo -e "${YELLOW}Starting Equilibration...${NC}"
    cd 02nvt && $NAMD $OPTS nvt.confg > nvt.log || exit 1
    cd ..
    cd 03npt && $NAMD $OPTS npt.confg > npt.log || exit 1
    cd ..
fi

if [ "$md_init" == "on" ]; then
    echo -e "${YELLOW}Starting SMD Production...${NC}"
    cd 04md && $NAMD $OPTS smd.confg > smd.log || exit 1
    cd ..
fi

echo -e "${GREEN}SMD simulation steps completed.${NC}"
"""
        f.write(script)
        f.close()
        os.system("chmod +x runner.sh")

#-------------------------------------------------------------------#
# WELL TEMPERED METADYNAMICS                                        #
#-------------------------------------------------------------------#
class WTMetaDProtocolSol:
    def __init__(self, psf, pdb, temperature, mdtime, hill=0.01, hillfreq=500, width=1.0,
                 biasT=15, sel1="segid PROA and name CA", sel2="segid PROB and name CA", 
                 dunbind=50.0, dcdfreq=5000, colvar_input=None):
        self.psf = psf 
        self.pdb = pdb 
        self.temperature = temperature
        self.mdtime = mdtime 
        self.dcdfreq = dcdfreq
        self.mdsteps = int((self.mdtime * 1000)/0.002) # mdtime is em nanosegundos e converte para mdsteps. 
        self.hill = hill         
        self.hillfreq = int(hillfreq)      
        self.width = width
        self.biasT = biasT
        self.biasTemperature = int((self.biasT * temperature) - temperature)
        self.sel1 = sel1
        self.sel2 = sel2
        self.dunbind = dunbind
        self.colvar_input = colvar_input


    def wtmetad(self):
        f = open("04md/md.confg", "w")
        metad = """\
################### Structure ###################
structure               ../%s
coordinates             ../%s

################### Variables ###################
set dotemp %s
set outputname md0
outputName              $outputname

################### Output Parameters ###################
binaryoutput    no
outputenergies  500
outputtiming    500
outputpressure  500
binaryrestart   yes
dcdfile         $outputname.dcd
dcdfreq         %s
XSTFreq         500
restartfreq     500
restartname     $outputname.restart

################### Thermostat and Barostat ###################
langevin        on
langevintemp    $dotemp
langevinHydrogen off
langevindamping  1.0

usegrouppressure    yes
useflexiblecell     no

langevinpiston      on
langevinpistontarget 1.01325
langevinpistonperiod 200.0
langevinpistondecay  100.0
langevinpistontemp  $dotemp

################### Integrator ###################
timestep    2

fullElectFrequency 1
nonbondedfreq 1
cutoff      12.0
pairlistdist 14.0
switching   on

vdwForceSwitching on

switchdist  10.0
PME         on
PMEGridspacing 1
wrapAll     on
wrapWater   on
exclude scaled1-4
1-4scaling 1.0
rigidbonds all

################### FF ###################
paraTypeCharmm          on;                 # We're using charmm type parameter file(s)
set files [glob "../toppar/*"]
foreach file $files {
   parameters		$file 
}

############ Metadynamics ################
colvars on 
colvarsConfig wtmetad.in 

constraints     on
consref         ../restraints/prot_posres.ref
conskfile       ../restraints/prot_posres.ref
constraintScaling 1.0
conskcol         B

################### Running ###################
# Continuing a job from the restart files
set npt 1
set restart off
set num 0
set count [expr $num - 1]

if {$npt} {
    set inputname  ../03npt/npt
    binCoordinates $inputname.restart.coor
    extendedSystem $inputname.restart.xsc
    binvelocities  $inputname.restart.vel
} else {
    set inputname  md$count
    binCoordinates $inputname.restart.coor
    extendedSystem $inputname.restart.xsc
    binvelocities  $inputname.restart.vel
    colvarsIput    $inputname.colvars.state
}

proc get_first_ts {xscfile} {
    set fd [open $xscfile r]
    gets $fd
    gets $fd
    gets $fd line
    set ts [lindex $line 0]
    close $fd
    return $ts
}

if { $restart == "on" } {
    firsttimestep       [get_first_ts md$count.restart.xsc]
    set ft              [get_first_ts md$count.restart.xsc]
} else {
    set ft 0
    firsttimestep $ft
}

set totaltime   %s
set currenttime [expr $totaltime - $ft]

# run
if {$npt} {
    reinitvels $dotemp
} 
numsteps                $totaltime;       # para cuando chega aos steps total aqui. 
run                     $currenttime;     # %s ns

""" % (self.psf, self.pdb, self.temperature, self.dcdfreq, self.mdsteps, self.mdtime)
        f.write(metad)
        f.close()
        
    def colvars(self):
        '''
           This method writes the collective variable file for Well-Tempered Metadynamics.
        '''
        if self.colvar_input and os.path.isdir(self.colvar_input):
            config_name = "wtmetad.in"
            config_path = os.path.join(self.colvar_input, config_name)
            
            if not os.path.exists(config_path):
                # Check for alternative naming
                if os.path.exists(os.path.join(self.colvar_input, "colvars.in")):
                    config_name = "colvars.in"
                    config_path = os.path.join(self.colvar_input, config_name)
                else:
                    raise FileNotFoundError(f"Main config file (wtmetad.in) not found in {self.colvar_input}")

            # Validation: Check for files mentioned in the colvars config
            import re
            with open(config_path, 'r') as f:
                content = f.read()
                files_mentioned = re.findall(r'atomsFile\s+([^\s]+)', content)
                for fm in files_mentioned:
                    fm = fm.strip('"').strip("'")
                    if not os.path.exists(os.path.join(self.colvar_input, fm)):
                        print(f"[WARNING] File '{fm}' mentioned in {config_name} was not found in the custom folder.")

            # Copy all files
            for item in os.listdir(self.colvar_input):
                s = os.path.join(self.colvar_input, item)
                d = os.path.join("04md", item)
                if os.path.isfile(s):
                    shutil.copy2(s, d)
            
            # Ensure proper naming
            if config_name != "wtmetad.in":
                shutil.move(os.path.join("04md", config_name), "04md/wtmetad.in")
            return

        f = open("04md/wtmetad.in", "w")
        colvars = """\
Colvarstrajfrequency    100

colvar {
    name AtomDistance
    width %s 

    distance {
        group1 {
            atomsFile colvars_sel1.pdb
            atomsCol B
            atomsColValue 1
        }
        group2 {
            atomsFile colvars_sel2.pdb
            atomsCol B
            atomsColValue 1
        }

    }
}

harmonicWalls {
    name WTMetaD-Walls
    colvars AtomDistance
    lowerWalls xc          # lowerboundary. 
    upperWalls xd         # upperboundary.
    lowerWallConstant 10.0  # Força mesma como em charmm-gui. 
    upperWallConstant 10.0  # Força mesma como em charmm-gui. 


}

metadynamics {
    name     WTMetaD-Distance
    colvars  AtomDistance 
    hillWeight              %s       # Valor padrão é 0.01 kcal/mol.  
    newHillFrequency        %s   # Valor padrão. 500.     
    hillwidth               %s        # Mesmo no que BFEE2. valores recomendados no manual entre 1 e 3. 
    writeHillsTrajectory    on         # Escreve un arquivo para armazenar os Hills (kcal/mol)
    wellTempered            on         # Favorece WellTempered Metadynamics.
    biasTemperature         %s      # Mesmo no que BFEE2. O Bias factor é calculado como:
                                       # biasFactor = (TemperatureMD + biasTemperature) / TemperatureMD
                                       # Onde TemperatureMD é a temperatura escolhida da simulação.
                                       # e biasTemperature é a temperatura escolhida aquí, na metadinâmica, biasFactor 15 cá. 
} 
""" % (self.width, self.hill, self.hillfreq, self.width, self.biasTemperature) 
        f.write(colvars)
        f.close()

    def makecolvarspdb(self):
        f = open("makePDBcolvars.tcl", "w")
        script = """\
set psf %s 
set pdb %s 
set selp1 \\"%s\\"
set selp2 \\"%s\\"
set dunbind %s


mol new $psf
mol addfile $pdb 

set all [atomselect top \\"all\\"] 
$all set beta 0 
set s1 [atomselect top \\"$selp1\\"]
$s1 set beta 1.0
$all writepdb 04md/colvars_sel1.pdb 

set all [atomselect top \\"all\\"]
$all set beta 0 
set s2 [atomselect top \\"$selp2\\"]
$s2 set beta 1.0
$all writepdb 04md/colvars_sel2.pdb 

set c1 [measure center [atomselect top \\"$selp1\\"]]
set c2 [measure center [atomselect top \\"$selp2\\"]]
set dist [veclength [vecsub $c1 $c2]]

set lb [expr $dist - 5.0]
if { $lb < 0 } { set lb 0 }
set ub [expr $dist + %s]

exec sed -i -e \\"s/xc/$lb/g\\" 04md/wtmetad.in
exec sed -i -e \\"s/xd/$ub/g\\" 04md/wtmetad.in

quit 
""" % (self.psf, self.pdb, self.sel1, self.sel2, self.dunbind, self.dunbind) 
        f.write(script)
        f.close()
        os.system("vmd -dispdev text -e makePDBcolvars.tcl 2>&1 | tee colvars.log")

    def runner_script(self):
        f = open("runner.sh", "w")
        script = """#!/bin/bash
# Generated by MSTBx Runner Generator v0.8.5

# --- CONTROL FLAGS ---
eq=on
md_init=off
md_continue=off
# ----------------------

# --- NAMD CONFIG ---
NAMD="namd2"
OPTS="+p8"
# --------------------

GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m'

echo -e "${GREEN}MSTBx Runner initiated (Metadynamics Protocol)${NC}"

if [ "$eq" == "on" ]; then
    echo -e "${YELLOW}Starting Equilibration...${NC}"
    cd 02nvt && $NAMD $OPTS nvt.confg > nvt.log || exit 1
    cd ..
    cd 03npt && $NAMD $OPTS npt.confg > npt.log || exit 1
    cd ..
fi

if [ "$md_init" == "on" ]; then
    echo -e "${YELLOW}Starting Metadynamics Production...${NC}"
    cd 04md && $NAMD $OPTS md.confg > md.log || exit 1
    cd ..
fi

if [ "$md_continue" == "on" ]; then
    echo -e "${YELLOW}Continuing Metadynamics Production...${NC}"
    cd 04md && $NAMD $OPTS md.confg >> md.log || exit 1
    cd ..
fi

echo -e "${GREEN}Metadynamics simulation steps completed.${NC}"
"""
        f.write(script)
        f.close()
        os.system("chmod +x runner.sh")
