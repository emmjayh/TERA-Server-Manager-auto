# Python Process Manager & GUI

## 1. Overview

The Python Process Manager & GUI is a Python application designed to directly launch, monitor, and manage your existing `.bat` or `.exe` applications. It ensures these applications are kept running by providing automatic restart-on-failure capabilities, handled internally by its `process_manager.py` module. The system features a Tkinter/CustomTkinter based Graphical User Interface (GUI) for easy visual monitoring, control, and configuration of the managed processes.

This system relies on a central configuration file (`server_config.json`) to define the applications to be managed. The primary way to interact with the system is via the Python GUI, launched using the `start_gui.bat` script.

## 2. Features

*   Directly launches and manages existing `.bat` and `.exe` applications as persistent processes.
*   **Automatic Restart-on-Failure:** The `process_manager.py` module monitors managed processes and automatically restarts them if they terminate unexpectedly (respecting restart count limits and delays).
*   **Application Log Management:** Redirects `stdout` and `stderr` of each managed application to dedicated log files (e.g., `ServiceName_app.log`) in a user-configurable directory.
*   **Process Manager Logging:** The `process_manager.py` module itself logs its operations to `logs_manager/process_manager.log`.
*   **Graphical User Interface (Tkinter/CustomTkinter):**
    *   Visual display of all configured processes, their status (running, stopped, error, etc.), and Process IDs (PIDs).
    *   Color-coded status indicators for quick assessment.
    *   In-row "Start" and "Stop" buttons for individual process control.
    *   Global "Start All" and "Stop All" buttons.
    *   Manual "Refresh Status" button.
    *   Auto-refresh of the process list.
    *   **Configuration Editor:**
        *   Allows adding, editing, and removing process configurations.
        *   Saves changes directly to `server_config.json`.
        *   Features "Auto-detect Application Paths" based on a TERA server base directory and predefined cues (`service_path_cues.py`).
        *   Supports defining a "Startup Delay (seconds)" for each process.
    *   **Programmable Startup Delay:** Processes configured with a startup delay are automatically started by the GUI after the specified interval from GUI launch, if currently stopped and not manually stopped by the user.
*   **Centralized Configuration:** All managed applications are defined in a single `server_config.json` file.
*   **Easy Launch:** Uses `start_gui.bat` to simplify starting the Python GUI application.

## 3. File Structure

The recommended directory layout for the application is as follows:

