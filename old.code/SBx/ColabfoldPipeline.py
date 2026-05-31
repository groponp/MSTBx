#!/usr/bin/env python3
# ColabFoldPipeline.py
"""
Main wrapper script to run colabfold_batch via an Apptainer container 
for multiple FASTA files from a specified directory.
It handles the setup of the ColabFold environment (SIF and model parameters)
if they are not already present.
Applies default parameters to colabfold_batch, which can be 
overridden by user-provided command-line arguments.
All other unrecognized arguments are passed directly to colabfold_batch.

Written by: Ropon-Palacios G., assisted by Gemini 2.5Pro.
__version__ = 0.4 
"""

import os
import sys
import subprocess
import argparse
import glob
import shutil
import logging
# import json # No es necesario si no hay reporte CSV complejo
# import csv  # No es necesario si no hay reporte CSV complejo
from typing import List, Dict, Optional, Any 
import re

# --- Global Configuration ---
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(SCRIPT_NAME)
APPTAINER_EXECUTABLE = "apptainer" 

DEFAULT_COLABFOLD_OPTS_WITH_VALUES = {
    "--model-type": "auto",
    "--max-msa": "1024:2048", 
    "--num-recycle": "10",
    "--rank": "plddt",
    "--num-models": "5",
    "--stop-at-score": "90",
    "--num-ensemble": "8", 
    "--num-relax": "5"    
}
DEFAULT_COLABFOLD_FLAGS = [ 
    "--use-gpu-relax",    
    "--amber",             
    "--templates"          
]

