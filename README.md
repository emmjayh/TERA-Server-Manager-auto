# Windows App Launcher and Service Manager

## 1. Overview

The Windows App Launcher and Service Manager is a suite of tools designed to manage your existing `.bat` or `.exe` applications by running them as robust Windows services. It ensures that these pre-existing applications are always running by providing automatic restart-on-failure capabilities (handled by the Windows Service Control Manager when the application is registered as a service).

This system provides two primary methods for management:
1.  A comprehensive set of **PowerShell scripts** for command-line based registration, control, and status checking.
2.  A **Python-based Graphical User Interface (GUI)** using Tkinter/CustomTkinter for visual monitoring and management of the services.

Both methods rely on a central configuration file (`server_config.json`) to define the applications to be managed.

## 2. Features

*   Manages both existing `.bat` and `.exe` applications as Windows Services.
*   Automatic restart on application/service failure (configured via standard Windows Service recovery options once registered).
*   Individual, timestamped log files for each managed application's console output (stdout and stderr).
*   PowerShell scripts for easy registration, starting, stopping, status checking, and uninstallation of all configured services.
*   A Python GUI application (Tkinter/CustomTkinter) for visual status display, service control (start/stop individual or all), and configuration editing.
*   **Programmable Startup Delay (GUI):** Services can be configured with a startup delay. The GUI application will attempt to start these services automatically after the specified delay (in seconds) from when the GUI itself launches, provided the service is currently stopped.
*   **Auto-detect Application Paths (GUI):** The GUI's configuration editor can attempt to automatically locate application paths based on a specified TERA server base directory and predefined search cues.
*   Centralized configuration via a single JSON file (`server_config.json`) detailing which existing applications to manage.
*   Batch script (`start_gui.bat`) for easy launching of the Python GUI, using the `py` Python launcher.

## 3. File Structure

The recommended directory layout for the application is as follows:

```
WindowsAppLauncher/
├── scripts/
│   ├── launch_bat.ps1              # Helper script to launch .bat files
│   ├── launch_exe.ps1              # Helper script to launch .exe files
│   ├── New-AppWindowsService.ps1   # Core script to create a single service wrapper
│   ├── Install-ServerParts.ps1     # Registers all configured applications as services
│   ├── Start-AllServerParts.ps1    # Starts all configured services
│   ├── Stop-AllServerParts.ps1     # Stops all configured services
│   ├── Get-ServerPartStatus.ps1    # Gets status for CLI or web UI
│   └── Uninstall-ServerParts.ps1   # Stops and removes all configured services
├── web_frontend/  (Optional - for PowerShell Web Dashboard)
│   ├── status_dashboard.html
│   └── Start-StatusWebServer.ps1
├── test_apps/                      # Dummy applications for testing
│   ├── continuous_loop.bat
│   ├── quick_exit.bat
│   ├── error_exit.bat
│   ├── dummy_app.cs
│   └── dummy_app.exe               # (Compiled from dummy_app.cs)
├── python_gui/                     # Python GUI application files
│   ├── app_tk.py                   # Main Python GUI application script (Tkinter/CustomTkinter)
│   ├── service_utils.py            # Utility functions for Python GUI (service interaction, config)
│   ├── service_path_cues.py        # Definitions for auto-detecting paths
│   ├── requirements.txt            # Python dependencies for the GUI
│   └── test_service_utils.py       # Unit tests for service_utils.py
├── server_config.template.json     # Template for the configuration file
├── start_gui.bat                   # Batch script to launch the Python GUI
└── README.md                       # This documentation file
```

## 4. Prerequisites - General

*   **Operating System:** Windows 10 / Windows Server 2016 or later.
*   **User's Applications:** The actual `.bat` or `.exe` files you wish to manage must already be present on your system at known locations. This system *does not* install your application software.
*   **Administrative Privileges:** Required for registering, starting, stopping, and uninstalling Windows services (via PowerShell scripts or the GUI performing these actions).

## 5. Prerequisites - PowerShell Management

*   **PowerShell:** Version 5.1 or later (typically pre-installed).

## 6. Setup and Configuration (Shared)

### Download/Copy Management System Files
Copy all the files and folders of this management system (maintaining the structure above) to a directory on your Windows server (e.g., `C:\Tools\WindowsAppLauncher`).

