# -*- coding: utf-8 -*-

#//*****************************************************************************************//# 
# MDMembProtocol: Este módulo escreve o protcolo estandar para realizar simulações de         #
#                moléculas, em membrana, tais como: Proteínas ou proteina e ligando           #
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

class MDProtocolMemb:
    def __init__(self, psf, pdb, temperature=310, mdtime=100):
        self.psf = psf 
        self.pdb = pdb 
        self.temperature = temperature 
        self.mdtime = mdtime 
        self.mdsteps = int((self.mdtime * 1000)/0.002) # mdtime is em nanosegundos e converte para mdsteps.

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
dcdfreq         5000
XSTFreq         5000
restartfreq     5000
restartname     $outputname.restart

################### Harmonic constriants ###################

constraints     on
consref         ../restraints/meltlipid.ref	
conskfile       ../restraints/meltlipid.ref	
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
exec tr "\[:upper:\]" "\[:lower:\]" < ../01build/step3_pbcsetup.str | sed -e "s/ =//g" > step3_input.str
source                  step3_input.str

cellBasisVector1     $a   0.0   0.0;        # vector to the next image
cellBasisVector2    0.0    $b   0.0;
cellBasisVector3    0.0   0.0    $c;
cellOrigin          $xcen $ycen $zcen;        # the *center* of the cell

minimize 25000
reinitvels $temp 

run 1000000    ;# 2 ns
""" %(self.psf, self.pdb, self.temperature) 
        f.write(nvt)
        f.close()
        
    def npt1(self): 
        f = open("03npt1/npt1.confg", "w")
        npt = """\
################### Structure ###################
structure               ../%s
coordinates             ../%s

################### Variables ###################
set temp  %s
set outputname npt1
outputName              $outputname

################### Output Parameters ###################
binaryoutput    no
outputenergies  500
outputtiming    500
outputpressure  500
binaryrestart   yes
dcdfile         $outputname.dcd
dcdfreq         5000
XSTFreq         5000
restartfreq     5000
restartname     $outputname.restart

################### Harmonic constriants ###################

constraints     on
consref         ../restraints/protein.ref		
conskfile       ../restraints/protein.ref		
constraintScaling 1.0
conskcol         B

################### Thermostat and Barostat ###################
langevin        on
langevintemp    $temp
langevinHydrogen off
langevindamping  1

usegrouppressure    yes
useflexiblecell     yes
useConstantRatio    yes;                # keeps the ratio of the unit cell in the x-y plane constant A=B

langevinpiston      on
langevinpistontarget 1.01325
langevinpistonperiod 50.0
langevinpistondecay 25.0
langevinpistontemp  $temp

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
set inputname  ../02nvt/nvt
binCoordinates $inputname.restart.coor
extendedSystem $inputname.restart.xsc
binvelocities  $inputname.restart.vel

# equilibration with constraint during 5 ns 
minimize 25000
reinitvels $temp 

run 2500000
""" % (self.psf, self.pdb, self.temperature)
        f.write(npt)
        f.close()


    def npt2(self): 
        f = open("04npt2/npt2.confg", "w")
        npt = """\
################### Structure ###################
structure               ../%s
coordinates             ../%s

################### Variables ###################
set temp  %s
set outputname npt2
outputName              $outputname

################### Output Parameters ###################
binaryoutput    no
outputenergies  500
outputtiming    500
outputpressure  500
binaryrestart   yes
dcdfile         $outputname.dcd
dcdfreq         5000
XSTFreq         5000
restartfreq     5000
restartname     $outputname.restart

################### Harmonic constriants ###################

constraints     on
consref         ../restraints/backbone.ref	
conskfile       ../restraints/backbone.ref	
constraintScaling 1.0
conskcol         B

################### Thermostat and Barostat ###################
langevin        on
langevintemp    $temp
langevinHydrogen off
langevindamping  1

usegrouppressure    yes
useflexiblecell     yes
useConstantRatio    yes;                # keeps the ratio of the unit cell in the x-y plane constant A=B

langevinpiston      on
langevinpistontarget 1.01325
langevinpistonperiod 50.0
langevinpistondecay 25.0
langevinpistontemp  $temp

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
set inputname  ../03npt1/npt1
binCoordinates $inputname.restart.coor
extendedSystem $inputname.restart.xsc
binvelocities  $inputname.restart.vel

# equilibration with constraint during 5 ns 
run 2500000
""" % (self.psf, self.pdb, self.temperature)
        f.write(npt)
        f.close()

    def md(self): 
        f = open("05md/md.confg", "w")
        md = """\
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
dcdfreq         5000
XSTFreq         5000
restartfreq     5000
restartname     $outputname.restart

################### Thermostat and Barostat ###################
langevin        on
langevintemp    $dotemp
langevinHydrogen off
langevindamping  1.0

usegrouppressure    yes
useflexiblecell     yes
useConstantRatio    yes;                # keeps the ratio of the unit cell in the x-y plane constant A=B

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

################### Running ###################
# Continuing a job from the restart files
set npt 1
set restart off
set num 0
set count [expr $num - 1]

if {$npt} {
    set inputname  ../04npt2/npt2
    binCoordinates $inputname.restart.coor
    extendedSystem $inputname.restart.xsc
    binvelocities  $inputname.restart.vel
} else {
    set inputname md$count
    binCoordinates $inputname.restart.coor
    extendedSystem $inputname.restart.xsc
    binvelocities  $inputname.restart.vel
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
run                     $currenttime;     # %s ns
""" % (self.psf, self.pdb, self.temperature, self.mdsteps, self.mdtime) 
        f.write(md)
        f.close()

    def restraint(self):
        f = open("rest.tcl", "w")
        rest = """\
set psf %s 
set pdb %s 

mol new $psf
mol addfile $pdb 

set all [atomselect top \"all\"] 
$all set beta 0 
set lipid [atomselect top \"(protein) or (segid MEMB and type PL) or (segid HETA and noh) or waters or ions\"] 
$lipid set beta 5               ;# Set force constant k=5 kcal/mol for restraint atoms
$all writepdb restraints/meltlipid.ref 

set all [atomselect top \"all\"]
$all set beta 0 
set protein [atomselect top \"protein or (segid HETA and noh)\"]
$protein set beta 5 
$all writepdb restraints/protein.ref

set all [atomselect top \"all\"]
$all set beta 0
set backbone [atomselect top \"(protein and backbone) or (segid HETA and noh)\"]
$backbone set beta 5
$all writepdb restraints/backbone.ref 

quit
""" % (self.psf, self.pdb) 
        f.write(rest)
        f.close()
        os.system("mkdir -p restraints")
        os.system("vmd -dispdev text -e rest.tcl 2>&1 | tee rest.log")


    def copytoppar(self):
        #shutil.copytree("../../TestLIB/toppar/", "./")
        os.system("cp -r ../../TestLIB/toppar/ .")

