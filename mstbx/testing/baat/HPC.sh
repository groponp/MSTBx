#SBATCH --job-name ubiquitin
#SBATCH -N1 --ntasks-per-node=32
#SBATCH --cpus-per-task=1
#SBATCH --gpus-per-node=4
#SBATCH --time=24:00:00
#SBATCH -A EUHPC_R01_130
#SBATCH --partition=boost_usr_prod
#SBATCH --mail-type=ALL
#SBATCH --mail-user=georcki.ropon@unesp.br
  
module load profile/lifesc
module load namd/2.14--gcc--11.3.0-cuda-11.8
export OMP_NUM_THREADS=1
 
# NAMD3 stable
namd3=/leonardo_scratch/large/userexternal/groponpa/NAMD_3.0_Linux-x86_64-multicore-CUDA
run=0
# Running 15 ns of equilibration in total
namd2 +p 32  +idlepoll +isomalloc_sync +setcpuaffinity +devices 0,1,2,3 02nvt/nvt.confg > 02nvt/nvt.out
namd2 +p 32  +idlepoll +isomalloc_sync +setcpuaffinity +devices 0,1,2,3 03npt/npt.confg > 03npt/npt.out
# Running 50 ns of production in NPT 
${namd3}/namd3 +p 16 --GPUresident on  +setcpuaffinity +devices 0,1,2,3  04md/md.confg > 04md/md${run}.out