### Configure `server_config.json`
1.  Copy `server_config.template.json` and rename it to `server_config.json` in the root directory of the management system.
2.  Edit `server_config.json` to define the existing applications you want to manage as services. It's a JSON array of objects, where each object represents an application to be managed.

    **Fields for each application object:**
    *   `FriendlyName` (string): A human-readable name for the application.
    *   `AppPath` (string): The **full and absolute path** to your **pre-existing** `.bat` or `.exe` application file. Use double backslashes in JSON (e.g., `C:\\Path\\To\\Your\\ExistingApp.exe`). Can also be auto-detected by the Tkinter GUI.
    *   `AppArguments` (string, optional): Any command-line arguments to pass to your application.
    *   `LogDirectory` (string): The **full and absolute path** to the directory where this managed application's console output log files will be stored. Use double backslashes in JSON.
    *   `ServiceName` (string): A unique name for the Windows service that will wrap your application. Must not contain spaces or special characters.
    *   `StartupDelaySeconds` (integer, optional): If greater than 0, the Python GUI application will wait this many seconds after its own launch before attempting to start this service, but only if the service is found to be in a "stopped" state. Defaults to 0 if omitted.

    **Example `server_config.json` snippet:**
    ```json
    [
      {
        "FriendlyName": "Hub Server Application",
        "AppPath": "C:\\MyCompany\\Apps\\HubServer\\hubServer.bat",
        "AppArguments": "/config:hub.json",
        "LogDirectory": "C:\\AppLauncherLogs\\HubServer",
        "ServiceName": "HubServerSvc",
        "StartupDelaySeconds": 5
      },
      {
        "FriendlyName": "Data Processing Utility",
        "AppPath": "D:\\InstalledPrograms\\DataProc\\processor.exe",
        "AppArguments": "--mode=production --threads=4",
        "LogDirectory": "C:\\AppLauncherLogs\\DataProcessor",
        "ServiceName": "DataProcessorSvc"
      }
    ]
    ```

## 7. PowerShell Script Management

This section details how to manage services using the PowerShell scripts. The `server_config.json` should be in the root project directory when running these scripts.

### Registering Applications as Services
(Requires Admin privileges)
```powershell
# Navigate to project root
.\scripts\Install-ServerParts.ps1 -ConfigFilePath ".\server_config.json" -LauncherScriptDirectory ".\scripts" -ServiceScriptPath ".\scripts\New-AppWindowsService.ps1"
```

### Starting All Registered Services
(Requires Admin privileges)
```powershell
.\scripts\Start-AllServerParts.ps1 -ConfigFilePath ".\server_config.json"
```

### Stopping All Registered Services
(Requires Admin privileges)
```powershell
.\scripts\Stop-AllServerParts.ps1 -ConfigFilePath ".\server_config.json"
```

### Checking Status (Command Line)
```powershell
.\scripts\Get-ServerPartStatus.ps1 -ConfigFilePath ".\server_config.json"
```

### Uninstalling (Unregistering) Services
(Requires Admin privileges)
```powershell
.\scripts\Uninstall-ServerParts.ps1 -ConfigFilePath ".\server_config.json"
```

## 8. Windows Service Manager GUI (Tkinter/CustomTkinter)

The Python-based GUI provides a visual way to monitor and manage services.

### Prerequisites (for GUI)
*   **Python Installation:** Python 3.x installed (e.g., Python 3.7 or newer). The Python Launcher for Windows (`py.exe`) is typically installed by default with Python from python.org and is recommended for use with `start_gui.bat`. Alternatively, ensure `python` is in your system's PATH.
*   **Python Dependencies:**
    *   The required Python libraries are listed in `python_gui/requirements.txt`.
    *   To install them, navigate to the project's root directory in your terminal and run:
        ```bash
        pip install -r python_gui/requirements.txt
        ```
    *   This will install `customtkinter` and `psutil`.
*   The `server_config.json` file (in the project root) should be configured.
*   The `service_utils.py` and `service_path_cues.py` scripts must be in the `python_gui` directory.

***Note:** If using a pre-packaged version of the GUI (e.g., `ServiceManagerGUI_TK.exe`), Python and the above dependencies do not need separate installation.*

### Running the GUI Application

To run the GUI application:
1.  Ensure Python is installed (and the `py` launcher is available or `python` is in PATH).
2.  Navigate to the project's root directory (e.g., `C:\Tools\WindowsAppLauncher`).
3.  Double-click the `start_gui.bat` file. This script uses the `py` Python launcher.

Alternatively, you can run it from the command line:
```bash
# From the project root directory
start_gui.bat
```
Or, if you prefer to call Python directly (from the project root directory, using the `py` launcher or `python` if in PATH):
```bash
py python_gui/app_tk.py
```

#### Running the Packaged GUI Application (If available)
If a packaged version (e.g., `ServiceManagerGUI_TK.exe`) is available:
1.  Place the executable (e.g., `ServiceManagerGUI_TK.exe`) in a dedicated folder.
2.  Place your `server_config.json` file in the **same directory** as the executable.
3.  Double-click the executable to run it.

### GUI Features

#### Main Window
*   **Service List:** Displays a scrollable list of all configured services. Each row shows:
    *   Friendly Name
    *   Service Name
    *   Current Status (e.g., Running, Stopped, Not Found) - Color-coded for readability.
    *   Process ID (PID) if running.
    *   **Actions Column:** Contains "Start" and "Stop" buttons for each individual service. These buttons are enabled/disabled based on the current service status.
