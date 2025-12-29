import subprocess
import time
from urllib.parse import urlparse
import uuid
import os

import qtau
from qtau.job import slurm, ssh
from qtau.pcs_logger import QTauComputeServiceLogger


class QTauManager:
    def __init__(self, working_directory, execution_engine):
        self.working_directory = working_directory
        self.execution_engine = execution_engine
        self.logger = QTauComputeServiceLogger(self.working_directory)
        self.scheduler_info_file=f'{self.working_directory}/scheduler'
        self.worker_config_file=f'{self.working_directory}/worker_config.json'        
        self.execution_engine = execution_engine
        self.qtau_job = None
        
    def create_worker_config_file(self):
        pass

    def get_id(self):
        return self.qtau_id

    def start_scheduler(self):
        pass

    def create_qtau(self):
        pass

    def submit_qtau(self, qtau_compute_description):
        self._setup_qtau_job(qtau_compute_description)

        try:
            
            qtau_js, qtau_jd = self._setup_qtau_saga_job(self.qtau_compute_description)
            self.qtau_job = qtau_js.create_job(qtau_jd)
            self.qtau_job.run()
            self.qtau_job_id = self.qtau_job.get_id()
            self.logger.info(f"Job submitted with id: {self.qtau_job_id} and state: {self.qtau_job.get_state()}")
            return self.qtau_job
        except Exception as ex:
            self.logger.error(f"QTau job submission failed: {str(ex)}")
            raise ex

    def _setup_qtau_job(self, qtau_compute_description):
        self.qtau_compute_description = qtau_compute_description
        self.qtau_id = self.execution_engine.name + "-" + uuid.uuid1().__str__()
        self.qtau_working_directory = os.path.join(self.working_directory, self.qtau_id)
        self.qtau_compute_description["working_directory"] = self.qtau_working_directory
        self.create_worker_config_file()
        
        try:
            self.logger.info(f"Creating working directory: {self.qtau_working_directory}")
            os.makedirs(self.qtau_working_directory)
        except Exception:
            self.logger.error(f"Failed to create working directory: {self.qtau_working_directory}")
        

        
    def wait(self):
        state = self.qtau_job.get_state().lower()        
        while state != "running" and state != "done":
            self.logger.debug(f"QTau Job {self.qtau_job_id} State {state}")            
            time.sleep(6)
            state = self.qtau_job.get_state().lower()
        

    def get_config_data(self):
        pass
                    

    def get_qtau_status(self):
        pass

    def cancel(self):
        if self.qtau_job:
            self.qtau_job.cancel()

        time.sleep(2)

    def _setup_qtau_saga_job(self, qtau_compute_description):
        resource_url = qtau_compute_description["resource"]
        url_scheme = urlparse(resource_url).scheme

        js = self._get_saga_job_service(resource_url, url_scheme)
        
        executable = self._get_qtau_saga_job_executable()
        arguments = self._get_saga_job_arguments()                
        self.logger.debug(f"Launching qtau with {executable} and arguments: {arguments}")

        jd = {"executable": executable, "arguments": arguments}
        jd.update(qtau_compute_description)

        return js, jd

    def _get_saga_job_service(self, resource_url, url_scheme):
        if url_scheme.startswith("slurm"):
            js = slurm.Service(resource_url)
        else:
            js = ssh.Service(resource_url)
        return js
    
    def _get_qtau_saga_job_executable(self):
        return "python"
        
    def _stop_existing_processes(self, process_name):
        # Find the process IDs of all running dask-scheduler processes
        try:
            result = subprocess.run(['pgrep', '-f', process_name], stdout=subprocess.PIPE, text=True)
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print(f"Stopping existing ray/dask process with PID: {pid}")
                    subprocess.run(['kill', '-9', pid])
        except Exception as e:
            print(f"Error stopping existing schedulers: {e}")

    def is_scheduler_started(self):
        return os.path.exists(os.path.join(self.working_directory, "scheduler"))
