import subprocess
import psutil
import os
import time 
import json 
import logging # Added

# --- Logging Configuration ---
LOG_DIR_NAME = "logs_manager" # Name of the log directory for process_manager itself
# Path: project_root/logs_manager/process_manager.log
# Assumes process_manager.py is in python_gui/ which is in project_root
PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
LOG_DIR_PATH = os.path.join(PROJECT_ROOT, LOG_DIR_NAME)

if not os.path.exists(LOG_DIR_PATH):
    try:
        os.makedirs(LOG_DIR_PATH, exist_ok=True)
    except OSError as e:
        # Fallback or print error if log directory for manager itself cannot be created
        # This is a critical setup step, so print is used if logger isn't ready.
        print(f"CRITICAL: Could not create log directory {LOG_DIR_PATH}: {e}")
        # As a last resort, log in the current script's directory
        LOG_DIR_PATH = os.path.dirname(os.path.abspath(__file__))


LOG_FILE_MANAGER_PATH = os.path.join(LOG_DIR_PATH, "process_manager.log")

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_MANAGER_PATH), 
        logging.StreamHandler() 
    ]
)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG) # Uncomment for more verbose debug logging

# --- Data Structures ---
managed_processes = {}
CONFIG_FILE_PATH = os.path.normpath(os.path.join(PROJECT_ROOT, "server_config.json"))

# --- Monitoring Control ---
monitoring_active = False
MONITOR_INTERVAL_SECONDS = 10 
MAX_RESTARTS_IN_INTERVAL = 3 
RESTART_INTERVAL_SECONDS = 60 
DEFAULT_RESTART_DELAY_SECONDS = 5 


# --- Configuration Loading ---
def load_configuration():
    """Loads server_config.json and initializes managed_processes."""
    global managed_processes
    new_managed_processes = {} 

    try:
        with open(CONFIG_FILE_PATH, 'r') as f:
            config_entries = json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file '{CONFIG_FILE_PATH}' not found.")
        managed_processes.clear()
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Could not decode '{CONFIG_FILE_PATH}'. Invalid JSON: {e}")
        managed_processes.clear() 
        return False

    for entry in config_entries:
        service_name = entry.get("ServiceName")
        if not service_name:
            logger.warning(f"Config entry missing 'ServiceName': {entry}")
            continue
        
        log_dir_config = entry.get("LogDirectory")
        log_file_path_app = None 
        if not log_dir_config:
            logger.warning(f"Config entry for '{service_name}' missing 'LogDirectory'. Will not redirect app logs.")
        else:
            if not os.path.isabs(log_dir_config):
                log_dir_config = os.path.normpath(os.path.join(os.path.dirname(CONFIG_FILE_PATH), log_dir_config))

            if not os.path.exists(log_dir_config):
                try:
                    os.makedirs(log_dir_config, exist_ok=True)
                except OSError as e:
                    logger.error(f"Error creating app log directory {log_dir_config} for {service_name}: {e}")
            
            # Application log file: One per service name, appended.
            log_file_path_app = os.path.join(log_dir_config, f"{service_name}_app.log")


        existing_proc_info = managed_processes.get(service_name, {})
        
        new_managed_processes[service_name] = {
            "config": entry,
            "pid": existing_proc_info.get("pid"), 
            "process_handle": existing_proc_info.get("process_handle"), 
            "status": existing_proc_info.get("status", "stopped"), 
            "last_start_time": existing_proc_info.get("last_start_time"),
            "restart_history": existing_proc_info.get("restart_history", []), 
            "log_file_path": log_file_path_app, # This is for the application's stdout/stderr
            "log_file_handle": existing_proc_info.get("log_file_handle"), 
            "user_stopped": existing_proc_info.get("user_stopped", False) 
        }
    
    managed_processes = new_managed_processes
    logger.info(f"Configuration reloaded. Managing {len(managed_processes)} processes.")
    return True