*   **Status Bar:** Located at the bottom, displays messages about ongoing operations or errors.
*   **Control Buttons:**
    *   **"Edit Configurations"**: Opens the Configuration Editor window.
    *   **"Start All Services"**: Attempts to start all services listed in the configuration that are currently stopped or not found.
    *   **"Stop All Services"**: Attempts to stop all services listed in the configuration that are currently running or paused.
    *   **"Refresh Status"**: Manually reloads the status of all services.
*   **Auto-Refresh:** The service list automatically refreshes every 10 seconds.
*   **Delayed Startup:** On application launch (and after configuration changes), services configured with `StartupDelaySeconds > 0` in `server_config.json` will be automatically started after the specified delay if they are currently stopped.

#### Configuration Editor Window (`Edit Configurations...`)
This modal dialog allows for managing the `server_config.json` file content:
*   **TERA Server Base Directory Input:**
    *   An input field and "Browse..." button to select the root directory of your TERA server installation. This path is used by the auto-detect feature.
*   **"Auto-detect App Paths" Button:**
    *   Uses the specified Base Directory and predefined cues (from `service_path_cues.py`) to automatically find and populate the "Application Path" for services in the list below.
    *   Provides a summary of found/not found paths.
*   **Service Configuration List:**
    *   Displays the current services from the configuration in a simplified list (Friendly Name, Service Name, App Path).
    *   Allows selection of a service to Edit or Remove.
*   **Control Buttons:**
    *   **"Add Service..."**: Opens the Add/Edit Service dialog to define a new service.
    *   **"Edit Service..."**: Opens the Add/Edit Service dialog populated with data from the selected service.
    *   **"Remove Service"**: Removes the selected service from the list (after confirmation).
*   **"Save Changes" Button:** Saves the current state of the service list (additions, edits, removals) back to `server_config.json`.
*   **"Cancel" Button:** Closes the Configuration Editor without saving changes.

#### Add/Edit Service Dialog
This modal dialog is used for adding a new service or editing an existing one:
*   **Fields:**
    *   Friendly Name
    *   Service Name (read-only when editing)
    *   Application Path (manual input or "Browse..." file picker)
    *   Application Arguments (optional)
    *   Log Directory (manual input or "Browse..." directory picker)
    *   Startup Delay (seconds): Input for the delayed start feature (0-3600 seconds).
*   **Validation:** Ensures required fields are filled and Service Name has valid characters. Checks for duplicate Service Names when adding.
*   **"OK" Button:** Saves the new/edited service data and closes the dialog.
*   **"Cancel" Button:** Closes the dialog without saving.

### Packaging the GUI with PyInstaller (for distribution)
To create a standalone executable from the Python GUI scripts:
1.  Ensure PyInstaller is installed: `pip install pyinstaller`.
2.  Navigate to the project's root directory (`WindowsAppLauncher`).
3.  Run a command similar to the following:
    ```bash
    pyinstaller --name ServiceManagerGUI_TK --onefile --windowed --add-data "python_gui/service_path_cues.py:python_gui" python_gui/app_tk.py
    ```
    *   `--name ServiceManagerGUI_TK`: Name of the output executable.
    *   `--onefile`: Bundles everything into a single `.exe`.
    *   `--windowed`: Prevents a console window from appearing.
    *   `--add-data "python_gui/service_path_cues.py:python_gui"`: Ensures `service_path_cues.py` is included.
    *   `python_gui/app_tk.py`: The main script for the GUI.
4.  The executable will be found in the `dist/` folder.
5.  Distribute the generated `.exe` file along with `server_config.json` (placed in the same directory as the `.exe`).

## 9. Logging (Shared)

*   **Application Logs:** Output from managed `.bat` or `.exe` applications is redirected to log files in the `LogDirectory` specified in `server_config.json`.
*   **Service Events:** Windows Service events are logged in the Windows Event Log.
*   **PowerShell Script Output:** PowerShell scripts output to the console.
*   **GUI Feedback:** The Python GUI provides feedback via its status bar and message boxes.

## 10. Troubleshooting

*   **Paths in `server_config.json`:** Ensure `AppPath` and `LogDirectory` are full, absolute paths with double backslashes (`\\`).
*   **Admin Privileges:** Required for service management (PowerShell or GUI actions).
*   **Python GUI:**
    *   Ensure Python is installed and accessible via the `py` launcher or that `python` is in the system PATH for `start_gui.bat` to work.
    *   Ensure required dependencies are installed using `pip install -r python_gui/requirements.txt`.
    *   Verify `app_tk.py`, `service_utils.py`, and `service_path_cues.py` are correctly located in the `python_gui` folder and `server_config.json` is in the project root when running from source or via `start_gui.bat`.
    *   Check console output for errors when running `start_gui.bat` or `py python_gui/app_tk.py`.

```
