# -*- coding: utf-8 -*-

#//*****************************************************************************************//# 
# MDSolProtocol: Este módulo escreve o protcolo estandar para realizar simulações de          #
#                moléculas, em solução, tais como: Proteínas ou proteina e ligando            #
#                                                                                             #
# autor     : Ropón-Palacios G., BSc - MSc estudante em Física Biomolecular.                  #
# afiliação : Departamento de Física, IBILCE/UNESP, São Jośe do Rio Preto, São Paulo.         #                                                  
# e-mail    : georcki.ropon@unesp.br                                                          #
# data      : Terça-feira 2 de Julho do 2024.                                               #
# $rev$     : Rev Terça-feira 2 de Julho de 2024                                              #                    
#//*****************************************************************************************//#

#// ****************************************************************************************//#
# Log mudanças no código:                                                                     #
#  1. Adicionando uma classe para o protocolo de md em agua - Terça-feira 2 de Julho 2024.    #
#// ****************************************************************************************//#

import os 
import shutil

class MDProtocolSol:
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
exec tr "\[:upper:\]" "\[:lower:\]" < ../01build/step3_pbcsetup.str | sed -e "s/ =//g" > step3_input.str
source                  step3_input.str

cellBasisVector1     $a   0.0   0.0;        # vector to the next image
cellBasisVector2    0.0    $b   0.0;
cellBasisVector3    0.0   0.0    $c;
cellOrigin          $xcen $ycen $zcen;        # the *center* of the cell

minimize 50000
reinitvels $temp 

run 1000000    ;# 2 ns
""" %(self.psf, self.pdb, self.temperature) 
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
dcdfreq         5000
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
langevindamping  1

usegrouppressure    yes
useflexiblecell     no
useConstantArea     no

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
run 2500000
""" % (self.psf, self.pdb, self.temperature)
        f.write(npt)
        f.close()

    def md(self): 
        f = open("04md/md.confg", "w")
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
        f = open("makerest.tcl", "w")
        rest = """\
set psf %s 
set pdb %s 

mol new $psf
mol addfile $pdb 

set all [atomselect top \"all\"] 
$all set beta 0 
set restraints [atomselect top \"(protein and backbone) or (segid HETA and noh)\"] 
$restraints set beta 5 ;# Set force constant k=5 kcal/mol for restraint atoms
$all writepdb restraints/prot_posres.ref
quit
""" % (self.psf, self.pdb) 
        f.write(rest)
        f.close()
        os.system("mkdir -p restraints")
        os.system("vmd -dispdev text -e makerest.tcl 2>&1 | tee rest.log")


    def copytoppar(self):
        #shutil.copytree("../../TestLIB/toppar/", "./")
        #abs_path = list(os.path.abspath(".").split("MD"))[0]
        #toppar = os.path.join(abs_path, "toppar") 
        f = open("copy.sh", "w")
        f.write("cp -r $MSTBx/LIB/toppar .")
        f.close()
        os.system("bash copy.sh")
        os.system("rm copy.sh")
        #os.system("cp -r \$MSTBx/LIB/toppar .")

#-------------------------------------------------------------------#
# STEERED MOLECULAR DYNAMICS                                        #
#-------------------------------------------------------------------#
class SMDProtocolSol:
    def __init__(self, psf, pdb, temperature, mdtime, selpull, selanchor, targetCenter,
                 kforce=1.5):
        self.psf = psf 
        self.pdb = pdb 
        self.temperature = temperature
        self.mdtime = mdtime 
        self.mdsteps = int((self.mdtime * 1000)/0.002) # mdtime is em nanosegundos e converte para mdsteps. 
        #self.speed  = speed          # 10 A/ns for pulling.  
        self.kforce = kforce         # 1.5 kcal/mol/A² é equivalente para ~ 600 kJ/mol/nm².
        self.selpull = selpull       # Seleção dos atomos para fazer pulling.
        self.selanchor = selanchor   # Seleção dos atomos para ser restraint.
        self.targetCenter = targetCenter #! Center até onde queremos levar os átomos de pulling.

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
dcdfreq         5000
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
run                     $currenttime;     #  %s ns
""" % (self.psf, self.pdb, self.temperature, self.mdsteps, self.mdtime)
        f.write(smd)
        f.close()

    def colvars(self):
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
    targetNumSteps %s        #! Total número de steps, onde para fazer 10 A/ns.  
    outputCenters   on       #! Print o centers do atoms pulling durante a simulação. 
    outputAccumulatedWork yes #! Print o trabalho acumulado, necessário para o jarzynski.
}
""" % (self.kforce, int(self.mdsteps))
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

#-------------------------------------------------------------------#
# WELL TEMPERED METADYNAMICS                                        #
#-------------------------------------------------------------------#

