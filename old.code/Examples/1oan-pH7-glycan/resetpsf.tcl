package require psfgen
resetpsf
# Lee el archivo PSF de entrada (formato CHARMM, ex: CHARMM-GUI)
readpsf step1_pdbreader.psf
# Asocia coordenadas do arquivo PDB
coordpdb step1_pdbreader.pdb
# Activa la opción de escribir enlaces virtuales
vpbonds 1
# Escreve o novo arquivo PSF no formato x-plor (compatível com NAMD)
writepsf x-plor reset.psf
# Escreve o novo arquivo PDB
writepdb reset.pdb
quit
