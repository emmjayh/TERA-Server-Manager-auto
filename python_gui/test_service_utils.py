# test_service_utils.py
# Unit tests for service_utils.py
# Dependencies: unittest (built-in), unittest.mock (built-in for Python 3.3+)

import unittest
from unittest.mock import patch, mock_open, MagicMock, call
import json
import subprocess
import os

# Assume service_utils.py is in the same directory or accessible via PYTHONPATH
import service_utils
import psutil # for psutil.NoSuchProcess

# Helper to create a CompletedProcess mock object
def make_completed_process(returncode=0, stdout="", stderr=""):
    mock_proc = MagicMock(spec=subprocess.CompletedProcess)
    mock_proc.returncode = returncode
    mock_proc.stdout = stdout
    mock_proc.stderr = stderr
    return mock_proc

class TestServiceUtils(unittest.TestCase):

    # --- Test Configuration Management ---

    @patch('service_utils.open', new_callable=mock_open, read_data='[{"name": "Test"}]')
    @patch('service_utils.os.path.exists', return_value=True)
    def test_load_config_success(self, mock_exists, mock_file_open):
        """Test successful loading of a valid JSON config file."""
        expected_data = [{"name": "Test"}]
        loaded_data = service_utils.load_config("dummy_path.json")
        self.assertEqual(loaded_data, expected_data)
        mock_file_open.assert_called_once_with("dummy_path.json", 'r')

    @patch('service_utils.os.path.exists', return_value=False)
    def test_load_config_file_not_found(self, mock_exists):
        """Test load_config when the file does not exist."""
        # service_utils.py prints a warning and returns [], so we check that.
        # We might also want to capture stdout to verify the warning.
        self.assertEqual(service_utils.load_config("non_existent.json"), [])
        mock_exists.assert_called_once_with("non_existent.json")

    @patch('service_utils.open', new_callable=mock_open, read_data='This is not JSON')
    @patch('service_utils.os.path.exists', return_value=True)
    def test_load_config_json_decode_error(self, mock_exists, mock_file_open):
        """Test load_config with invalid JSON content."""
        self.assertEqual(service_utils.load_config("invalid_json.json"), [])
        mock_file_open.assert_called_once_with("invalid_json.json", 'r')

    @patch('service_utils.open', new_callable=mock_open)
    @patch('service_utils.json.dump')
    def test_save_config_success(self, mock_json_dump, mock_file_open):
        """Test successful saving of config data."""
        test_data = [{"service": "TestSvc", "path": "C:\\app.exe"}]
        filepath = "test_save.json"

        result = service_utils.save_config(filepath, test_data)

        self.assertTrue(result)
        mock_file_open.assert_called_once_with(filepath, 'w')
        mock_json_dump.assert_called_once_with(test_data, mock_file_open(), indent=4)

    @patch('service_utils.open', side_effect=IOError("Disk full"))
    def test_save_config_io_error(self, mock_file_open):
        """Test save_config when an IOError occurs."""
        test_data = [{"service": "TestSvc"}]
        filepath = "test_io_error.json"

        result = service_utils.save_config(filepath, test_data)

        self.assertFalse(result)
        mock_file_open.assert_called_once_with(filepath, 'w')

    # --- Test Service Interaction ---

    @patch('service_utils.psutil.win_service_get')
    def test_get_service_status_running(self, mock_win_service_get):
        """Test get_service_status for a running service."""
        mock_service = MagicMock(spec=psutil.Service)
        mock_service.status.return_value = 'running'
        mock_service.pid.return_value = 1234
        mock_win_service_get.return_value = mock_service

        status, pid = service_utils.get_service_status("TestSvcRunning")

        self.assertEqual(status, 'running')
        self.assertEqual(pid, 1234)
        mock_win_service_get.assert_called_once_with("TestSvcRunning")
        mock_service.status.assert_called_once()
        mock_service.pid.assert_called_once()

    @patch('service_utils.psutil.win_service_get')
    def test_get_service_status_stopped(self, mock_win_service_get):
        """Test get_service_status for a stopped service."""
        mock_service = MagicMock(spec=psutil.Service)
        mock_service.status.return_value = 'stopped'
        # pid() should not be called if status is not 'running' per service_utils logic
        # but we can set it to None or 0 on the mock for completeness if the mock was more generic
        mock_service.pid.return_value = None # or 0, service_utils sets to None if not running
        mock_win_service_get.return_value = mock_service

        status, pid = service_utils.get_service_status("TestSvcStopped")

        self.assertEqual(status, 'stopped')
        self.assertIsNone(pid) # As per service_utils.py, PID is None if not running
        mock_win_service_get.assert_called_once_with("TestSvcStopped")
        mock_service.status.assert_called_once()
        mock_service.pid.assert_not_called() # Based on current service_utils logic


    @patch('service_utils.psutil.win_service_get', side_effect=psutil.NoSuchProcess(name="TestSvcNotFound"))
    def test_get_service_status_not_found(self, mock_win_service_get):
        """Test get_service_status for a service that is not found."""
        status, pid = service_utils.get_service_status("TestSvcNotFound")

        self.assertEqual(status, 'Not Found')
        self.assertIsNone(pid)
        mock_win_service_get.assert_called_once_with("TestSvcNotFound")

    @patch('service_utils.subprocess.run')
    def test_start_service_app_success(self, mock_subprocess_run):
        """Test start_service_app successful execution."""
        mock_subprocess_run.return_value = make_completed_process(returncode=0)
        service_name = "MyTestService"

        result = service_utils.start_service_app(service_name)

        self.assertTrue(result)
        mock_subprocess_run.assert_called_once_with(
            ["sc.exe", "start", service_name],
            check=False,
            capture_output=True,
            text=True,
            timeout=30
        )

    @patch('service_utils.subprocess.run')
    def test_start_service_app_failure(self, mock_subprocess_run):
        """Test start_service_app when sc.exe reports failure."""
        mock_subprocess_run.return_value = make_completed_process(returncode=1058, stderr="Service disabled") # Example error code
        service_name = "DisabledService"

        result = service_utils.start_service_app(service_name)

        self.assertFalse(result)
        mock_subprocess_run.assert_called_once_with(
            ["sc.exe", "start", service_name],
            check=False, capture_output=True, text=True, timeout=30
        )

    @patch('service_utils.subprocess.run')
    def test_start_service_app_already_running(self, mock_subprocess_run):
        """Test start_service_app when service is already running (SC.EXE code 1056)."""
        mock_subprocess_run.return_value = make_completed_process(returncode=1056) # SC_MANAGER_ALREADY_RUNNING
        service_name = "AlreadyRunningSvc"

        result = service_utils.start_service_app(service_name)

        self.assertTrue(result) # As per service_utils.py, this is considered success
        mock_subprocess_run.assert_called_once_with(
            ["sc.exe", "start", service_name],
            check=False, capture_output=True, text=True, timeout=30
        )

    @patch('service_utils.subprocess.run', side_effect=subprocess.TimeoutExpired(cmd="sc.exe start TestSvc", timeout=30))
    def test_start_service_app_timeout(self, mock_subprocess_run):
        """Test start_service_app when subprocess.run times out."""
        service_name = "TimeoutSvc"
        result = service_utils.start_service_app(service_name)
        self.assertFalse(result)
        mock_subprocess_run.assert_called_once()

    @patch('service_utils.subprocess.run')
    def test_stop_service_app_success(self, mock_subprocess_run):
        """Test stop_service_app successful execution."""
        mock_subprocess_run.return_value = make_completed_process(returncode=0)
        service_name = "MyTestServiceToStop"

        result = service_utils.stop_service_app(service_name)

        self.assertTrue(result)
        mock_subprocess_run.assert_called_once_with(
            ["sc.exe", "stop", service_name],
            check=False, capture_output=True, text=True, timeout=30
        )

    @patch('service_utils.subprocess.run')
    def test_stop_service_app_failure(self, mock_subprocess_run):
        """Test stop_service_app when sc.exe reports failure."""
        mock_subprocess_run.return_value = make_completed_process(returncode=1060, stderr="Service does not exist") # Example error code
        service_name = "NonExistentSvcForStop"

        result = service_utils.stop_service_app(service_name)

        self.assertFalse(result)
        mock_subprocess_run.assert_called_once_with(
            ["sc.exe", "stop", service_name],
            check=False, capture_output=True, text=True, timeout=30
        )

    @patch('service_utils.subprocess.run')
    def test_stop_service_app_not_running(self, mock_subprocess_run):
        """Test stop_service_app when service is not running (SC.EXE code 1062)."""
        mock_subprocess_run.return_value = make_completed_process(returncode=1062) # ERROR_SERVICE_NOT_ACTIVE
        service_name = "NotRunningSvc"

        result = service_utils.stop_service_app(service_name)

        self.assertTrue(result) # As per service_utils.py, this is considered success
        mock_subprocess_run.assert_called_once_with(
            ["sc.exe", "stop", service_name],
            check=False, capture_output=True, text=True, timeout=30
        )

    @patch('service_utils.subprocess.run', side_effect=FileNotFoundError("sc.exe not found"))
    def test_start_service_sc_not_found(self, mock_subprocess_run):
        """Test start_service_app when sc.exe is not found."""
        service_name = "AnySvc"
        result = service_utils.start_service_app(service_name)
        self.assertFalse(result)
        # subprocess.run is called, but then raises FileNotFoundError
        mock_subprocess_run.assert_called_once()

    @patch('service_utils.subprocess.run', side_effect=FileNotFoundError("sc.exe not found"))
    def test_stop_service_sc_not_found(self, mock_subprocess_run):
        """Test stop_service_app when sc.exe is not found."""
        service_name = "AnySvc"
        result = service_utils.stop_service_app(service_name)
        self.assertFalse(result)
        mock_subprocess_run.assert_called_once()

if __name__ == '__main__':
    unittest.main(verbosity=2)
