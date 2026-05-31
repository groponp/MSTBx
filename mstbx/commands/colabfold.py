import click
import os
import glob
from mstbx.core.Utils.Apptainer import ApptainerManager
from mstbx.core.Utils.Utils import UnixMessage

@click.command()
@click.option('--input-dir', '-i', required=True, help="Directory with input FASTA files.")
@click.option('--output-dir', '-o', required=True, help="Directory to save results.")
@click.option('--sif', help="Path to ColabFold SIF file (will search in ./apptainer/ if not provided).")
@click.option('--cache', default="./colabfold_cache", help="Directory for model parameters.")
def colabfold(input_dir, output_dir, sif, cache):
    """colabfold: Run ColabFold batch prediction via Apptainer."""
    uxm = UnixMessage()
    
    sif_name = os.path.basename(sif) if sif else "colabfold.sif"
    sif_url = "docker://ghcr.io/sokrypton/colabfold:1.5.5-cuda12.2.2" # Default URL
    
    app = ApptainerManager(sif_name=sif_name, sif_url=sif_url)
    
    if not os.path.exists(cache):
        os.makedirs(cache)
    
    fasta_files = glob.glob(os.path.join(input_dir, "*.fasta")) + glob.glob(os.path.join(input_dir, "*.fa"))
    if not fasta_files:
        uxm.message(message="No FASTA files found in input directory.", type="error")
        return

    uxm.message(message=f"Found {len(fasta_files)} FASTA files. Starting ColabFold...", type="info")
    
    for fasta in fasta_files:
        basename = os.path.splitext(os.path.basename(fasta))[0]
        run_output = os.path.join(output_dir, basename)
        if not os.path.exists(run_output):
            os.makedirs(run_output)
            
        binds = {
            os.path.abspath(fasta): "/input.fasta",
            os.path.abspath(run_output): "/output",
            os.path.abspath(cache): "/cache"
        }
        
        # colabfold_batch command inside container
        cmd = "colabfold_batch /input.fasta /output --model-type auto --num-recycle 10"
        
        uxm.message(message=f"Processing {basename}...", type="info")
        app.run(command=cmd, binds=binds)
    
    uxm.message(message="ColabFold processing finished.", type="info")
    app.cleanup()
