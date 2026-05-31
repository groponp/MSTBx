#python $MSTBx/GenSol.py  --psf step1_pdbreader.psf --pdb step1_pdbreader.pdb --salt 0.150 --ofile mol
python $MSTBx/GenWTMetaDSolConfg.py --psf 01build/mol.psf --pdb 01build/mol.pdb --hill 0.01 --hillfreq 500 --width 1.0 --biasT 15\
    --sel1 "segid PROA and name CA" --sel2 "segid PROB and name CA" --target_distance 50.0 --temperature 310 --mdtime 2000


