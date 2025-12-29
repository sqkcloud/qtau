import os
import time

from qtau.qtau_compute_service import ExecutionEngine, QTauComputeService
from time import sleep

RESOURCE_URL_HPC = "ssh://localhost"
WORKING_DIRECTORY = os.path.join(os.environ["HOME"], "work")

qtau_compute_description_ray = {
    "resource": RESOURCE_URL_HPC,
    "working_directory": WORKING_DIRECTORY,
    "type": "ray",
    "number_of_nodes": 1,
    "cores_per_node": 40,
}


def start_qtau():
    pcs = QTauComputeService(execution_engine=ExecutionEngine.RAY, working_directory=WORKING_DIRECTORY)
    pcs.create_qtau(qtau_compute_description=qtau_compute_description_ray)
    return pcs

def sleep(timeSecs):
    time.sleep(timeSecs)

if __name__ == "__main__":
    pcs = None
    mpi_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mpi_script.py")
    try:
        # Start QTau
        pcs = start_qtau()        
        tasks = []
        start_time = time.time()
        for i in range(3):            
            k = pcs.submit_mpi_task(mpi_script_path, 4, "foo", "bar" , resources={'num_cpus': 1, 'num_gpus': 0, 'memory': None})
            tasks.append(k)                    
        pcs.wait_tasks(tasks)
        end_time = time.time()
        print(f"Execution time: {end_time-start_time}")
    finally:
        if pcs:
            pcs.cancel()