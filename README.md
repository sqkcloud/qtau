# QTau

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)

**QTau** (Quantum Task Automation Utility) is a Quantum-HPC middleware framework designed to address the challenges of integrating quantum and classical computing resources. It provides a unified interface for managing heterogeneous resources, including diverse Quantum Processing Unit (QPU) modalities and various integration types with classical HPC systems.

## Features

- **Multi-Engine Support**: Pluggable architecture supporting both [Dask](https://www.dask.org/) and [Ray](https://www.ray.io/) distributed computing backends
- **HPC Cluster Integration**: Native support for SLURM job schedulers and SSH-based remote execution
- **Quantum Framework Compatibility**: Seamless integration with [PennyLane](https://pennylane.ai/) and [Qiskit](https://qiskit.org/)
- **Task Metrics & Monitoring**: Automatic performance tracking with detailed timing breakdowns
- **Scalable Architecture**: From single-node development to multi-node HPC deployments

## Requirements

- Python 3.8+
- Anaconda or Miniconda (recommended)
- SLURM cluster access (for HPC deployments)
- Password-less SSH authentication configured (e.g., using `sshproxy` on Perlmutter)

## Installation

Requirement (in case a manual installation is required):

### Using pip

    pip install -r requirements.txt

To install QTau type:

    python setup.py install

## Usage Examples

### Example 1: Basic Task Execution with Dask

```python
import os
from qtau.qtau_compute_service import QTauComputeService
from qtau.qtau_enums_exceptions import ExecutionEngine

WORKING_DIRECTORY = os.path.join(os.environ["HOME"], "work")

# Define qtau configuration
qtau_description = {
    "resource": "ssh://localhost",
    "number_of_nodes": 2,
    "cores_per_node": 4,
}

# Initialize QTauComputeService with Dask backend
pcs = QTauComputeService(ExecutionEngine.DASK, WORKING_DIRECTORY)
pcs.create_qtau(qtau_compute_description=qtau_description)

# Define a simple task
def compute_square(x):
    return x ** 2

try:
    # Submit multiple tasks
    tasks = [pcs.submit_task(compute_square, i) for i in range(10)]

    # Wait for all tasks to complete
    pcs.wait_tasks(tasks)

    # Retrieve results
    results = pcs.get_results(tasks)
    print(results)  # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
finally:
    pcs.cancel()
```

### Example 2: Using Ray Backend with Resource Specifications

```python
import os
from qtau.qtau_compute_service import QTauComputeService
from qtau.qtau_enums_exceptions import ExecutionEngine

WORKING_DIRECTORY = os.path.join(os.environ["HOME"], "work")

qtau_description = {
    "resource": "ssh://localhost",
    "number_of_nodes": 2,
    "cores_per_node": 8,
}

# Initialize with Ray execution engine
pcs = QTauComputeService(
    execution_engine=ExecutionEngine.RAY,
    working_directory=WORKING_DIRECTORY
)
pcs.create_qtau(qtau_compute_description=qtau_description)

def heavy_computation(data):
    # Simulate CPU-intensive task
    return sum(x ** 2 for x in range(data))

try:
    # Submit tasks with specific resource requirements
    tasks = []
    for i in range(10):
        task = pcs.submit_task(
            heavy_computation,
            i * 1000,
            resources={'num_cpus': 1, 'num_gpus': 0, 'memory': None}
        )
        tasks.append(task)

    pcs.wait_tasks(tasks)
    results = pcs.get_results(tasks)
    print(results)
finally:
    pcs.cancel()
```

### Example 3: Quantum Circuit Execution with PennyLane

```python
import os
import pennylane as qml
from qtau.qtau_compute_service import QTauComputeService
from qtau.qtau_enums_exceptions import ExecutionEngine

WORKING_DIRECTORY = os.path.join(os.environ["HOME"], "work")

qtau_description = {
    "resource": "ssh://localhost",
    "number_of_nodes": 2,
    "cores_per_node": 10,
}

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

# Initialize service
pcs = QTauComputeService(ExecutionEngine.DASK, WORKING_DIRECTORY)
pcs.create_qtau(qtau_compute_description=qtau_description)

try:
    # Submit quantum circuit tasks with custom names
    tasks = []
    for i in range(10):
        task = pcs.submit_task(
            pennylane_quantum_circuit,
            task_name=f"quantum_task_{i}"
        )
        tasks.append(task)

    pcs.wait_tasks(tasks)
    results = pcs.get_results(tasks)
    print(f"Quantum circuit results: {results}")
finally:
    pcs.cancel()
```

### Example 4: Multi-QTau Deployment

```python
import os
from qtau.qtau_compute_service import QTauComputeService
from qtau.qtau_enums_exceptions import ExecutionEngine

WORKING_DIRECTORY = os.path.join(os.environ["HOME"], "work")

qtau_description = {
    "resource": "ssh://localhost",
    "number_of_nodes": 2,
    "cores_per_node": 10,
}

def process_data(x):
    return x * 2

# Initialize service
pcs = QTauComputeService(ExecutionEngine.DASK, WORKING_DIRECTORY)

# Create multiple qtaus
for i in range(2):
    qtau_description["name"] = f"qtau-{i}"
    pcs.create_qtau(qtau_compute_description=qtau_description)

try:
    # Get list of available qtaus
    qtaus = pcs.get_qtaus()
    print(f"Available qtaus: {qtaus}")

    tasks = []

    # Submit tasks to any available qtau
    for i in range(10):
        task = pcs.submit_task(process_data, i, task_name=f"general_task_{i}")
        tasks.append(task)

    # Submit tasks to a specific qtau
    for i in range(10):
        task = pcs.submit_task(
            process_data,
            i,
            task_name=f"qtau0_task_{i}",
            qtau=qtaus[0]  # Route to specific qtau
        )
        tasks.append(task)

    pcs.wait_tasks(tasks)
    results = pcs.get_results(tasks)
    print(results)
finally:
    pcs.cancel()
```

### Example 5: SLURM Cluster Deployment (HPC)

```python
import os
from qtau.qtau_compute_service import QTauComputeService
from qtau.qtau_enums_exceptions import ExecutionEngine

WORKING_DIRECTORY = os.path.join(os.environ["HOME"], "work")

# SLURM configuration for HPC cluster
qtau_description = {
    "resource": "slurm://localhost",
    "working_directory": WORKING_DIRECTORY,
    "number_of_nodes": 4,
    "cores_per_node": 24,
    "gpus_per_node": 4,
    "queue": "debug",
    "walltime": 30,  # minutes
    "project": "your_project_id",
    "conda_environment": "/path/to/conda/env",
    "scheduler_script_commands": [
        "#SBATCH --constraint=gpu",
        "#SBATCH --gpus-per-task=1",
        "#SBATCH --ntasks-per-node=4",
        "#SBATCH --gpu-bind=none"
    ]
}

pcs = QTauComputeService(
    execution_engine=ExecutionEngine.RAY,
    working_directory=WORKING_DIRECTORY
)

qtau = pcs.create_qtau(qtau_compute_description=qtau_description)
qtau.wait()  # Wait for SLURM job to start

try:
    # Submit GPU-accelerated tasks
    tasks = []
    for i in range(10):
        task = pcs.submit_task(
            your_gpu_function,
            i,
            resources={'num_cpus': 1, 'num_gpus': 1, 'memory': None}
        )
        tasks.append(task)

    pcs.wait_tasks(tasks)
    results = pcs.get_results(tasks)
finally:
    pcs.cancel()
```

### Example 6: MPI Task Execution

```python
import os
from qtau.qtau_compute_service import QTauComputeService
from qtau.qtau_enums_exceptions import ExecutionEngine

WORKING_DIRECTORY = os.path.join(os.environ["HOME"], "work")

pcs = QTauComputeService(ExecutionEngine.RAY, WORKING_DIRECTORY)
pcs.create_qtau(qtau_compute_description={
    "resource": "slurm://localhost",
    "number_of_nodes": 4,
    "cores_per_node": 32,
})

try:
    # Submit MPI task
    task = pcs.submit_mpi_task(
        script_path="/path/to/mpi_script.py",
        num_procs=128,
        "arg1", "arg2"  # Additional arguments
    )

    pcs.wait_tasks([task])
    stdout, stderr = pcs.get_results([task])[0]
    print(stdout)
finally:
    pcs.cancel()
```

### Example 7: Using the Task Decorator

```python
import os
from qtau.qtau_compute_service import QTauComputeService
from qtau.qtau_enums_exceptions import ExecutionEngine

WORKING_DIRECTORY = os.path.join(os.environ["HOME"], "work")

pcs = QTauComputeService(ExecutionEngine.DASK, WORKING_DIRECTORY)
pcs.create_qtau(qtau_compute_description={
    "resource": "ssh://localhost",
    "number_of_nodes": 2,
    "cores_per_node": 4,
})

# Use the task decorator for automatic submission
@pcs.task
def distributed_function(x, y):
    return x + y

try:
    # Tasks are automatically submitted when called
    future = distributed_function(10, 20)
    result = future.result()
    print(f"Result: {result}")  # Result: 30
finally:
    pcs.cancel()
```

### Example 8: Accessing the Native Client

```python
import os
import ray
from qtau.qtau_compute_service import QTauComputeService
from qtau.qtau_enums_exceptions import ExecutionEngine

WORKING_DIRECTORY = os.path.join(os.environ["HOME"], "work")

pcs = QTauComputeService(ExecutionEngine.RAY, WORKING_DIRECTORY)
pcs.create_qtau(qtau_compute_description={
    "resource": "ssh://localhost",
    "number_of_nodes": 2,
    "cores_per_node": 4,
})

def square(x):
    return x ** 2

try:
    # Get the native Ray client for advanced operations
    ray_client = pcs.get_client()

    with ray_client:
        # Use Ray API directly
        results = ray.get([ray.remote(square).remote(i) for i in range(10)])
        print(results)
finally:
    pcs.cancel()
```

## Configuration Reference

### QTau Description Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `resource` | Resource URL for job submission | `ssh://localhost`, `slurm://localhost` |
| `name` | QTau identifier (auto-generated if not provided) | `qtau-0` |
| `number_of_nodes` | Number of compute nodes | `2` |
| `cores_per_node` | CPU cores per node | `4` |
| `gpus_per_node` | GPUs per node (optional) | `1` |
| `queue` | SLURM queue/partition | `debug`, `regular` |
| `walltime` | Job walltime in minutes | `30` |
| `project` | HPC project/account ID | `m4408` |
| `conda_environment` | Path to conda environment | `/path/to/env` |
| `scheduler_script_commands` | Additional SLURM directives | `["#SBATCH --constraint=gpu"]` |

### Supported Resource URLs

| URL | Description |
|-----|-------------|
| `ssh://localhost` | Local SSH execution |
| `ssh://hostname` | Remote SSH execution |
| `slurm://localhost` | SLURM cluster submission |
| `pbs+ssh://hostname` | PBS cluster via SSH |

## Project Structure

```
qtau/
├── qtau/                          # Main package
│   ├── qtau_compute_service.py   # Core service API
│   ├── qtau_enums_exceptions.py  # Enums and exceptions
│   ├── pcs_logger.py              # Logging system
│   ├── job/                       # Job submission modules
│   │   ├── slurm.py               # SLURM integration
│   │   ├── ssh.py                 # SSH execution
│   │   └── local_subprocess.py    # Local execution
│   ├── plugins/                   # Execution engine plugins
│   │   ├── dask_v2/               # Dask backend
│   │   └── ray_v2/                # Ray backend
│   └── util/                      # Utility functions
├── examples/                      # Example scripts
├── tests/                         # Test suite
├── requirements.txt               # Python dependencies
└── setup.py                       # Package configuration
```

## Metrics and Logging

QTau automatically tracks task execution metrics and writes them to `metrics.csv` in the working directory:

| Metric | Description |
|--------|-------------|
| `task_id` | Unique task identifier |
| `qtau_scheduled` | QTau that executed the task |
| `submit_time` | Task submission timestamp |
| `wait_time_secs` | Time waiting in queue |
| `execution_secs` | Actual execution time |
| `status` | Task status (SUCCESS/FAILED) |
| `error_msg` | Error message if failed |

Logs are written to `qtau.log` in the working directory.

## Hints

Your default conda environment should contain all QTau and application dependencies. Activate it, e.g., in the `.bashrc`

## Dependencies

- `dask~=2024.12.1` / `distributed~=2024.12.1`
- `ray[all]~=2.40.0`
- `pennylane~=0.37.0`
- `asyncssh==2.16.0`
- `python-hostlist==1.23.0`

## License

QTau is released under the Apache 2.0 license. See LICENSE for more details.

## Authors

- Son Dang
- Youngje Son

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
