# QTAU

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)

**QTAU** (Quantum Task Automation Utility) is a Quantum-HPC middleware framework designed to address the challenges of integrating quantum and classical computing resources. It provides a unified interface for managing heterogeneous resources, including diverse Quantum Processing Unit (QPU) modalities and various integration types with classical HPC systems.

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

### Using pip

```bash
pip install -r requirements.txt
python setup.py install
```

### Development Installation

```bash
git clone https://github.com/your-org/qtau.git
cd qtau
pip install -e .
```

## Quick Start

### Basic Usage with Dask

```python
import os
from qtau.pilot_compute_service import PilotComputeService

WORKING_DIRECTORY = os.path.join(os.environ["HOME"], "work")

# Configure pilot
pilot_description = {
    "resource": "ssh://localhost",
    "working_directory": WORKING_DIRECTORY,
    "type": "dask",
    "number_of_nodes": 2,
    "cores_per_node": 4,
}

# Initialize and create pilot
pcs = PilotComputeService(working_directory=WORKING_DIRECTORY)
pcs.create_pilot(pilot_compute_description=pilot_description)

# Define a task
def compute(x):
    return x ** 2

# Submit tasks
tasks = [pcs.submit_task(compute, i) for i in range(10)]

# Wait for completion and get results
pcs.wait_tasks(tasks)
results = pcs.get_results(tasks)
print(results)  # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# Cleanup
pcs.cancel()
```

### Using Ray Backend

```python
from qtau.pilot_compute_service import ExecutionEngine, PilotComputeService

pilot_description = {
    "resource": "ssh://localhost",
    "working_directory": WORKING_DIRECTORY,
    "type": "ray",
    "number_of_nodes": 2,
    "cores_per_node": 4,
}

pcs = PilotComputeService(
    execution_engine=ExecutionEngine.RAY,
    working_directory=WORKING_DIRECTORY
)
pcs.create_pilot(pilot_compute_description=pilot_description)

# Submit tasks with resource specifications
task = pcs.submit_task(
    compute,
    42,
    resources={'num_cpus': 1, 'num_gpus': 0, 'memory': None}
)
```

### Quantum Computing with PennyLane

```python
import pennylane as qml
from qtau.pilot_compute_service import PilotComputeService

def quantum_circuit():
    wires = 4
    dev = qml.device('default.qubit', wires=wires)

    @qml.qnode(dev)
    def circuit(parameters):
        qml.StronglyEntanglingLayers(weights=parameters, wires=range(wires))
        return [qml.expval(qml.PauliZ(i)) for i in range(wires)]

    shape = qml.StronglyEntanglingLayers.shape(n_layers=1, n_wires=wires)
    weights = qml.numpy.random.random(size=shape)
    return circuit(weights)

# Submit quantum tasks
pcs = PilotComputeService(working_directory=WORKING_DIRECTORY)
pcs.create_pilot(pilot_compute_description=pilot_description)

tasks = [
    pcs.submit_task(quantum_circuit, task_name=f"quantum_task_{i}")
    for i in range(10)
]
pcs.wait_tasks(tasks)
```

## Configuration Options

### Pilot Description Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `resource` | Resource URL for job submission | `ssh://localhost`, `slurm+ssh://cluster` |
| `working_directory` | Directory for logs and metrics | `/home/user/work` |
| `type` | Execution engine type | `dask`, `ray` |
| `number_of_nodes` | Number of compute nodes | `2` |
| `cores_per_node` | CPU cores per node | `4` |
| `gpus_per_node` | GPUs per node (optional) | `1` |

### Supported Resource URLs

- `ssh://localhost` - Local SSH execution
- `slurm+ssh://hostname` - SLURM cluster via SSH
- `pbs+ssh://hostname` - PBS cluster via SSH

## Project Structure

```
qtau/
├── qtau/                      # Main package
│   ├── pilot_compute_service.py   # Core service API
│   ├── pilot_enums_exceptions.py  # Enums and exceptions
│   ├── pcs_logger.py              # Logging system
│   ├── job/                       # Job submission modules
│   │   ├── slurm.py               # SLURM integration
│   │   ├── ssh.py                 # SSH execution
│   │   └── local_subprocess.py    # Local execution
│   ├── plugins/                   # Execution engine plugins
│   │   ├── dask_v2/               # Dask backend
│   │   └── ray_v2/                # Ray backend
│   └── util/                      # Utility functions
├── examples/                  # Example scripts
├── tests/                     # Test suite
├── requirements.txt           # Python dependencies
└── setup.py                   # Package configuration
```

## Examples

The `examples/` directory contains various usage scenarios:

| Example | Description |
|---------|-------------|
| `pq_pcs_dask.py` | Basic Dask with PennyLane quantum circuits |
| `pq_pcs_ray.py` | Basic Ray with PennyLane quantum circuits |
| `pq_pcs_multi_dask.py` | Multi-node Dask deployment |
| `pq_ray_slurm_perlmutter.py` | Ray on NERSC Perlmutter with SLURM |
| `pilot_circuit_execution.py` | Qiskit circuit execution |
| `benchmarks/` | Performance benchmarking scripts |

## Metrics and Logging

QTAU automatically tracks task execution metrics and writes them to `metrics.csv` in the working directory:

- Task submission and completion times
- Wait time and execution duration
- Task status (SUCCESS/FAILED)
- Error messages (if any)

Logs are written to `qtau.log` in the working directory.

## Environment Setup

For optimal usage, activate your conda environment with all dependencies in your shell configuration:

```bash
# Add to ~/.bashrc or ~/.zshrc
conda activate qtau-env
```

## Dependencies

- `dask~=2024.7.1` / `distributed~=2024.7.1`
- `ray[all]~=2.34.0`
- `pennylane~=0.37.0`
- `asyncssh==2.16.0`
- `python-hostlist==1.23.0`

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Authors

- Son Dang
- Youngje Son

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
