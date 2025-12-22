"""Tests for qtau.pilot_enums_exceptions module."""
import pytest
from qtau.pilot_enums_exceptions import ExecutionEngine, PilotAPIException


class TestExecutionEngine:
    """Tests for ExecutionEngine enum."""

    def test_dask_engine_value(self):
        """Test that DASK engine has correct value."""
        assert ExecutionEngine.DASK.value == "dask"

    def test_ray_engine_value(self):
        """Test that RAY engine has correct value."""
        assert ExecutionEngine.RAY.value == "ray"

    def test_execution_engine_members(self):
        """Test that ExecutionEngine has expected members."""
        members = list(ExecutionEngine)
        assert len(members) == 2
        assert ExecutionEngine.DASK in members
        assert ExecutionEngine.RAY in members

    def test_execution_engine_name(self):
        """Test the name property of ExecutionEngine."""
        assert ExecutionEngine.DASK.name == "DASK"
        assert ExecutionEngine.RAY.name == "RAY"


class TestPilotAPIException:
    """Tests for PilotAPIException."""

    def test_exception_is_exception_subclass(self):
        """Test that PilotAPIException is a subclass of Exception."""
        assert issubclass(PilotAPIException, Exception)

    def test_exception_can_be_raised(self):
        """Test that PilotAPIException can be raised and caught."""
        with pytest.raises(PilotAPIException):
            raise PilotAPIException("Test error message")

    def test_exception_message(self):
        """Test that exception message is preserved."""
        message = "Custom error message"
        try:
            raise PilotAPIException(message)
        except PilotAPIException as e:
            assert str(e) == message

    def test_exception_empty_message(self):
        """Test that exception can be raised with empty message."""
        with pytest.raises(PilotAPIException):
            raise PilotAPIException()
