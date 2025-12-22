"""Tests for qtau.plugins.pilot_manager_base module."""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from qtau.pilot_enums_exceptions import ExecutionEngine
from qtau.plugins.pilot_manager_base import PilotManager


class TestPilotManager:
    """Tests for PilotManager class."""

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

    def test_init_sets_working_directory(self, temp_dir):
        """Test that initialization sets working directory."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)
        assert manager.working_directory == temp_dir

    def test_init_sets_execution_engine(self, temp_dir):
        """Test that initialization sets execution engine."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)
        assert manager.execution_engine == ExecutionEngine.RAY

    def test_init_creates_scheduler_info_file_path(self, temp_dir):
        """Test that initialization creates scheduler info file path."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)
        expected_path = f'{temp_dir}/scheduler'
        assert manager.scheduler_info_file == expected_path

    def test_init_creates_worker_config_file_path(self, temp_dir):
        """Test that initialization creates worker config file path."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)
        expected_path = f'{temp_dir}/worker_config.json'
        assert manager.worker_config_file == expected_path

    def test_init_pilot_job_is_none(self, temp_dir):
        """Test that pilot_job is initially None."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)
        assert manager.pilot_job is None

    def test_start_scheduler_base_implementation(self, temp_dir):
        """Test that start_scheduler base implementation does nothing."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)
        # Should not raise
        manager.start_scheduler()

    def test_create_pilot_base_implementation(self, temp_dir):
        """Test that create_pilot base implementation does nothing."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)
        # Should not raise
        manager.create_pilot()

    def test_get_config_data_base_implementation(self, temp_dir):
        """Test that get_config_data base implementation returns None."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)
        assert manager.get_config_data() is None

    def test_get_pilot_status_base_implementation(self, temp_dir):
        """Test that get_pilot_status base implementation returns None."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)
        assert manager.get_pilot_status() is None

    def test_is_scheduler_started_false_when_no_file(self, temp_dir):
        """Test that is_scheduler_started returns False when file doesn't exist."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)
        assert manager.is_scheduler_started() is False

    def test_is_scheduler_started_true_when_file_exists(self, temp_dir):
        """Test that is_scheduler_started returns True when file exists."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)
        # Create the scheduler file
        scheduler_file = os.path.join(temp_dir, "scheduler")
        with open(scheduler_file, 'w') as f:
            f.write("scheduler_info")

        assert manager.is_scheduler_started() is True

    def test_cancel_with_no_pilot_job(self, temp_dir):
        """Test that cancel works when pilot_job is None."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)
        # Should not raise
        manager.cancel()

    def test_cancel_with_pilot_job(self, temp_dir):
        """Test that cancel calls pilot_job.cancel()."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)
        mock_job = MagicMock()
        manager.pilot_job = mock_job

        manager.cancel()

        mock_job.cancel.assert_called_once()

    @patch('subprocess.run')
    def test_stop_existing_processes(self, mock_run, temp_dir):
        """Test _stop_existing_processes method."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)
        mock_run.return_value = MagicMock(stdout="12345\n12346")

        manager._stop_existing_processes("ray")

        # Should call pgrep first
        assert mock_run.called

    def test_get_pilot_saga_job_executable(self, temp_dir):
        """Test _get_pilot_saga_job_executable returns python."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)
        assert manager._get_pilot_saga_job_executable() == "python"

    def test_setup_pilot_job_creates_working_directory(self, temp_dir):
        """Test that _setup_pilot_job creates pilot working directory."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)
        pilot_description = {
            "resource": "ssh://localhost",
            "type": "ray"
        }

        manager._setup_pilot_job(pilot_description)

        assert manager.pilot_working_directory is not None
        assert os.path.exists(manager.pilot_working_directory)

    def test_setup_pilot_job_sets_pilot_id(self, temp_dir):
        """Test that _setup_pilot_job sets pilot_id."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)
        pilot_description = {
            "resource": "ssh://localhost",
            "type": "ray"
        }

        manager._setup_pilot_job(pilot_description)

        assert manager.pilot_id is not None
        assert "RAY" in manager.pilot_id

    def test_get_saga_job_service_ssh(self, temp_dir):
        """Test _get_saga_job_service returns SSH service for ssh:// URLs."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)

        service = manager._get_saga_job_service("ssh://localhost", "ssh")

        from qtau.job import ssh
        assert isinstance(service, ssh.Service)

    def test_get_saga_job_service_slurm(self, temp_dir):
        """Test _get_saga_job_service returns SLURM service for slurm:// URLs."""
        manager = PilotManager(temp_dir, ExecutionEngine.RAY)

        service = manager._get_saga_job_service("slurm://localhost", "slurm")

        from qtau.job import slurm
        assert isinstance(service, slurm.Service)