```
WindowsAppLauncher/
├── python_gui/                     # Python GUI application files
│   ├── app_tk.py                   # Main Python GUI application script (Tkinter/CustomTkinter)
│   ├── process_manager.py          # Core logic for launching, monitoring, and restarting processes
│   ├── service_utils.py            # Utility functions for config file I/O (used by GUI config editor)
│   ├── service_path_cues.py        # Definitions for auto-detecting paths
│   ├── requirements.txt            # Python dependencies for the GUI
│   └── test_service_utils.py       # Unit tests for service_utils.py (may need renaming/refocusing)
├── logs_manager/                   # Logs for process_manager.py itself
│   └── process_manager.log         # (Example log file)
├── test_apps/                      # Dummy applications for testing (optional)
│   ├── continuous_loop.bat
│   ├── quick_exit.bat
│   ├── error_exit.bat
│   ├── dummy_app.cs
│   └── dummy_app.exe               # (Compiled from dummy_app.cs)
├── server_config.template.json     # Template for the configuration file
├── server_config.json              # User's actual configuration (created from template)
├── start_gui.bat                   # Batch script to launch the Python GUI
└── README.md                       # This documentation file
```
*(Note: The `logs_manager/` directory will be created automatically if it doesn't exist when `process_manager.py` first attempts to log.)*

## 4. Prerequisites

*   **Operating System:** Windows 10 / Windows Server 2016 or later.
*   **Python Installation:** Python 3.x installed (e.g., Python 3.7 or newer). The Python Launcher for Windows (`py.exe`) is typically installed by default with Python from python.org and is recommended for use with `start_gui.bat`. Alternatively, ensure `python` is in your system's PATH.
*   **Python Dependencies:**
    *   The required Python libraries are listed in `python_gui/requirements.txt`.
    *   To install them, navigate to the project's root directory in your terminal and run:
        ```bash
        pip install -r python_gui/requirements.txt
        ```
    *   This will install `customtkinter` and `psutil`.
*   **User's Applications:** The actual `.bat` or `.exe` files you wish to manage must already be present on your system at known locations. This system *does not* install your application software.
*   **Administrative Privileges:** May be required by the applications being managed if they need to perform privileged operations. The Python GUI itself does not directly require admin rights to run, but starting/stopping some external applications might.

## 5. Setup and Configuration

### Download/Copy System Files
Copy all files and folders from this system (maintaining the structure above) to a directory on your Windows machine (e.g., `C:\Tools\PythonProcessManager`).

### Configure `server_config.json`
1.  In the project root directory, copy `server_config.template.json` and rename it to `server_config.json`.
2.  Edit `server_config.json` to define the applications you want to manage. This file is a JSON array of objects, where each object represents an application.

    **Fields for each application object:**
    *   `FriendlyName` (string): A human-readable name for the application, displayed in the GUI.
    *   `ServiceName` (string): A **unique identifier** for this managed process entry (e.g., `MyWebApp1`). This name is used internally by the manager and should not contain spaces or special characters.
    *   `AppPath` (string): The **full and absolute path** to your **pre-existing** `.bat` or `.exe` application file (e.g., `C:\MyApps\run_my_app.bat`). Use double backslashes (`\\`) for paths in JSON. This can also be auto-detected using the GUI's configuration editor.
    *   `AppArguments` (string, optional): Any command-line arguments to pass to your application when it's launched.
    *   `LogDirectory` (string): The **full and absolute path** to the directory where this application's console output (stdout/stderr) log files will be stored (e.g., `C:\AppLogs\MyWebApp1Logs`). The system will create a file like `MyWebApp1_app.log` in this directory. Use double backslashes in JSON.
    *   `StartupDelaySeconds` (integer, optional): If greater than 0, the GUI will wait this many seconds after its own launch before attempting to automatically start this process (if it's stopped and not manually stopped by the user). Defaults to 0 (no GUI-triggered delayed start) if omitted.
    *   `AutoRestart` (boolean, optional): Set to `true` (default) to allow the `process_manager.py` to automatically restart this process if it terminates unexpectedly. Set to `false` to disable auto-restarts for this specific process.
    *   `RestartDelaySeconds` (integer, optional): Seconds to wait before attempting an auto-restart after a crash. Defaults to 5 seconds (controlled by `DEFAULT_RESTART_DELAY_SECONDS` in `process_manager.py`).
    *   `MaxRestartsInInterval` (integer, optional): Maximum number of auto-restarts allowed within the `RestartIntervalSeconds`. Defaults to 3 (controlled by `MAX_RESTARTS_IN_INTERVAL` in `process_manager.py`).
    *   `RestartIntervalSeconds` (integer, optional): The time window (in seconds) during which restarts are counted towards `MaxRestartsInInterval`. Defaults to 60 seconds (controlled by `RESTART_INTERVAL_SECONDS` in `process_manager.py`).

    **Example `server_config.json` snippet:**
    ```json
    [
      {
        "FriendlyName": "My Web Server",
        "ServiceName": "WebServer01",
        "AppPath": "C:\\Apps\\MyWebServer\\start.bat",
        "AppArguments": "--port 8080",
        "LogDirectory": "C:\\AppLogs\\WebServer01",
        "StartupDelaySeconds": 5,
        "AutoRestart": true 
      },
      {
        "FriendlyName": "Data Processing Task",
        "AppPath": "C:\\Apps\\DataTasks\\processor.exe",
        "AppArguments": "--config C:\\Apps\\DataTasks\\prod.json",
        "LogDirectory": "C:\\AppLogs\\DataProcessor",
        "ServiceName": "DataProc01",
        "AutoRestart": false 
      }
    ]
    ```

## 6. Usage: Running and Using the GUI

The primary way to manage your processes is through the Python GUI.

1.  **Ensure Prerequisites:** Verify Python is installed and dependencies from `python_gui/requirements.txt` are installed.
2.  **Navigate:** Open a command prompt or terminal in the project's root directory (e.g., `C:\Tools\PythonProcessManager`).
3.  **Launch:**
    *   Double-click `start_gui.bat`.
    *   Or, from the command line in the project root: `start_gui.bat`
    *   Or, directly using Python (from project root): `py python_gui/app_tk.py`

The "Windows Process Manager (Tkinter)" window will appear.

### GUI Features Explained:
Refer to Section 8 in the previous `README.md` version (Turn 86) for a detailed breakdown of GUI features, as these remain largely the same in terms of user interaction patterns (Main Window, Configuration Editor, Add/Edit Dialog). The key difference is that it's now managing direct processes, not Windows Services.

**Key Interaction Points:**
*   **Main Process List:** View status, PID, and use in-row "Start"/"Stop" buttons.
*   **"Edit Configurations" Button:** Access the editor to modify `server_config.json`. This is where you add new applications to manage, change paths, arguments, delays, and auto-restart behavior.
*   **"Start All" / "Stop All" Buttons:** Global controls for all configured processes.
*   **"Refresh Status" Button:** Manually updates the displayed status of all processes.
*   **Auto-Detection in Config Editor:** Use the "TERA Server Base Directory" and "Auto-detect App Paths" to help fill in `AppPath` values for your configured processes.

## 7. Restart-on-Failure (Process Monitoring)

The `python_gui/process_manager.py` module includes a monitoring loop that runs in a separate thread when the GUI is active.
*   It periodically checks the status of processes that are supposed to be running (i.e., were launched by the manager and not manually stopped by the user via the GUI).
*   If a monitored process is found to have terminated unexpectedly (crashed or exited), the manager will attempt to restart it automatically.
*   This restart behavior considers:
    *   The `AutoRestart` setting in `server_config.json` for that process.
    *   A configurable delay before attempting restart (`RestartDelaySeconds`).
    *   A limit on how many times a process can be restarted within a specific time window (`MaxRestartsInInterval` and `RestartIntervalSeconds`) to prevent rapid failing processes from consuming excessive resources.
*   The `user_stopped` flag for each process (managed internally) ensures that processes intentionally stopped via the GUI are not automatically restarted by the monitor.

## 8. Application Logging

*   **Process Manager Logs:** Operational logs from `process_manager.py` (e.g., loading configuration, starting/stopping processes, monitoring actions) are saved to `logs_manager/process_manager.log` and also printed to the console where `start_gui.bat` is run.
*   **Managed Application Logs:** The `stdout` and `stderr` output of each application launched by the `process_manager.py` is redirected to a dedicated log file (e.g., `MyWebApp1_app.log`). The location of these logs is determined by the `LogDirectory` field specified for each entry in `server_config.json`. These files are appended to, with markers for each launch/termination.

## 9. Packaging the GUI with PyInstaller (Optional)

To create a standalone executable from the Python GUI scripts for easier distribution:
1.  Ensure PyInstaller is installed: `pip install pyinstaller`.
2.  Navigate to the project's root directory (`WindowsAppLauncher` or `PythonProcessManager`).
3.  Run a command similar to the following:
    ```bash
    pyinstaller --name ProcessManagerGUI_TK --onefile --windowed --add-data "python_gui/service_path_cues.py:python_gui" python_gui/app_tk.py
    ```
    *   `--name ProcessManagerGUI_TK`: Name of the output executable.
    *   `--onefile`: Bundles everything into a single `.exe`.
    *   `--windowed`: Prevents a console window from appearing when the `.exe` is run.
    *   `--add-data "python_gui/service_path_cues.py:python_gui"`: Ensures `service_path_cues.py` is included in the correct relative path for the GUI to find it. You might need similar `--add-data` flags if other non-code assets were used or if PyInstaller misses auto-detecting `service_utils.py` (though direct imports usually work).
    *   `python_gui/app_tk.py`: The main script for the GUI.
4.  The executable will be found in the `dist/` folder.
5.  To run the packaged application, place the generated `.exe` file in the project root directory (i.e., alongside `server_config.json` and the `python_gui` folder if helper modules were not perfectly bundled, though `--onefile` aims to avoid this). For truly standalone execution where `server_config.json` is also in the same folder as the `.exe`, ensure paths in `process_manager.py` to `CONFIG_FILE_PATH` are adjusted or the file is indeed found next to the executable.
    *The current `CONFIG_FILE_PATH = os.path.normpath(os.path.join(PROJECT_ROOT, "server_config.json"))` in `process_manager.py` assumes it's relative to the script's location within the bundle, then up to a "project root". This might need adjustment for a packaged app if `server_config.json` isn't automatically found or if a different location strategy is desired.*

## 10. Auto-Starting the GUI Application on Windows Login

Refer to the "Auto-Starting the GUI Application on Windows Login" section from Turn 96/97 (Method 1: Startup Folder, Method 2: Task Scheduler, using `start_gui.bat`). This section remains relevant.

## 11. Troubleshooting

*   **Configuration File:** Ensure `server_config.json` is present in the project root, is valid JSON, and all `AppPath` and `LogDirectory` entries are correct, absolute paths with double backslashes (`\\`).
*   **Python Environment:** Verify Python is installed and accessible (via `py` launcher or `python` in PATH). Ensure dependencies from `python_gui/requirements.txt` are installed.
*   **File Locations:** When running from source, ensure `app_tk.py`, `service_utils.py`, and `service_path_cues.py` are in the `python_gui` directory, and you run `start_gui.bat` or `py python_gui/app_tk.py` from the project root.
*   **Application Logs:** Check the individual application logs in the directories specified by `LogDirectory` in your config. These show the direct output of your managed applications.
*   **Process Manager Logs:** Check `logs_manager/process_manager.log` for insights into what the manager itself is doing.
*   **Console Output:** When running `start_gui.bat`, the console window will display live logging from `process_manager.py`. Look for errors here.

```