class WTMetaDProtocolSol:
    def __init__(self, psf, pdb, temperature, mdtime, hill=0.01, hillfreq=500, width=1.0,
                 biasT=15, sel1="segid PROA and name CA", sel2="segid PROB and name CA", dunbind=50.0):
        self.psf = psf 
        self.pdb = pdb 
        self.temperature = temperature
        self.mdtime = mdtime 
        self.mdsteps = int((self.mdtime * 1000)/0.002) # mdtime is em nanosegundos e converte para mdsteps. 
        self.hill = hill         
        self.hillfreq = int(hillfreq)      
        self.width = width               # Este é o desvió padrão, que pode ser obtenido de rodar uma simulãcao unbias, e calcular 
                                         # o desvió padrão da variable collectiva. É uma boa regra de thumb. 
        self.biasT = biasT
        self.biasTemperature = int((self.biasT * temperature) - temperature)  # Permite obtener a temperatura para o bias definido pelo usuario. 
        self.sel1 = sel1            # No meu caso particular o sel1 pode ser PROA ou PROC. 
        self.sel2 = sel2            # Este é só PROB. 
        self.dunbind = dunbind      # Esta é a distância, que o usuario quer usar para separar as duas moléculas. 


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
dcdfreq         5000
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
#wrapAll     on          ;# Deixar em off este parâmetro para evitar erros na continuação do CV. 
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

################ WTMetaD  ##################
colvars on 
colvarsConfig wtmetad.in 

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
    set inputname md$count
    binCoordinates $inputname.restart.coor
    extendedSystem $inputname.restart.xsc
    binvelocities  $inputname.restart.vel
    colvarsInput   $inputname.restart.colvars.state
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

""" % (self.psf, self.pdb, self.temperature, self.mdsteps, self.mdtime)
        f.write(metad)
        f.close()
        
    def colvars(self):
        '''
            O colvar aquí é a distância medida entre os centros de massa de duas molẽculas. 
            Neste caso particular, é de proteína e proteína. 
        '''
        f = open("04md/wtmetad.in", "w")
        colvars = """\
colvarsTrajFrequency      500   
colvarsRestartFrequency   500  

colvar {
    name AtomDistance
    width 0.10              # Mesmo do que CHARMM-GUI and também BFEE2. Não considere lower/upperWall.
    lowerboundary xa        # O valor é zero, porque a diferencia de distanciaentre os dímeros é 0.0. 
    upperboundary xb        # O valor máximo para evaluar o PMF. 
    expandboundaries  on   


    distance {
        forceNoPBC       yes  
        group1 {
                atomsFile  P1.pdb    # PROA ou PROC. 
                atomsCol B 
                atomsColValue 1.0 
        }

        group2 { 
                atomsFile  P2.pdb  # PROB.
                atomsCol B 
                atomsColValue 1.0  
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
""" % (self.hill, self.hillfreq, self.width, self.biasTemperature) 
        f.write(colvars)
        f.close()

    def makecolvarspdb(self):
        f = open("makePDBcolvars.tcl", "w")
        script = f"""\
set psf %s 
set pdb %s 
set selp1 \"%s\"
set selp2 \"%s\"
set dunbind %s


mol new $psf
mol addfile $pdb 

set all [atomselect top \"all\"] 
$all set beta 0 
set p1 [atomselect top \"$selp1\"]
$p1 set beta 1.0
$all writepdb 04md/P1.pdb 

set all [atomselect top \"all\"]
$all set beta 0 
set p2 [atomselect top \"$selp2\"]
$p2 set beta 1.0      
$all writepdb 04md/P2.pdb 

# Calcular a distância entre as duas moléculas
set p1cm [atomselect top $selp1]
set p2cm [atomselect top $selp2]

set cm1 [measure center $p1cm]
set cm2 [measure center $p2cm]
set d [vecdist $cm1 $cm2]

# lower and upper boundaries. 
set lb [format "%%.2f" [expr $d - 1.0]]              ;# Eu subtraio -1 ou adiciono + 1 para dar um espaço extra na variável coletiva. 
set ub [format "%%.2f" [expr $d + $dunbind + 1.0]]


exec sed -i -e \"s/xa/$lb/g\" 04md/wtmetad.in
exec sed -i -e \"s/xb/$ub/g\" 04md/wtmetad.in
exec sed -i -e \"s/xc/$lb/g\" 04md/wtmetad.in
exec sed -i -e \"s/xd/$ub/g\" 04md/wtmetad.in

quit 
""" % (self.psf, self.pdb, self.sel1, self.sel2, self.dunbind) 
        f.write(script)
        f.close()
        os.system("vmd -dispdev text -e makePDBcolvars.tcl 2>&1 | tee colvars.log")
        
            



