"""Tests for qtau.util.ssh_utils module."""
import os
import socket
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from qtau.util.ssh_utils import (
    get_localhost,
    execute_local_process,
    execute_ssh_command,
    execute_ssh_command_as_daemon,
    execute_ssh_command_shell_as_daemon,
)


class TestGetLocalhost:
    """Tests for get_localhost function."""

    def test_get_localhost_returns_string(self):
        """Test that get_localhost returns a string."""
        result = get_localhost()
        assert isinstance(result, str)

    def test_get_localhost_returns_ip_format(self):
        """Test that get_localhost returns an IP-like format."""
        result = get_localhost()
        # Should contain dots (IPv4) or return the hostname
        assert result is not None
        assert len(result) > 0

    @patch('socket.gethostbyname')
    @patch('socket.gethostname')
    def test_get_localhost_uses_socket(self, mock_gethostname, mock_gethostbyname):
        """Test that get_localhost uses socket module."""
        mock_gethostname.return_value = "testhost"
        mock_gethostbyname.return_value = "192.168.1.100"

        result = get_localhost()

        assert result == "192.168.1.100"
        mock_gethostname.assert_called_once()
        mock_gethostbyname.assert_called_once_with("testhost")

    @patch('socket.gethostbyname')
    @patch('socket.gethostname')
    def test_get_localhost_fallback_on_error(self, mock_gethostname, mock_gethostbyname):
        """Test that get_localhost falls back to 127.0.0.1 on error."""
        mock_gethostname.side_effect = Exception("Network error")

        result = get_localhost()

        assert result == "127.0.0.1"


class TestExecuteLocalProcess:
    """Tests for execute_local_process function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @patch('subprocess.Popen')
    def test_execute_local_process_success(self, mock_popen, temp_dir):
        """Test execute_local_process with successful command."""
        mock_process = MagicMock()
        mock_process.poll.side_effect = [None, 0]  # First running, then done
        mock_popen.return_value = mock_process

        # Should not raise
        execute_local_process("echo test", temp_dir)

        mock_popen.assert_called_once()

    @patch('subprocess.Popen')
    def test_execute_local_process_failure_raises(self, mock_popen, temp_dir):
        """Test execute_local_process raises on failure."""
        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Non-zero return code
        mock_popen.return_value = mock_process

        with pytest.raises(RuntimeError):
            execute_local_process("false", temp_dir)

    @patch('subprocess.Popen')
    def test_execute_local_process_uses_shell(self, mock_popen, temp_dir):
        """Test that execute_local_process uses shell=True."""
        mock_process = MagicMock()
        mock_process.poll.return_value = 0
        mock_popen.return_value = mock_process

        execute_local_process("echo test", temp_dir)

        call_kwargs = mock_popen.call_args[1]
        assert call_kwargs['shell'] is True


class TestExecuteSshCommand:
    """Tests for execute_ssh_command function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @patch('subprocess.Popen')
    def test_execute_ssh_command_constructs_command(self, mock_popen, temp_dir):
        """Test that execute_ssh_command constructs SSH command correctly."""
        mock_process = MagicMock()
        mock_process.poll = MagicMock(return_value=0)
        mock_process.wait = MagicMock()
        mock_popen.return_value = mock_process

        execute_ssh_command(
            host="testhost",
            user="testuser",
            command="/bin/date",
            working_directory=temp_dir
        )

        call_args = mock_popen.call_args[0][0]
        assert "ssh" in call_args
        assert "testhost" in call_args
        assert "testuser" in call_args

    @patch('subprocess.Popen')
    def test_execute_ssh_command_with_keyfile(self, mock_popen, temp_dir):
        """Test that execute_ssh_command includes keyfile parameter."""
        mock_process = MagicMock()
        mock_process.poll = MagicMock(return_value=0)
        mock_process.wait = MagicMock()
        mock_popen.return_value = mock_process

        execute_ssh_command(
            host="testhost",
            command="/bin/date",
            keyfile="/path/to/key",
            working_directory=temp_dir
        )

        call_args = mock_popen.call_args[0][0]
        assert "-i" in call_args
        assert "/path/to/key" in call_args

    @patch('subprocess.Popen')
    def test_execute_ssh_command_with_arguments(self, mock_popen, temp_dir):
        """Test that execute_ssh_command includes arguments."""
        mock_process = MagicMock()
        mock_process.poll = MagicMock(return_value=0)
        mock_process.wait = MagicMock()
        mock_popen.return_value = mock_process

        execute_ssh_command(
            host="testhost",
            command="/bin/echo",
            arguments=["arg1", "arg2"],
            working_directory=temp_dir
        )

        call_args = mock_popen.call_args[0][0]
        assert "arg1" in call_args
        assert "arg2" in call_args


class TestExecuteSshCommandAsDaemon:
    """Tests for execute_ssh_command_as_daemon function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @patch('subprocess.Popen')
    def test_execute_ssh_command_as_daemon_uses_close_fds(self, mock_popen, temp_dir):
        """Test that daemon command uses close_fds=True."""
        mock_process = MagicMock()
        mock_process.poll = MagicMock(return_value=0)
        mock_popen.return_value = mock_process

        execute_ssh_command_as_daemon(
            host="testhost",
            command="/bin/date",
            working_directory=temp_dir
        )

        call_kwargs = mock_popen.call_args[1]
        assert call_kwargs['close_fds'] is True


class TestExecuteSshCommandShellAsDaemon:
    """Tests for execute_ssh_command_shell_as_daemon function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @patch('subprocess.Popen')
    def test_execute_ssh_command_shell_as_daemon_includes_nohup(self, mock_popen, temp_dir):
        """Test that shell daemon command includes nohup."""
        mock_process = MagicMock()
        mock_process.poll = MagicMock(return_value=None)
        mock_popen.return_value = mock_process

        execute_ssh_command_shell_as_daemon(
            host="testhost",
            command="/bin/date",
            working_directory=temp_dir
        )

        call_args = mock_popen.call_args[0][0]
        assert "nohup" in call_args