class LoggerConfigurator:
    @staticmethod
    def setup():
        logger.setLevel(logging.DEBUG)
        log_filename = f"{SCRIPT_NAME}.log"
        log_file_msg_path = f"'{log_filename}' (log file potentially not writable)"
        try:
            fh = logging.FileHandler(log_filename, mode='w')
            fh.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '[%(levelname)-8s %(asctime)s %(name)s] [%(funcName)s:%(lineno)d] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')
            fh.setFormatter(file_formatter)
            if not any(isinstance(h, logging.FileHandler) for h in logger.handlers): logger.addHandler(fh)
            log_file_msg_path = os.path.abspath(log_filename)
        except Exception as e:
            sys.stderr.write(f"WARNING: Could not configure logging to file '{log_filename}'. Error: {e}\n")
            if not logger.handlers:
                ch_fallback = logging.StreamHandler(sys.stdout); ch_fallback.setLevel(logging.INFO)
                console_formatter_fallback = logging.Formatter('[%(levelname)-8s %(asctime)s %(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
                ch_fallback.setFormatter(console_formatter_fallback); logger.addHandler(ch_fallback)
        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            ch = logging.StreamHandler(sys.stdout); ch.setLevel(logging.INFO)
            console_formatter = logging.Formatter('[%(levelname)-8s %(asctime)s %(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            ch.setFormatter(console_formatter); logger.addHandler(ch)
        # logger.info(f"Logging configured. Detailed logs may be saved to {log_file_msg_path}.") # Movido a main

class FileSystemUtils:
    @staticmethod
    def sanitize_path_component(text: str) -> str:
        s = str(text).replace(" ", "_"); s = re.sub(r'[^\w.-]', '_', s)
        return re.sub(r'__+', '_', s).strip('_')

    @staticmethod
    def find_fasta_files(input_dir: str) -> list:
        patterns = ['*.fasta', '*.fas', '*.fa', '*.fna']
        files = [f for p in patterns for f in glob.glob(os.path.join(input_dir, p))]
        logger.debug(f"Found {len(files)} FASTA files in '{input_dir}' using patterns: {patterns}.")
        return files

    @staticmethod
    def ensure_dir_exists(dir_path: str) -> bool:
        try: os.makedirs(dir_path, exist_ok=True); logger.debug(f"Directory ensured: {dir_path}"); return True
        except OSError as e: logger.error(f"Could not create directory '{dir_path}': {e}"); return False

class EnvironmentSetupService:
    def __init__(self, sif_path: str, cache_dir: str, sif_url: str, apptainer_exec: str):
        self.sif_path = os.path.abspath(sif_path)
        self.cache_dir = os.path.abspath(cache_dir)
        self.params_indicator_dir = os.path.join(self.cache_dir, "colabfold", "params") 
        self.sif_url = sif_url
        self.apptainer_executable = apptainer_exec
        self.fs_utils = FileSystemUtils()

    def _run_command(self, cmd_list: list, cwd: Optional[str] = None, check_return_code=True) -> bool:
        command_str = ' '.join(cmd_list)
        logger.info(f"Executing system command: {command_str}")
        try:
            process = subprocess.Popen(cmd_list, stdout=sys.stdout, stderr=sys.stderr, cwd=cwd)
            process.wait()
            if check_return_code and process.returncode != 0:
                logger.error(f"Command failed with return code {process.returncode}: {command_str}")
                return False
            logger.debug(f"Command completed successfully: {command_str}")
            return True
        except FileNotFoundError:
            logger.critical(f"Executable '{cmd_list[0]}' not found. Ensure it is installed and in PATH.")
            return False 
        except Exception as e:
            logger.error(f"Exception during command execution '{command_str}': {e}")
            return False

    def setup_colabfold_environment(self):
        logger.info("Checking LocalColabFold environment (SIF and model parameters)...")
        sif_dir = os.path.dirname(self.sif_path)
        if not self.fs_utils.ensure_dir_exists(sif_dir): return False
        if not self.fs_utils.ensure_dir_exists(self.cache_dir): return False

        if not os.path.isfile(self.sif_path):
            logger.info(f"SIF file not found at '{self.sif_path}'. Attempting to download from '{self.sif_url}'...")
            pull_cmd = [self.apptainer_executable, "pull", "--name", self.sif_path, self.sif_url]
            if not self._run_command(pull_cmd):
                logger.critical(f"Failed to download SIF image. Please ensure '{self.apptainer_executable}' is installed, '{self.sif_url}' is correct, and you have write permissions to '{sif_dir}'.")
                return False
            logger.info(f"SIF image downloaded to '{self.sif_path}'.")
        else:
            logger.info(f"SIF file found at '{self.sif_path}'.")

        logger.info("Performing initial GPU check inside the container (if SIF exists)...")
        if os.path.isfile(self.sif_path):
            gpu_check_cmd = [self.apptainer_executable, "exec", "--nv", self.sif_path, "nvidia-smi"]
            self._run_command(gpu_check_cmd, check_return_code=False)
        else:
            logger.warning("SIF file not available for GPU check.")

        logger.info(f"Ensuring ColabFold model parameters are downloaded/updated in host cache directory: {self.cache_dir}")
        download_weights_cmd = [self.apptainer_executable, "run", "--nv", "--containall",
                                "-B", f"{self.cache_dir}:/cache:rw", self.sif_path,
                                "python", "-m", "colabfold.download"]
        if not self._run_command(download_weights_cmd):
            logger.warning("Command 'python -m colabfold.download' for parameters failed or returned non-zero. ColabFold might attempt to download them on first use if internet is available inside the container, or it might fail if parameters are strictly required beforehand.")
        
        if os.path.isdir(self.params_indicator_dir):
             logger.info(f"Model parameters indicator directory ('{self.params_indicator_dir}') found in cache.")
        else:
             logger.warning(f"Model parameter indicator directory ('{self.params_indicator_dir}') NOT found after download attempt. This could lead to issues if parameters are not downloaded on demand by ColabFold.")
        logger.info("ColabFold environment setup check completed.")
        return True

class ArgumentService:
    def __init__(self, script_name: str, default_opts: dict, default_flags: list):
        self.script_name = script_name
        self.default_opts_with_values = default_opts
        self.default_flags = default_flags
        self.parser = self._create_parser()

    def _get_default_args_help_string(self) -> str:
        display_list = [flag for flag in self.default_flags] + [f"{k} {v}" for k, v in self.default_opts_with_values.items()]
        base_cmd = f"  {APPTAINER_EXECUTABLE} run --nv -B \"$(pwd)/cache\":/cache:rw <sif_file> colabfold_batch"
        lines = [base_cmd]
        current_line_length = len(lines[0]) 
        for item in display_list:
            if (lines[-1] == base_cmd and current_line_length + len(item) + 1 <= 80) or \
               (lines[-1] != base_cmd and current_line_length + len(item) + 1 <= 80 - 4):
                lines[-1] += f" {item}" 
                current_line_length += len(item) + 1
            else:
                lines.append("    " + item) 
                current_line_length = len("    " + item)
        lines.append("    <input.fasta> <results_dir/>") 
        return " \\\n".join(lines) 

    def _create_parser(self) -> argparse.ArgumentParser:
        default_args_help = self._get_default_args_help_string()
        parser = argparse.ArgumentParser(
            prog=self.script_name,
            description=f"{self.script_name}: Sets up LocalColabFold environment (SIF, weights) if needed, then runs colabfold_batch via Apptainer for multiple FASTA files, with default settings.",
            epilog=(
                "-----------------------------------------------------------------------------------\n"
                "DEFAULT PARAMETERS FOR 'colabfold_batch' (applied by this wrapper if not overridden):\n"
                "  (Example command structure with defaults applied, actual SIF path and cache dir will be used from args)\n"
                f"{default_args_help}\n\n"
                "Any arguments provided to this script not listed under 'Wrapper Arguments' or 'Utility Arguments'\n"
                "will be passed directly to 'colabfold_batch'.\n"
                "If you provide an option that is also a default, your value will override the default.\n\n"
                "To see the full help for 'colabfold_batch' itself (via the --show-colabfold-help flag):\n"
                f"  python {self.script_name}.py --show-colabfold-help --sif-path /path/to/colabfold.sif\n"
                "Or manually within a shell:\n"
                f"  {APPTAINER_EXECUTABLE} run --nv /path/to/your/colabfold.sif colabfold_batch --help\n"
                "-----------------------------------------------------------------------------------"
            ),
            formatter_class=argparse.RawTextHelpFormatter
        )
        grp_main = parser.add_argument_group(f"Main Wrapper Arguments ({self.script_name})")
        grp_main.add_argument('--input-fasta-dir', metavar='FASTA_DIR', help="Directory containing input FASTA files (required for processing runs).")
        grp_main.add_argument('--output-dir', metavar='OUTPUT_DIR', help="Main directory where results will be saved (a subfolder per FASTA will be created; required for processing runs).")
        grp_setup = parser.add_argument_group("ColabFold Environment Setup Arguments")
        grp_setup.add_argument('--sif-path', default=os.path.join(os.getcwd(), "localcolabfold", "colabfold_1.5.5-cuda12.2.2.sif"), metavar='SIF_FILE', help="Path to the LocalColabFold Apptainer SIF file. (Default: ./localcolabfold/colabfold_1.5.5-cuda12.2.2.sif)")
        grp_setup.add_argument('--sif-url', default="docker://ghcr.io/sokrypton/colabfold:1.5.5-cuda12.2.2", metavar='URL', help="URL to pull SIF image if not found locally. (Default: docker://ghcr.io/sokrypton/colabfold:1.5.5-cuda12.2.2)")
        grp_setup.add_argument('--cache-dir', default=os.path.join(os.getcwd(), "localcolabfold", "cache"), metavar='CACHE_DIR', help="Directory for ColabFold model parameters. (Default: ./localcolabfold/cache)")
        grp_setup.add_argument('--skip-setup-checks', action='store_true', help="Skip SIF and parameters download checks.")
        
        # Argumento --csv-report-name y la sección de Reporting eliminados
        # grp_runtime = parser.add_argument_group("Reporting Arguments")
        # grp_runtime.add_argument('--csv-report-name', default="colabfold_summary_metrics.csv", metavar='CSV_NAME', help="Name of the CSV file for the metrics report (default: colabfold_summary_metrics.csv).")

        # Argumento --databases-dir, movido a un grupo más general si es necesario o mantenido como argumento del wrapper
        parser.add_argument('--databases-dir', default=None, metavar='DB_DIR', 
                            help="Optional: Directory with local ColabFold databases (e.g., PDB70) to mount at /databases (ro).")

        grp_util = parser.add_argument_group(f"Utility Arguments ({self.script_name})")
        grp_util.add_argument('--show-colabfold-help', action='store_true', help="Display 'colabfold_batch --help' from the SIF and exit. Uses --sif-path.")
        return parser

    def parse_cli_args(self, cli_args_list=None):
        if cli_args_list is None: cli_args_list = sys.argv[1:]
        wrapper_args, passthrough_args = self.parser.parse_known_args(cli_args_list)
        logger.debug(f"Wrapper specific arguments parsed: {wrapper_args}")
        logger.debug(f"User passthrough arguments for colabfold_batch: {passthrough_args}")
        return wrapper_args, passthrough_args

    def get_effective_colabfold_args(self, user_passthrough_args: list) -> list:
        effective_dict = {**self.default_opts_with_values}
        for flag in self.default_flags: effective_dict[flag] = True 
        idx = 0
        while idx < len(user_passthrough_args):
            arg = user_passthrough_args[idx]
            if arg.startswith("--"):
                if (idx + 1 < len(user_passthrough_args) and not user_passthrough_args[idx+1].startswith("--")):
                    effective_dict[arg] = user_passthrough_args[idx+1]; idx += 2
                else: effective_dict[arg] = True; idx += 1
            else: logger.warning(f"Ignoring unexpected passthrough argument: {arg}"); idx += 1
        final_list = [str(item) for k, v in effective_dict.items() for item in ([k] if v is True else [k, v])]
        logger.info(f"Effective arguments for colabfold_batch: {' '.join(final_list)}")
        return final_list

class ApptainerJobRunner:
    def __init__(self, sif_path: str, apptainer_executable: str = APPTAINER_EXECUTABLE):
        self.sif_path = os.path.abspath(sif_path)
        self.apptainer_executable = apptainer_executable

    def run_colabfold_help(self):
        logger.info(f"Attempting to display 'colabfold_batch --help' from container: {self.sif_path}")
        cmd = [self.apptainer_executable, "run", "--nv", "--containall", self.sif_path, "colabfold_batch", "--help"]
        logger.info(f"Executing: {' '.join(cmd)}")
        try:
            process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr); process.wait()
        except Exception as e: logger.error(f"Failed to execute 'colabfold_batch --help' in container: {e}")

    def run_colabfold_prediction(self, input_fasta_host_path: str, colabfold_output_dir_host_path: str, 
                                 colabfold_args: list, cache_dir_host_path: str, 
                                 databases_dir_host_path: Optional[str] = None):
        fasta_filename = os.path.basename(input_fasta_host_path)
        logger.info(f"--- Starting ColabFold prediction for: {fasta_filename} ---")
        logger.debug(f"  Output will be in: {colabfold_output_dir_host_path}")
        binds = [f"--bind={os.path.abspath(input_fasta_host_path)}:/input.fasta:ro",
                 f"--bind={os.path.abspath(colabfold_output_dir_host_path)}:/output",
                 f"--bind={os.path.abspath(cache_dir_host_path)}:/cache:rw"]
        if databases_dir_host_path and os.path.isdir(databases_dir_host_path):
            binds.append(f"--bind={os.path.abspath(databases_dir_host_path)}:/databases:ro")
            logger.debug(f"  Mounting local databases: {databases_dir_host_path}")
        elif databases_dir_host_path: # Path was given but not a directory
            logger.warning(f"  Databases directory '{databases_dir_host_path}' specified but not found or not a directory. Will not be mounted.")
        
        cmd_list = [self.apptainer_executable, "run", "--nv", "--containall"] + binds + \
                   [self.sif_path, "colabfold_batch", "/input.fasta", "/output"] + colabfold_args
        
        logger.info(f"Full command for {fasta_filename}: {' '.join(cmd_list)}")
        try:
            process = subprocess.Popen(cmd_list, stdout=sys.stdout, stderr=sys.stderr)
            process.wait()
            if process.returncode == 0:
                logger.info(f"--- Successfully completed ColabFold for: {fasta_filename} ---")
            else:
                logger.error(f"--- ColabFold FAILED for: {fasta_filename}. Return code: {process.returncode} ---")
        except Exception as e:
            logger.error(f"--- Unexpected exception during ColabFold for {fasta_filename}: {e} ---")

class ColabFoldPipelineOrchestrator:
    def __init__(self, wrapper_args: argparse.Namespace, colabfold_effective_args: list):
        self.args = wrapper_args
        self.colabfold_effective_args = colabfold_effective_args
        self.fs_utils = FileSystemUtils()
        
        if shutil.which(APPTAINER_EXECUTABLE) is None:
            logger.critical(f"'{APPTAINER_EXECUTABLE}' command not found. Is Apptainer/Singularity installed and in PATH?")
            sys.exit(1)
            
        self.env_setup_service = EnvironmentSetupService(
            sif_path=self.args.sif_path, cache_dir=self.args.cache_dir, 
            sif_url=self.args.sif_url, apptainer_exec=APPTAINER_EXECUTABLE
        )
        self.apptainer_job_runner = ApptainerJobRunner(self.args.sif_path, APPTAINER_EXECUTABLE)

    def setup_environment_if_needed(self):
        if not self.args.skip_setup_checks:
            if not self.env_setup_service.setup_colabfold_environment():
                logger.critical("Failed to setup ColabFold environment (SIF/parameters). Exiting."); sys.exit(1)
        else:
            logger.info("Skipping SIF and parameters download checks as per --skip-setup-checks.")
            if not os.path.isfile(self.args.sif_path): 
                logger.critical(f"SIF file '{self.args.sif_path}' not found, and --skip-setup-checks was used."); sys.exit(1)
            if not os.path.isdir(self.args.cache_dir) or not os.path.isdir(os.path.join(self.args.cache_dir, "colabfold","params")):
                 logger.warning(f"Cache directory '{self.args.cache_dir}' or 'colabfold/params' subdirectory seems incomplete, and --skip-setup-checks was used.")
            logger.info(f"Using existing SIF: {self.args.sif_path} and cache: {self.args.cache_dir}")

    def _validate_processing_args(self):
        if not self.args.input_fasta_dir: logger.critical("--input-fasta-dir is required."); sys.exit(1)
        if not self.args.output_dir: logger.critical("--output-dir is required."); sys.exit(1)
        if not os.path.isdir(self.args.input_fasta_dir): logger.critical(f"Input FASTA directory does not exist: {self.args.input_fasta_dir}"); sys.exit(1)
        if not self.fs_utils.ensure_dir_exists(self.args.output_dir): logger.critical(f"Failed to create main output directory: {self.args.output_dir}"); sys.exit(1)

    def run_pipeline(self): 
        self._validate_processing_args()
        fasta_files = self.fs_utils.find_fasta_files(self.args.input_fasta_dir)
        if not fasta_files: 
            logger.warning(f"No FASTA files found in: {self.args.input_fasta_dir}. Nothing to process.")
            return
        
        logger.info(f"Found {len(fasta_files)} FASTA files to process with ColabFold.")
        for fasta_file_path in fasta_files:
            fasta_basename = os.path.splitext(os.path.basename(fasta_file_path))[0]
            sanitized_basename = self.fs_utils.sanitize_path_component(fasta_basename)
            colabfold_run_output_dir = os.path.join(self.args.output_dir, sanitized_basename) 
            if not self.fs_utils.ensure_dir_exists(colabfold_run_output_dir):
                logger.error(f"Could not create output directory '{colabfold_run_output_dir}' for {os.path.basename(fasta_file_path)}. Skipping this FASTA."); continue
            
            self.apptainer_job_runner.run_colabfold_prediction(
                input_fasta_host_path=fasta_file_path, 
                colabfold_output_dir_host_path=colabfold_run_output_dir,
                colabfold_args=self.colabfold_effective_args, 
                cache_dir_host_path=self.args.cache_dir,
                # --- USO CORREGIDO DE getattr ---
                databases_dir_host_path=getattr(self.args, 'databases_dir', None)
            )
        logger.info(f"Attempted processing for all {len(fasta_files)} FASTA file(s) found.")
    
    # La funcionalidad de generar reporte CSV ha sido eliminada.

def main():
    LoggerConfigurator.setup() 
    logger.info(f"Starting {SCRIPT_NAME} (ColabFold Pipeline Orchestrator)...") 

    arg_service = ArgumentService(SCRIPT_NAME, DEFAULT_COLABFOLD_OPTS_WITH_VALUES, DEFAULT_COLABFOLD_FLAGS)
    wrapper_args, user_passthrough_args = arg_service.parse_cli_args()

    if shutil.which(APPTAINER_EXECUTABLE) is None:
        logger.critical(f"'{APPTAINER_EXECUTABLE}' command not found. Is Apptainer/Singularity installed and in PATH? Exiting."); sys.exit(1)

    if wrapper_args.show_colabfold_help:
        if not wrapper_args.sif_path: logger.error(f"--sif-path is required for --show-colabfold-help."); sys.exit(1)
        
        sif_path_for_help = os.path.abspath(wrapper_args.sif_path) # Usar ruta absoluta
        cache_dir_for_setup = os.path.abspath(wrapper_args.cache_dir) # Usar ruta absoluta

        env_setup_for_help = EnvironmentSetupService(sif_path_for_help, cache_dir_for_setup, wrapper_args.sif_url, APPTAINER_EXECUTABLE)
        if not os.path.isfile(sif_path_for_help) and not wrapper_args.skip_setup_checks:
            logger.info("SIF file for --show-colabfold-help not found. Attempting setup...")
            if not env_setup_for_help.setup_colabfold_environment(): 
                logger.critical("SIF setup failed. Cannot show ColabFold help."); sys.exit(1)
        
        if not os.path.isfile(sif_path_for_help): # Comprobar de nuevo después del intento de setup
             logger.critical(f"Container SIF file still not found: {sif_path_for_help}."); sys.exit(1)
            
        job_runner_for_help = ApptainerJobRunner(sif_path_for_help, APPTAINER_EXECUTABLE)
        job_runner_for_help.run_colabfold_help(); sys.exit(0)

    if not wrapper_args.input_fasta_dir: logger.critical("--input-fasta-dir is required for ColabFold runs."); arg_service.parser.print_help(); sys.exit(1)
    if not wrapper_args.output_dir: logger.critical("--output-dir is required for ColabFold runs."); arg_service.parser.print_help(); sys.exit(1)
    
    effective_colabfold_args = arg_service.get_effective_colabfold_args(user_passthrough_args)
    orchestrator = ColabFoldPipelineOrchestrator(wrapper_args, effective_colabfold_args)
    orchestrator.setup_environment_if_needed()
    orchestrator.run_pipeline()
    
    logger.info(f"All ColabFold processing tasks initiated. Check console output and individual ColabFold logs for completion status. Detailed script logs in '{SCRIPT_NAME}.log'.")

if __name__ == "__main__":
    main()
