"""Tests for qtau.pcs_logger module."""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from qtau.pcs_logger import PilotComputeServiceLogger


class TestPilotComputeServiceLogger:
    """Tests for PilotComputeServiceLogger class."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton instance before each test."""
        PilotComputeServiceLogger._instance = None
        yield
        PilotComputeServiceLogger._instance = None

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_singleton_pattern(self, temp_dir):
        """Test that logger follows singleton pattern."""
        logger1 = PilotComputeServiceLogger(temp_dir)
        logger2 = PilotComputeServiceLogger(temp_dir)
        assert logger1 is logger2

    def test_logger_creates_log_file(self, temp_dir):
        """Test that logger creates log file in working directory."""
        logger = PilotComputeServiceLogger(temp_dir)
        log_file = os.path.join(temp_dir, "qtau.log")
        assert os.path.exists(log_file)

    def test_info_method(self, temp_dir):
        """Test info logging method."""
        logger = PilotComputeServiceLogger(temp_dir)
        # Should not raise
        logger.info("Test info message")

    def test_warning_method(self, temp_dir):
        """Test warning logging method."""
        logger = PilotComputeServiceLogger(temp_dir)
        # Should not raise
        logger.warning("Test warning message")

    def test_error_method(self, temp_dir):
        """Test error logging method."""
        logger = PilotComputeServiceLogger(temp_dir)
        # Should not raise
        logger.error("Test error message")

    def test_critical_method(self, temp_dir):
        """Test critical logging method."""
        logger = PilotComputeServiceLogger(temp_dir)
        # Should not raise
        logger.critical("Test critical message")

    def test_debug_method(self, temp_dir):
        """Test debug logging method."""
        logger = PilotComputeServiceLogger(temp_dir)
        # Should not raise
        logger.debug("Test debug message")

    def test_log_method_with_different_levels(self, temp_dir):
        """Test log method with various log levels."""
        import logging
        logger = PilotComputeServiceLogger(temp_dir)

        # Should not raise for any level
        logger.log("info message", logging.INFO)
        logger.log("warning message", logging.WARNING)
        logger.log("error message", logging.ERROR)
        logger.log("critical message", logging.CRITICAL)
        logger.log("debug message", logging.DEBUG)

    def test_working_directory_stored(self, temp_dir):
        """Test that working directory is stored."""
        logger = PilotComputeServiceLogger(temp_dir)
        assert logger.pcs_working_directory == temp_dir

    def test_initialized_flag(self, temp_dir):
        """Test that _initialized flag is set after initialization."""
        logger = PilotComputeServiceLogger(temp_dir)
        assert logger._initialized is True
