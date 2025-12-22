"""Tests for qtau.pilot_compute_service module."""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from qtau.pilot_enums_exceptions import ExecutionEngine, PilotAPIException
from qtau.pilot_compute_service import (
    PilotComputeBase,
    PilotComputeService,
    PilotCompute,
    PilotFuture,
    METRICS,
    SORTED_METRICS_FIELDS,
    run_mpi_task,
)


class TestMetrics:
    """Tests for METRICS configuration."""

    def test_metrics_keys(self):
        """Test that METRICS has expected keys."""
        expected_keys = {
            'task_id', 'pilot_scheduled', 'submit_time', 'wait_time_secs',
            'staging_time_secs', 'input_staging_data_size_bytes',
            'completion_time', 'execution_secs', 'status', 'error_msg'
        }
        assert set(METRICS.keys()) == expected_keys

    def test_sorted_metrics_fields(self):
        """Test that SORTED_METRICS_FIELDS is sorted."""
        assert SORTED_METRICS_FIELDS == sorted(METRICS.keys())


class TestRunMpiTask:
    """Tests for run_mpi_task function."""

    @patch('subprocess.run')
    def test_run_mpi_task_calls_srun(self, mock_run):
        """Test that run_mpi_task calls srun correctly."""
        mock_run.return_value = MagicMock(stdout="output", stderr="error")

        stdout, stderr = run_mpi_task(4, "/path/to/script.py", "arg1", "arg2")

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0][0] == "srun"
        assert "-n" in call_args[0][0]
        assert "4" in call_args[0][0]
        assert "python" in call_args[0][0]
        assert "/path/to/script.py" in call_args[0][0]


class TestPilotComputeBase:
    """Tests for PilotComputeBase class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture(autouse=True)
    def reset_logger_singleton(self):
        """Reset logger singleton before each test."""
        from qtau.pcs_logger import PilotComputeServiceLogger
        PilotComputeServiceLogger._instance = None
        yield
        PilotComputeServiceLogger._instance = None

    def test_init_creates_working_directory(self, temp_dir):
        """Test that initialization creates working directory."""
        work_dir = os.path.join(temp_dir, "new_dir")
        base = PilotComputeBase(ExecutionEngine.DASK, work_dir)
        assert os.path.exists(work_dir)

    def test_init_creates_metrics_file(self, temp_dir):
        """Test that initialization creates metrics file."""
        base = PilotComputeBase(ExecutionEngine.DASK, temp_dir)
        metrics_file = os.path.join(temp_dir, "metrics.csv")
        assert os.path.exists(metrics_file)

    def test_get_logger(self, temp_dir):
        """Test get_logger returns logger instance."""
        base = PilotComputeBase(ExecutionEngine.DASK, temp_dir)
        logger = base.get_logger()
        assert logger is not None

    def test_submit_task_without_client_raises(self, temp_dir):
        """Test that submit_task raises when client is not available."""
        base = PilotComputeBase(ExecutionEngine.DASK, temp_dir)
        base.get_client = MagicMock(return_value=None)

        with pytest.raises(PilotAPIException):
            base.submit_task(lambda: None)

    def test_task_decorator(self, temp_dir):
        """Test task decorator wraps function."""
        base = PilotComputeBase(ExecutionEngine.DASK, temp_dir)

        @base.task
        def sample_task():
            return 42

        # The decorated function should be callable
        assert callable(sample_task)


class TestPilotFuture:
    """Tests for PilotFuture wrapper class."""

    @pytest.fixture
    def mock_future(self):
        """Create a mock Future object."""
        future = MagicMock()
        future.result.return_value = "test_result"
        future.done.return_value = True
        future.exception.return_value = None
        future.cancelled.return_value = False
        return future

    def test_result(self, mock_future):
        """Test result method delegates to wrapped future."""
        pilot_future = PilotFuture(mock_future)
        assert pilot_future.result() == "test_result"
        mock_future.result.assert_called_once()

    def test_done(self, mock_future):
        """Test done method delegates to wrapped future."""
        pilot_future = PilotFuture(mock_future)
        assert pilot_future.done() is True
        mock_future.done.assert_called_once()

    def test_cancel(self, mock_future):
        """Test cancel method delegates to wrapped future."""
        pilot_future = PilotFuture(mock_future)
        pilot_future.cancel()
        mock_future.cancel.assert_called_once()

    def test_exception(self, mock_future):
        """Test exception method delegates to wrapped future."""
        pilot_future = PilotFuture(mock_future)
        assert pilot_future.exception() is None
        mock_future.exception.assert_called_once()

    def test_cancelled(self, mock_future):
        """Test cancelled method delegates to wrapped future."""
        pilot_future = PilotFuture(mock_future)
        assert pilot_future.cancelled() is False
        mock_future.cancelled.assert_called_once()

    def test_add_done_callback(self, mock_future):
        """Test add_done_callback method delegates to wrapped future."""
        pilot_future = PilotFuture(mock_future)
        callback = lambda f: None
        pilot_future.add_done_callback(callback)
        mock_future.add_done_callback.assert_called_once_with(callback)

    def test_retry(self, mock_future):
        """Test retry method delegates to wrapped future."""
        pilot_future = PilotFuture(mock_future)
        pilot_future.retry()
        mock_future.retry.assert_called_once()

    def test_release(self, mock_future):
        """Test release method delegates to wrapped future."""
        pilot_future = PilotFuture(mock_future)
        pilot_future.release()
        mock_future.release.assert_called_once()

    def test_repr(self, mock_future):
        """Test string representation."""
        pilot_future = PilotFuture(mock_future)
        repr_str = repr(pilot_future)
        assert "PilotFuture" in repr_str


class TestPilotComputeService:
    """Tests for PilotComputeService class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture(autouse=True)
    def reset_logger_singleton(self):
        """Reset logger singleton before each test."""
        from qtau.pcs_logger import PilotComputeServiceLogger
        PilotComputeServiceLogger._instance = None
        yield
        PilotComputeServiceLogger._instance = None

    @patch('qtau.pilot_compute_service.dask_cluster_manager')
    def test_init_with_dask_engine(self, mock_dask_manager, temp_dir):
        """Test initialization with DASK execution engine."""
        mock_manager_instance = MagicMock()
        mock_dask_manager.DaskManager.return_value = mock_manager_instance

        pcs = PilotComputeService(ExecutionEngine.DASK, temp_dir)

        mock_dask_manager.DaskManager.assert_called_once()
        assert pcs.execution_engine == ExecutionEngine.DASK

    @patch('qtau.pilot_compute_service.ray_cluster_manager')
    def test_init_with_ray_engine(self, mock_ray_manager, temp_dir):
        """Test initialization with RAY execution engine."""
        mock_manager_instance = MagicMock()
        mock_ray_manager.RayManager.return_value = mock_manager_instance

        pcs = PilotComputeService(ExecutionEngine.RAY, temp_dir)

        mock_ray_manager.RayManager.assert_called_once()
        assert pcs.execution_engine == ExecutionEngine.RAY

    @patch('qtau.pilot_compute_service.dask_cluster_manager')
    def test_get_pilots_initially_empty(self, mock_dask_manager, temp_dir):
        """Test that get_pilots returns empty list initially."""
        mock_manager_instance = MagicMock()
        mock_dask_manager.DaskManager.return_value = mock_manager_instance

        pcs = PilotComputeService(ExecutionEngine.DASK, temp_dir)

        assert pcs.get_pilots() == []

    @patch('qtau.pilot_compute_service.dask_cluster_manager')
    def test_get_pilot_not_found_raises(self, mock_dask_manager, temp_dir):
        """Test that get_pilot raises for non-existent pilot."""
        mock_manager_instance = MagicMock()
        mock_dask_manager.DaskManager.return_value = mock_manager_instance

        pcs = PilotComputeService(ExecutionEngine.DASK, temp_dir)

        with pytest.raises(PilotAPIException):
            pcs.get_pilot("non_existent_pilot")

    @patch('qtau.pilot_compute_service.dask_cluster_manager')
    def test_get_client_delegates_to_manager(self, mock_dask_manager, temp_dir):
        """Test that get_client delegates to cluster manager."""
        mock_manager_instance = MagicMock()
        mock_manager_instance.get_client.return_value = "mock_client"
        mock_dask_manager.DaskManager.return_value = mock_manager_instance

        pcs = PilotComputeService(ExecutionEngine.DASK, temp_dir)
        client = pcs.get_client()

        assert client == "mock_client"
        mock_manager_instance.get_client.assert_called_once()