# --- Process Control Functions ---
def launch_process(service_name: str) -> bool:
    """Launches a single process based on its configuration."""
    if service_name not in managed_processes:
        logger.error(f"No configuration found for service '{service_name}'.")
        return False

    proc_info = managed_processes[service_name]
    config = proc_info["config"]
    app_path = config.get("AppPath")
    app_args_str = config.get("AppArguments", "") 
    
    if not app_path:
        logger.error(f"AppPath for '{service_name}' is not defined.")
        proc_info["status"] = "error_app_path_missing"
        return False
    
    if not os.path.isabs(app_path):
        app_path = os.path.normpath(os.path.join(os.path.dirname(CONFIG_FILE_PATH), app_path))

    if not os.path.exists(app_path):
        logger.error(f"AppPath for '{service_name}' does not exist: {app_path}")
        proc_info["status"] = "error_app_path_invalid"
        return False

    if proc_info["pid"] and psutil.pid_exists(proc_info["pid"]):
        try:
            p = psutil.Process(proc_info["pid"])
            logger.info(f"Service '{service_name}' (PID: {proc_info['pid']}) is already considered running.")
            proc_info["status"] = "running" 
            proc_info["user_stopped"] = False
            return True 
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            logger.warning(f"PID {proc_info['pid']} for '{service_name}' existed but process is now gone or inaccessible. Proceeding to launch.")
            proc_info["pid"] = None 
            proc_info["process_handle"] = None

    command = []
    if app_path.lower().endswith(".bat"):
        command = ['cmd.exe', '/c', app_path] + app_args_str.split()
    elif app_path.lower().endswith(".exe"):
        command = [app_path] + app_args_str.split()
    else:
        logger.error(f"Unsupported AppPath extension for '{service_name}': {app_path}. Only .bat and .exe supported directly.")
        proc_info["status"] = "error_unsupported_ext"
        return False

    try:
        logger.info(f"Attempting to launch '{service_name}': {' '.join(command)}")
        log_fp_app = None
        if proc_info["log_file_path"]: # This is app's log_file_path
            try:
                if proc_info.get("log_file_handle") and not proc_info["log_file_handle"].closed:
                    proc_info["log_file_handle"].close() 
                
                proc_info["log_file_handle"] = open(proc_info["log_file_path"], 'a')
                log_fp_app = proc_info["log_file_handle"]
                log_fp_app.write(f"\n--- Process '{service_name}' launched at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                log_fp_app.flush()
            except Exception as e:
                logger.error(f"Error opening app log file {proc_info['log_file_path']} for {service_name}: {e}")
                log_fp_app = subprocess.DEVNULL 
        else:
            log_fp_app = subprocess.DEVNULL

        creation_flags = 0
        if os.name == 'nt': creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

        proc_handle = subprocess.Popen(
            command, stdout=log_fp_app, stderr=subprocess.STDOUT, 
            creationflags=creation_flags, cwd=os.path.dirname(app_path)
        )
        
        proc_info["process_handle"] = proc_handle
        proc_info["pid"] = proc_handle.pid
        proc_info["status"] = "running"
        proc_info["last_start_time"] = time.time()
        proc_info["user_stopped"] = False 
        logger.info(f"Successfully launched '{service_name}' with PID {proc_info['pid']}.")
        return True
    except FileNotFoundError:
        logger.error(f"Command or application not found for '{service_name}': {command[0]}")
        proc_info["status"] = "error_not_found"
        if proc_info.get("log_file_handle") and not proc_info["log_file_handle"].closed:
            proc_info["log_file_handle"].close(); proc_info["log_file_handle"] = None
        return False
    except Exception as e:
        logger.error(f"Failed to launch '{service_name}': {e}")
        proc_info["status"] = "error_launch_failed"
        if proc_info.get("log_file_handle") and not proc_info["log_file_handle"].closed:
            proc_info["log_file_handle"].close(); proc_info["log_file_handle"] = None
        return False

def terminate_process(service_name: str, mark_user_stopped=True) -> bool:
    """Terminates a single managed process."""
    if service_name not in managed_processes:
        logger.error(f"No configuration found for service '{service_name}'.")
        return False

    proc_info = managed_processes[service_name]
    pid = proc_info.get("pid")

    if mark_user_stopped: proc_info["user_stopped"] = True

    if not pid or not psutil.pid_exists(pid):
        logger.info(f"Service '{service_name}' is not running or PID {pid} not found.")
        proc_info["status"] = "stopped"; proc_info["pid"] = None; proc_info["process_handle"] = None
        if proc_info.get("log_file_handle") and not proc_info["log_file_handle"].closed:
            proc_info["log_file_handle"].write(f"\n--- Process '{service_name}' confirmed stopped/not running at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            proc_info["log_file_handle"].close(); proc_info["log_file_handle"] = None
        return True

    try:
        logger.info(f"Attempting to terminate '{service_name}' (PID: {pid})...")
        parent_proc = psutil.Process(pid)
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(pid), '/T', '/F'], check=True, capture_output=True)
        else: 
            children = parent_proc.children(recursive=True)
            for child in children:
                try: child.terminate()
                except psutil.NoSuchProcess: pass
            parent_proc.terminate()
            gone, alive = psutil.wait_procs(children + [parent_proc], timeout=3)
            for p in alive: p.kill()
        
        if psutil.pid_exists(pid): time.sleep(0.5)
        if psutil.pid_exists(pid):
            logger.warning(f"Process {pid} for {service_name} might still be running after termination attempt.")
            return False 
        
        logger.info(f"Successfully issued termination for '{service_name}' (PID: {pid}).")
        proc_info["status"] = "stopped"
    except psutil.NoSuchProcess: 
        logger.info(f"Process for '{service_name}' (PID: {pid}) already gone before termination.")
        proc_info["status"] = "stopped"
    except subprocess.CalledProcessError as e: 
        logger.error(f"taskkill failed for '{service_name}' (PID: {pid}): {e.stderr.decode(errors='ignore') if e.stderr else 'No stderr'}")
        return False
    except Exception as e:
        logger.error(f"Failed to terminate '{service_name}' (PID: {pid}): {e}")
        return False
    finally: 
        if proc_info["status"] == "stopped":
            proc_info["pid"] = None; proc_info["process_handle"] = None
            if proc_info.get("log_file_handle") and not proc_info["log_file_handle"].closed:
                proc_info["log_file_handle"].write(f"\n--- Process '{service_name}' terminated at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                proc_info["log_file_handle"].close(); proc_info["log_file_handle"] = None
    return proc_info["status"] == "stopped"


def get_process_info(service_name: str) -> dict | None:
    """Returns the full process info dictionary for a service_name, updating status if needed."""
    proc_info = managed_processes.get(service_name)
    if not proc_info: return None

    if proc_info["status"] == "running":
        pid_exists_check = proc_info["pid"] and psutil.pid_exists(proc_info["pid"])
        handle_poll_check = proc_info["process_handle"] and proc_info["process_handle"].poll() is not None

        if not pid_exists_check or handle_poll_check:
            msg = ""
            if not pid_exists_check: msg = f"Process for '{service_name}' (PID: {proc_info['pid']}) no longer exists."
            else: msg = f"Process handle for '{service_name}' indicates process exited (return code: {proc_info['process_handle'].returncode})."
            logger.info(msg)
            
            proc_info["status"] = "stopped"; proc_info["pid"] = None; proc_info["process_handle"] = None
            if proc_info.get("log_file_handle") and not proc_info["log_file_handle"].closed:
                proc_info["log_file_handle"].write(f"\n--- Process '{service_name}' detected as stopped/exited at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                proc_info["log_file_handle"].close(); proc_info["log_file_handle"] = None
    return proc_info

# --- Monitoring Functions ---
def start_monitoring():
    global monitoring_active; monitoring_active = True
    logger.info("Process monitoring started.")

def stop_monitoring():
    global monitoring_active; monitoring_active = False
    logger.info("Process monitoring stopped.")

def monitor_and_restart_processes():
    if not monitoring_active: return
    logger.debug(f"Running monitor cycle at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
    for service_name, proc_info_snapshot in list(managed_processes.items()):
        proc_info = get_process_info(service_name) # Refreshes current status
        if not proc_info: continue

        config = proc_info["config"]
        should_auto_restart = config.get("AutoRestart", True) and not proc_info.get("user_stopped", False)

        if proc_info["status"] == "stopped" and should_auto_restart:
            current_time = time.time()
            proc_info["restart_history"] = [t for t in proc_info.get("restart_history", []) if current_time - t < RESTART_INTERVAL_SECONDS]

            if len(proc_info["restart_history"]) < MAX_RESTARTS_IN_INTERVAL:
                logger.info(f"Service '{service_name}' found stopped and eligible for restart. Attempting restart...")
                restart_delay = config.get("RestartDelaySeconds", DEFAULT_RESTART_DELAY_SECONDS)
                logger.debug(f"Waiting {restart_delay}s before restarting '{service_name}'.")
                time.sleep(restart_delay) 

                if launch_process(service_name):
                    logger.info(f"Service '{service_name}' restarted successfully.")
                    proc_info["restart_history"].append(current_time)
                else:
                    logger.error(f"Service '{service_name}' failed to restart.")
                    proc_info["status"] = "error_restarting" 
            else:
                logger.warning(f"Service '{service_name}' has restarted too many times recently. Not restarting.")
                proc_info["status"] = "error_restart_limit" 
    logger.debug("Monitor cycle finished.")


# --- Main (for testing this module directly) ---
if __name__ == "__main__":
    logger.info("--- Starting Process Manager Direct Test ---")
    # CONFIG_FILE_PATH is already set to project_root/server_config.json

    dummy_config_content = [
        { "ServiceName": "TestEcho", "FriendlyName": "Test Echo CMD", "AppPath": "cmd.exe", 
          "AppArguments": "/c echo TestEcho service running for 8s && timeout /t 8 /nobreak", 
          "LogDirectory": "logs_pm_test", "AutoRestart": True },
        { "ServiceName": "TestPythonLoop", "FriendlyName": "Test Python Loop", "AppPath": "python.exe", 
          "AppArguments": "-u -c \"import time; print('TestPythonLoop started', flush=True); [time.sleep(1) for _ in range(20)]; print('TestPythonLoop finished', flush=True)\"",
          "LogDirectory": "logs_pm_test", "AutoRestart": False }
    ]
    logs_test_dir_abs = os.path.join(PROJECT_ROOT, "logs_pm_test")
    if not os.path.exists(logs_test_dir_abs): os.makedirs(logs_test_dir_abs, exist_ok=True)
    
    # Create dummy config if it doesn't exist for the test
    if not os.path.exists(CONFIG_FILE_PATH) or "TestEcho" not in open(CONFIG_FILE_PATH).read() : # cheap check
        logger.info(f"Creating dummy config at {CONFIG_FILE_PATH} for testing.")
        with open(CONFIG_FILE_PATH, 'w') as f: json.dump(dummy_config_content, f, indent=2)
    else:
        logger.info(f"Using existing config at {CONFIG_FILE_PATH}.")

    if load_configuration():
        logger.info("\n--- Initial Status ---")
        for name_iter in list(managed_processes.keys()):
            info = get_process_info(name_iter)
            if info: logger.info(f"  {name_iter}: Status - {info['status']}, PID - {info['pid']}, UserStopped - {info.get('user_stopped')}")

        start_monitoring()

        logger.info("\n--- Launching all processes from config ---")
        for name_iter in list(managed_processes.keys()):
            logger.info(f"Attempting to launch {name_iter} via main test harness...")
            launch_process(name_iter) # This now sets user_stopped to False implicitly
            info = get_process_info(name_iter)
            if info: logger.info(f"  {name_iter}: Status - {info['status']}, PID - {info['pid']}")

        logger.info("\n--- Monitoring for 25 seconds (TestEcho should finish and restart, TestPythonLoop should keep running) ---")
        for i in range(5): 
            time.sleep(5)
            monitor_and_restart_processes()
            logger.info("  --- Post-Monitor Status Check ---")
            for name_iter in list(managed_processes.keys()):
                info = get_process_info(name_iter)
                if info: logger.info(f"    {name_iter}: Status - {info['status']}, PID - {info['pid']}, Restarts - {len(info.get('restart_history',[]))}, UserStopped - {info.get('user_stopped')}")
        
        logger.info("\n--- Manually stopping TestPythonLoop (as user_stopped=True) ---")
        terminate_process("TestPythonLoop", mark_user_stopped=True)
        info_loop = get_process_info("TestPythonLoop")
        if info_loop: logger.info(f"  TestPythonLoop: Status - {info_loop['status']}, PID - {info_loop['pid']}, UserStopped - {info_loop.get('user_stopped')}")

        logger.info("\n--- Monitoring for 10 more seconds (TestPythonLoop should NOT restart) ---")
        for i in range(2):
            time.sleep(5)
            monitor_and_restart_processes()
            logger.info("  --- Post-Monitor Status Check ---")
            for name_iter in list(managed_processes.keys()):
                info = get_process_info(name_iter)
                if info: logger.info(f"    {name_iter}: Status - {info['status']}, PID - {info['pid']}, Restarts - {len(info.get('restart_history',[]))}, UserStopped - {info.get('user_stopped')}")

        logger.info("\n--- Terminating all remaining processes ---")
        stop_monitoring()
        for name_iter in list(managed_processes.keys()):
            terminate_process(name_iter, mark_user_stopped=False) # Terminate without marking as user_stopped to test restart if monitor was hypothetically on
        
        logger.info("\n--- Final Status Check ---")
        for name_iter in list(managed_processes.keys()):
            info = get_process_info(name_iter)
            if info: logger.info(f"  {name_iter}: Status - {info['status']}, PID - {info['pid']}")
        
        logger.info("\n--- Test Cleanup: Closing log file handles ---")
        for name_iter in list(managed_processes.keys()):
            proc_info = managed_processes.get(name_iter)
            if proc_info and proc_info.get("log_file_handle") and not proc_info["log_file_handle"].closed:
                logger.info(f"Closing log file handle for {name_iter}")
                proc_info["log_file_handle"].close(); proc_info["log_file_handle"] = None
        
        logger.info("Test completed. Manual cleanup of dummy config and logs_pm_test directory may be needed if not done automatically.")

```
