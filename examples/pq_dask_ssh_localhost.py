import os

import pennylane as qml
from qtau.qtau_compute_service import QTauComputeService
from time import sleep

RESOURCE_URL_HPC = "ssh://localhost"
WORKING_DIRECTORY = os.path.join(os.environ["HOME"], "work")

qtau_compute_description_dask = {
    "resource": RESOURCE_URL_HPC,
    "working_directory": WORKING_DIRECTORY,
    "type": "dask",
    "number_of_nodes": 1,
    "cores_per_node": 2,
}


def start_qtau():
    pcs = QTauComputeService()
    dp = pcs.create_qtau(qtau_compute_description=qtau_compute_description_dask)
    dp.wait()
    return dp

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
    dask_qtau, dask_client = None, None

    try:
        # Start QTau
        dask_qtau = start_qtau()

        # Get Dask client details
        dask_client = dask_qtau.get_client()
        print(dask_client.scheduler_info())

        print("Start sleep 1 tasks")
        tasks = []
        for i in range(10):
            k = dask_qtau.submit_task(f"task_sleep-{i}",sleep, 1)
            tasks.append(k)

        dask_qtau.wait_tasks(tasks)
        print("Start Pennylane tasks")
        tasks = []
        for i in range(10):
            k = dask_qtau.submit_task(f"task_pennylane-{i}", pennylane_quantum_circuit)
            tasks.append(k)

        dask_qtau.wait_tasks(tasks)        
    finally:
        if dask_qtau:
            dask_qtau.cancel()