class TestPilotCompute:
    """Tests for PilotCompute class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture(autouse=True)
    def reset_logger_singleton(self):
        """Reset logger singleton before each test."""
        from qtau.pcs_logger import PilotComputeServiceLogger
        PilotComputeServiceLogger._instance = None
        yield
        PilotComputeServiceLogger._instance = None

    @pytest.fixture
    def mock_cluster_manager(self, temp_dir):
        """Create a mock cluster manager."""
        manager = MagicMock()
        manager.execution_engine = ExecutionEngine.DASK
        manager.working_directory = temp_dir
        return manager

    def test_cancel_calls_batch_job_cancel(self, mock_cluster_manager):
        """Test that cancel calls batch job cancel."""
        batch_job = MagicMock()
        pilot = PilotCompute(batch_job, mock_cluster_manager)

        pilot.cancel()

        batch_job.cancel.assert_called_once()

    def test_get_state_delegates_to_batch_job(self, mock_cluster_manager):
        """Test that get_state delegates to batch job."""
        batch_job = MagicMock()
        batch_job.get_state.return_value = "running"
        pilot = PilotCompute(batch_job, mock_cluster_manager)

        state = pilot.get_state()

        assert state == "running"
        batch_job.get_state.assert_called_once()

    def test_get_id_delegates_to_cluster_manager(self, mock_cluster_manager):
        """Test that get_id delegates to cluster manager."""
        mock_cluster_manager.get_id.return_value = "pilot-123"
        pilot = PilotCompute(None, mock_cluster_manager)

        pilot_id = pilot.get_id()

        assert pilot_id == "pilot-123"

    def test_get_details_delegates_to_cluster_manager(self, mock_cluster_manager):
        """Test that get_details delegates to cluster manager."""
        mock_cluster_manager.get_config_data.return_value = {"key": "value"}
        pilot = PilotCompute(None, mock_cluster_manager)

        details = pilot.get_details()

        assert details == {"key": "value"}

    def test_get_client_delegates_to_cluster_manager(self, mock_cluster_manager):
        """Test that get_client delegates to cluster manager."""
        mock_cluster_manager.get_client.return_value = "mock_client"
        pilot = PilotCompute(None, mock_cluster_manager)

        client = pilot.get_client()

        assert client == "mock_client"

    def test_wait_delegates_to_cluster_manager(self, mock_cluster_manager):
        """Test that wait delegates to cluster manager."""
        pilot = PilotCompute(None, mock_cluster_manager)

        pilot.wait()

        mock_cluster_manager.wait.assert_called_once()
