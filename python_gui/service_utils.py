# service_utils.py
# Description: Core utility functions for managing Windows services and configuration.
# Dependencies: psutil (install with: pip install psutil)

import json
import subprocess
import psutil
import os

# --- Configuration Management ---

def load_config(filepath: str) -> list:
    """
    Loads a JSON configuration file.

    Args:
        filepath: The path to the JSON configuration file.

    Returns:
        A list of dictionaries parsed from the JSON file.
        Returns an empty list if the file is not found or if a JSON decoding error occurs.
    """
    if not os.path.exists(filepath):
        print(f"Warning: Configuration file not found at {filepath}")
        return []
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                print(f"Error: Configuration file {filepath} does not contain a JSON list.")
                return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {filepath}: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while loading config from {filepath}: {e}")
        return []

def save_config(filepath: str, data: list) -> bool:
    """
    Saves data to a JSON configuration file.

    Args:
        filepath: The path to the JSON configuration file.
        data: A list of dictionaries to save.

    Returns:
        True if saving was successful, False otherwise.
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except IOError as e:
        print(f"Error saving configuration to {filepath}: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while saving config to {filepath}: {e}")
        return False

# --- Service Interaction ---

def get_service_status(service_name: str) -> tuple[str, int | None]:
    """
    Retrieves the status and PID of a given Windows service.

    Args:
        service_name: The name of the Windows service.

    Returns:
        A tuple (status_string, pid_integer_or_None).
        'status_string' can be 'running', 'stopped', 'paused', 'Not Found', or other psutil status.
        'pid_integer_or_None' is the Process ID if running, otherwise None.
    """
    try:
        service = psutil.win_service_get(service_name)
        status = service.status()
        pid = service.pid() if status == 'running' else None # Ensure PID is None if not running
        return status, pid
    except psutil.NoSuchProcess:
        # This exception is raised if the service does not exist.
        return "Not Found", None
    except Exception as e:
        # Catch other potential psutil or system errors
        print(f"Error getting status for service '{service_name}': {e}")
        return "Error", None

def start_service_app(service_name: str) -> bool:
    """
    Attempts to start a Windows service using 'sc.exe start'.

    Args:
        service_name: The name of the Windows service.

    Returns:
        True if the 'sc.exe start' command was issued and reported success (or did not report obvious failure).
        False if the command failed or the service could not be started.
        Note: Successful return doesn't guarantee the service is fully initialized and running,
        only that the start command was accepted by the Service Control Manager.
    """
    try:
        # Using shell=False is generally safer, but sc.exe might require shell=True in some environments
        # or if service_name could contain special characters that need shell interpretation (though ideally it shouldn't).
        # For direct command like sc.exe, shell=False with list of args is best.
        result = subprocess.run(
            ["sc.exe", "start", service_name],
            check=False,  # We'll check returncode manually
            capture_output=True,
            text=True,
            timeout=30 # Add a timeout for sc.exe to respond
        )

        # Typical success output from `sc.exe start` might include "STATE" information.
        # A return code of 0 is usually a good sign.
        # Some error codes:
        # 1056: An instance of the service is already running. (Consider this a success for "start")
        # 1060: The specified service does not exist as an installed service.
        # 1058: The service cannot be started, either because it is disabled or because it has no enabled devices associated with it.

        if result.returncode == 0:
            print(f"Command 'sc.exe start {service_name}' executed successfully.")
            return True
        elif result.returncode == 1056: # Service already running
            print(f"Service '{service_name}' is already running.")
            return True # Considered success for a start command
        else:
            print(f"Failed to start service '{service_name}'. SC.exe exited with code {result.returncode}.")
            print(f"SC.exe STDOUT: {result.stdout.strip()}")
            print(f"SC.exe STDERR: {result.stderr.strip()}")
            return False

    except FileNotFoundError:
        print("Error: 'sc.exe' not found. Ensure it's in the system PATH.")
        return False
    except subprocess.TimeoutExpired:
        print(f"Timeout expired for 'sc.exe start {service_name}'. The service might be taking too long to start or 'sc.exe' is unresponsive.")
        return False # Or handle as an indeterminate state
    except Exception as e:
        print(f"An unexpected error occurred while trying to start service '{service_name}': {e}")
        return False

def stop_service_app(service_name: str) -> bool:
    """
    Attempts to stop a Windows service using 'sc.exe stop'.

    Args:
        service_name: The name of the Windows service.

    Returns:
        True if the 'sc.exe stop' command was issued and reported success.
        False if the command failed or the service could not be stopped.
    """
    try:
        result = subprocess.run(
            ["sc.exe", "stop", service_name],
            check=False,
            capture_output=True,
            text=True,
            timeout=30 # Add a timeout
        )
        # A return code of 0 is usually a good sign.
        # Error codes:
        # 1062: The service has not been started. (Consider this a success for "stop")
        # 1060: The specified service does not exist as an installed service.

        if result.returncode == 0:
            print(f"Command 'sc.exe stop {service_name}' executed successfully.")
            return True
        elif result.returncode == 1062: # Service not started
            print(f"Service '{service_name}' was not running.")
            return True # Considered success for a stop command
        else:
            print(f"Failed to stop service '{service_name}'. SC.exe exited with code {result.returncode}.")
            print(f"SC.exe STDOUT: {result.stdout.strip()}")
            print(f"SC.exe STDERR: {result.stderr.strip()}")
            return False

    except FileNotFoundError:
        print("Error: 'sc.exe' not found. Ensure it's in the system PATH.")
        return False
    except subprocess.TimeoutExpired:
        print(f"Timeout expired for 'sc.exe stop {service_name}'. The service might be taking too long to stop or 'sc.exe' is unresponsive.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while trying to stop service '{service_name}': {e}")
        return False

if __name__ == "__main__":
    print("--- Testing service_utils.py ---")

    # Create a dummy server_config.json for testing load/save if it doesn't exist
    # This will be in the same directory as service_utils.py if run directly.
    # For a real application, provide a full path or handle paths appropriately.
    test_config_path = "server_config_test.json"

    config_data_to_save = [
        {"ServiceName": "TestSvcPy1", "FriendlyName": "My Python Test Service 1", "AppPath": "C:\\dummy1.exe"},
        {"ServiceName": "TestSvcPy2", "FriendlyName": "My Python Test Service 2", "AppPath": "C:\\dummy2.bat"}
    ]

    # Test save_config
    print(f"\nAttempting to save config to '{test_config_path}'...")
    if save_config(test_config_path, config_data_to_save):
        print(f"Successfully saved config to {test_config_path}")
    else:
        print(f"Failed to save config to {test_config_path}")

    # Test load_config
    print(f"\nAttempting to load config from '{test_config_path}'...")
    loaded_data = load_config(test_config_path)
    if loaded_data:
        print(f"Successfully loaded config: {loaded_data}")
        # Verify content (optional)
        if loaded_data == config_data_to_save:
            print("Loaded data matches saved data.")
        else:
            print("Warning: Loaded data does NOT match saved data.")
    else:
        print(f"Failed to load config or config was empty from {test_config_path}")

    # Test get_service_status
    # Using 'PrintSpooler' as it's a common Windows service. Replace if needed.
    # Or use a service created by the PowerShell scripts if they were run.
    test_service_name = "PrintSpooler"
    print(f"\nAttempting to get status for service '{test_service_name}'...")
    status, pid = get_service_status(test_service_name)
    print(f"Service '{test_service_name}': Status = {status}, PID = {pid}")

    non_existent_service = "ThisServiceDoesNotExist123"
    print(f"\nAttempting to get status for service '{non_existent_service}'...")
    status, pid = get_service_status(non_existent_service)
    print(f"Service '{non_existent_service}': Status = {status}, PID = {pid}")

    # Test start_service_app and stop_service_app
    # WARNING: These tests attempt to START and STOP the 'PrintSpooler' service.
    # Do NOT run this on a critical system without understanding the implications.
    # For CI/CD or non-critical test environments, this might be acceptable.
    # It's better to have a dedicated dummy service for these tests.

    # For now, we'll just call them with a non-existent service to show they run without crashing.
    # To truly test start/stop, a service would need to be installed.
    print(f"\nAttempting to start '{non_existent_service}' (expected to fail as it doesn't exist)...")
    start_result = start_service_app(non_existent_service)
    print(f"Result of starting '{non_existent_service}': {start_result}")

    print(f"\nAttempting to stop '{non_existent_service}' (expected to fail or report not running)...")
    stop_result = stop_service_app(non_existent_service)
    print(f"Result of stopping '{non_existent_service}': {stop_result}")

    # Example of trying to stop an actual service (use with caution)
    # print(f"\nAttempting to stop '{test_service_name}'...")
    # if get_service_status(test_service_name)[0] == 'running':
    #     stop_actual_result = stop_service_app(test_service_name)
    #     print(f"Result of stopping '{test_service_name}': {stop_actual_result}")
    #     if stop_actual_result:
    #         print(f"Waiting a few seconds before trying to start '{test_service_name}' again...")
    #         import time
    #         time.sleep(5) # Give time for service to fully stop
    #         print(f"Attempting to start '{test_service_name}'...")
    #         start_actual_result = start_service_app(test_service_name)
    #         print(f"Result of starting '{test_service_name}': {start_actual_result}")
    # else:
    #     print(f"Service '{test_service_name}' is not running, skipping stop/start test for it.")

    print("\n--- Finished testing service_utils.py ---")
