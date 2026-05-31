import os
import subprocess
import logging
import click
from mstbx.core.Utils.Utils import UnixMessage

class ApptainerManager:
    def __init__(self, sif_name, def_file=None, sif_url=None):
        self.sif_name = sif_name
        self.def_file = def_file
        self.sif_url = sif_url
        self.uxm = UnixMessage()
        
        # User's local apptainer directory
        self.local_app_dir = os.path.join(os.getcwd(), "apptainer")
        self.sif_path = os.path.join(self.local_app_dir, self.sif_name)

    def ensure_sif(self):
        if os.path.exists(self.sif_path):
            self.uxm.message(message=f"Container found at {self.sif_path}", type="info")
            return True
        
        self.uxm.message(message=f"Container {self.sif_name} not found in ./apptainer/", type="warning")
        if not os.path.exists(self.local_app_dir):
            os.makedirs(self.local_app_dir)

        if self.sif_url:
            self.uxm.message(message=f"Attempting to pull from {self.sif_url}...", type="info")
            cmd = f"apptainer pull --name {self.sif_path} {self.sif_url}"
            if os.system(cmd) == 0:
                return True

        if self.def_file and os.path.exists(self.def_file):
            self.uxm.message(message=f"Attempting to build from {self.def_file}...", type="info")
            cmd = f"apptainer build {self.sif_path} {self.def_file}"
            if os.system(cmd) == 0:
                return True
        
        self.uxm.message(message="Failed to obtain SIF container.", type="error")
        return False

    def run(self, command, options="--nv --containall", binds=None):
        if not self.ensure_sif():
            return False
        
        bind_str = ""
        if binds:
            for host, cont in binds.items():
                bind_str += f" -B {host}:{cont}"
        
        full_cmd = f"apptainer run {options} {bind_str} {self.sif_path} {command}"
        self.uxm.message(message=f"Running: {full_cmd}", type="info")
        return os.system(full_cmd) == 0

    def cleanup(self):
        if os.path.exists(self.sif_path):
            if click.confirm(f"Do you want to delete the container at {self.sif_path}?", default=False):
                os.remove(self.sif_path)
                self.uxm.message(message="Container deleted.", type="info")
