from enum import Enum


class ExecutionEngine(Enum):
    DASK = "dask"
    RAY = "ray"


class PilotAPIException(Exception):
    pass