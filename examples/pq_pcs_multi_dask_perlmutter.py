import os

import pennylane as qml
from qtau.qtau_compute_service import ExecutionEngine, QTauComputeService
from time import sleep

RESOURCE_URL = "slurm://localhost"
WORKING_DIRECTORY = os.path.join(os.environ["HOME"], "work")

qtau_compute_description = {
    "resource": RESOURCE_URL,
    "working_directory": WORKING_DIRECTORY,
    "type": "dask",
    "number_of_nodes": 1,
    "cores_per_node": 10,
    "queue": "premium",
    "walltime": 60,
    "project": "m4408",
    "scheduler_script_commands": ["#SBATCH --constraint=cpu"],
}


def start_pcs():
    pcs = QTauComputeService(ExecutionEngine.DASK, WORKING_DIRECTORY)
    for i in range(2):
        qtau_compute_description["name"] = f"qtau-{i}"
        pcs.create_qtau(qtau_compute_description=qtau_compute_description)
    return pcs

def pennylane_quantum_circuit():
    wires = 4
    layers = 1
    dev = qml.device('default.qubit', wires=wires, shots=None)

    @qml.qnode(dev)
    def circuit(parameters):
        qml.StronglyEntanglingLayers(weights=parameters, wires=range(wires))
        return [qml.expval(qml.PauliZ(i)) for i in range(wires)]

    shape = qml.StronglyEntanglingLayers.shape(n_layers=layers, n_wires=wires)
    weights = qml.numpy.random.random(size=shape)
    return circuit(weights)


if __name__ == "__main__":
    pcs = None
    try:
        # Start QTaus
        pcs = start_pcs()

        qtaus = pcs.get_qtaus()
        
        # print qtau names
        for pname in qtaus:
            print(pname)

        # Submit tasks to pcs
        tasks = []
        for i in range(10):
            k = pcs.submit_task(pennylane_quantum_circuit, task_name = f"task_pennylane-{i}" )
            tasks.append(k)

        for i in range(10):
            k = pcs.submit_task(pennylane_quantum_circuit, task_name = f"task_{qtaus[0]}_pennylane-{i}", qtau=qtaus[0])
            tasks.append(k)


        pcs.wait_tasks(tasks)
    finally:
        if pcs:
            pcs.cancel()
        