# Windows App Launcher and Service Manager

## 1. Overview

The Windows App Launcher and Service Manager is a suite of tools designed to manage your existing `.bat` or `.exe` applications by running them as robust Windows services. It ensures that these pre-existing applications are always running by providing automatic restart-on-failure capabilities (handled by the Windows Service Control Manager when the application is registered as a service).

This system provides two primary methods for management:
1.  A comprehensive set of **PowerShell scripts** for command-line based registration, control, and status checking.
2.  A **Python-based Graphical User Interface (GUI)** for visual monitoring and management of the services.

Both methods rely on a central configuration file (`server_config.json`) to define the applications to be managed.

## 2. Features

*   Manages both existing `.bat` and `.exe` applications as Windows Services.
*   Automatic restart on application/service failure (configured via standard Windows Service recovery options once registered).
*   Individual, timestamped log files for each managed application's console output (stdout and stderr).
*   PowerShell scripts for easy registration, starting, stopping, status checking, and uninstallation of all configured services.
*   A Python GUI application for visual status display, service control (start/stop individual or all), and configuration editing.
*   **Programmable Startup Delay (GUI):** Services can be configured with a startup delay. The GUI application will attempt to start these services automatically after the specified delay (in seconds) from when the GUI itself launches, provided the service is currently stopped. This is useful for staggering the startup of multiple resource-intensive services.
*   **Auto-detect Application Paths (GUI):** The GUI's configuration editor can attempt to automatically locate application paths based on a specified TERA server base directory and predefined search cues.
*   Centralized configuration via a single JSON file (`server_config.json`) detailing which existing applications to manage.

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
├── web_frontend/
│   ├── status_dashboard.html       # The HTML, CSS, and JS for the (optional) web UI
│   └── Start-StatusWebServer.ps1   # Script to start the web server for the UI
├── test_apps/                      # Dummy applications for testing
│   ├── continuous_loop.bat
│   ├── quick_exit.bat
│   ├── error_exit.bat
│   ├── dummy_app.cs
│   └── dummy_app.exe               # (Compiled from dummy_app.cs)
├── python_gui/                     # Python GUI application files
│   ├── main_gui.py                 # Main Python GUI application script
│   ├── service_utils.py            # Utility functions for Python GUI (service interaction, config)
│   ├── service_path_cues.py        # Definitions for auto-detecting paths
│   ├── requirements.txt            # Python dependencies for the GUI (NEW)
│   └── test_service_utils.py       # Unit tests for service_utils.py
├── server_config.template.json     # Template for the configuration file
└── README.md                       # This documentation file
```
*(Note: The `python_gui/` directory is a conceptual grouping; scripts might be in the root or a different structure as per your setup. Adjust paths accordingly.)*

## 4. Prerequisites - General

*   **Operating System:** Windows 10 / Windows Server 2016 or later.
*   **User's Applications:** The actual `.bat` or `.exe` files you wish to manage must already be present on your system at known locations. This system *does not* install your application software.
*   **Administrative Privileges:** Required for registering, starting, stopping, and uninstalling Windows services, and for running the web server or GUI on some ports or network configurations.

## 5. Prerequisites - PowerShell Management

*   **PowerShell:** Version 5.1 or later (typically pre-installed).

## 6. Setup and Configuration (Shared)

### Download/Copy Management System Files
Copy all the files and folders of this management system (maintaining the structure above) to a directory on your Windows server (e.g., `C:\Tools\WindowsAppLauncher`).

### Configure `server_config.json`
1.  Copy `server_config.template.json` and rename it to `server_config.json` in the root directory of the management system (or a designated configuration directory).
2.  Edit `server_config.json` to define the existing applications you want to manage as services. It's a JSON array of objects, where each object represents an application to be managed.

    **Fields for each application object:**
    *   `FriendlyName` (string): A human-readable name for the application (e.g., "My Awesome App"). Used in logs and the UI.
    *   `AppPath` (string): The **full and absolute path** to your **pre-existing** `.bat` or `.exe` application file (e.g., `C:\MyExistingApps\start_my_app.bat` or `D:\MyLegacyApp\run.exe`). **This is crucial and must point to an application file already on your disk.** Use double backslashes in JSON (e.g., `C:\\Path\\To\\Your\\ExistingApp.exe`). Can also be auto-detected by the GUI (see Section 8).
    *   `AppArguments` (string, optional): Any command-line arguments to pass to your application. If none, use an empty string `""`.
    *   `LogDirectory` (string): The **full and absolute path** to the directory where this managed application's console output log files will be stored (e.g., `C:\AppLauncherLogs\MyAwesomeAppLogs`). The launcher scripts will create this directory if it doesn't exist. Use double backslashes in JSON.
    *   `ServiceName` (string): A unique name for the Windows service that will wrap your application (e.g., `MyAwesomeAppSvc`). Must not contain spaces or special characters. Keep it short and descriptive.
    *   `StartupDelaySeconds` (integer, optional): If greater than 0, the Python GUI application will wait this many seconds after its own launch before attempting to start this service, but only if the service is found to be in a "stopped" state. Defaults to 0 (no automatic delayed start by the GUI) if omitted. This setting is primarily used by the Python GUI.

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

### Directory Paths in Scripts (Important Note)
The PowerShell management scripts (`Install-ServerParts.ps1`, `Start-StatusWebServer.ps1`) require paths to their dependencies. If you maintain the documented folder structure, the example commands should work with relative paths. If you rearrange, you **must** provide correct full or relative paths.

## 7. PowerShell Script Management

This section details how to manage services using the PowerShell scripts.

### Registering Applications as Services
(Requires Admin privileges)
To take your existing applications (defined in `server_config.json`) and register them as Windows services:
1.  Open PowerShell as **Administrator**.
2.  Navigate to the root directory (e.g., `cd C:\Tools\WindowsAppLauncher`).
3.  Run:
    ```powershell
    .\scripts\Install-ServerParts.ps1 -ConfigFilePath ".\server_config.json" -LauncherScriptDirectory ".\scripts" -ServiceScriptPath ".\scripts\New-AppWindowsService.ps1"
    ```
    This **does not install your application software**. It creates Windows Service wrappers for your existing applications.

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

### Checking Status of Managed Applications (Command Line)
```powershell
.\scripts\Get-ServerPartStatus.ps1 -ConfigFilePath ".\server_config.json"
```
To output as JSON:
```powershell
.\scripts\Get-ServerPartStatus.ps1 -ConfigFilePath ".\server_config.json" -OutputToJson
```

### Web Dashboard for Managed Applications (Optional)
1.  Start the Web Server (May require Admin privileges):
    ```powershell
    .\web_frontend\Start-StatusWebServer.ps1 -ConfigFilePath ".\server_config.json" -GetStatusScriptPath ".\scripts\Get-ServerPartStatus.ps1" -HtmlFilePath ".\web_frontend\status_dashboard.html"
    ```
2.  Access: `http://localhost:8088` (or your configured port).

### Uninstalling (Unregistering) Services
(Requires Admin privileges)
This stops and removes the Windows Service wrappers. It **does not** uninstall your actual application software.
```powershell
.\scripts\Uninstall-ServerParts.ps1 -ConfigFilePath ".\server_config.json"
```

## 8. Windows Service Manager GUI (Python)

In addition to the PowerShell scripts, a Python-based GUI application is available for managing and monitoring your services. To simplify initial setup, the Configuration Editor within the GUI includes a feature to auto-detect application paths based on a specified base server directory and common TERA file structures.

### Prerequisites (for GUI)
*   Python 3.x installed (e.g., Python 3.7 or newer).
*   **Python Dependencies:**
    *   The required Python libraries are listed in `python_gui/requirements.txt`.
    *   To install them, navigate to the project's root directory in your terminal and run:
        ```bash
        pip install -r python_gui/requirements.txt
        ```
    *   This will install `PyQt6` (for the graphical interface) and `psutil` (for service and process information).
*   The `server_config.json` file should be configured as described in the main "Setup and Configuration (Shared)" section.
*   The `service_utils.py` and `service_path_cues.py` scripts must be in the same directory as `main_gui.py` or accessible via the Python path.

***Note:** If you are using a pre-packaged version of the GUI (e.g., `ServiceManagerGUI.exe`), you do **not** need to install Python or the dependencies listed in `requirements.txt` separately.*

### Running the GUI Application

There are two ways to run the GUI application:

#### A. Running the Packaged GUI Application (Recommended for most users)
If a packaged version (e.g., `ServiceManagerGUI.exe`) is available:
1.  Ensure the executable (`ServiceManagerGUI.exe`) is in a dedicated folder (e.g., `C:\Tools\WindowsAppLauncher\gui_dist\`).
2.  Place your `server_config.json` file in the **same directory** as `ServiceManagerGUI.exe`.
3.  Simply double-click `ServiceManagerGUI.exe` to run it.

#### B. Running from Source (For development or if no packaged version is available)
1.  Ensure all prerequisites listed above are met (Python, and dependencies installed via `requirements.txt`).
2.  Navigate to the project's root directory (or the directory containing `main_gui.py`, `service_utils.py`, and `service_path_cues.py` e.g., `cd C:\Tools\WindowsAppLauncher\python_gui` or `cd C:\Tools\WindowsAppLauncher` if they are in root).
3.  Run the command: `python main_gui.py`
    *(If your python executable is named `python3`, use that instead).*

### GUI Features

#### Main Window
*   Displays a table of all configured services with their Friendly Name, Service Name, current Status (e.g., Running, Stopped, Not Found), and Process ID (PID).
*   Status is color-coded for quick visual identification (e.g., green for running, red for stopped).
*   The status display auto-refreshes every 10 seconds (or the configured interval).
*   A "Refresh Status" button allows for immediate manual refresh.

#### Menu Bar
*   **File > Exit**: Closes the application.
*   **Actions > Start All Services**: Attempts to start all configured services that are currently stopped or not found.
*   **Actions > Stop All Services**: Attempts to stop all configured services that are currently running or paused.
*   **Configuration > Edit Configurations...**: Opens the configuration editor dialog.

#### Service Controls (Main Window - Bottom Buttons)
*   Select a service in the table to enable the "Start Service" and "Stop Service" buttons.
*   **"Start Service"**: Attempts to start the selected service. Enabled if the service is currently stopped or reported as "Not Found".
*   **"Stop Service"**: Attempts to stop the selected service. Enabled if the service is currently running or paused.
*   Feedback on these actions is provided via message boxes and status bar updates.

#### Configuration Editor (`Edit Configurations...` Dialog)
This dialog allows you to manage the list of services and their properties. Key features include:
*   **TERA Server Base Directory Input:**
    *   A field to specify the main root directory where your TERA server files are located.
    *   A 'Browse...' button is provided to help select this directory.
*   **Auto-detect App Paths Button:**
    *   After setting the 'TERA Server Base Directory', click this button to let the application attempt to automatically find the `AppPath` for each service listed in the configuration.
    *   The detection uses a predefined set of common folder names (e.g., `hub`, `Executable/Bin`) and filename patterns (e.g., `Start.bat`, `*.ServiceName.bat`, `ServiceName.exe`) relevant to TERA server setups, defined in `service_path_cues.py`.
    *   A summary message will report how many paths were found and which services (if any) still require manual path configuration.
    *   Users should review the automatically detected paths for accuracy.
*   **Service Configuration Table:** Displays the current service configurations (Friendly Name, Service Name, Application Path).
*   **"Add..."**: Opens a dialog to add a new service configuration.
    *   Fields: Friendly Name, Service Name, Application Path (can be filled manually, via its own "Browse..." file picker, or by the "Auto-detect App Paths" feature above), Application Arguments, Log Directory (with "Browse..." directory picker), `Startup Delay (seconds)` (Optional: Number of seconds to wait after the GUI application launches before attempting to automatically start this service. This only applies if the service is initially stopped. Set to 0 for no automatic delayed start).
    *   Input validation is performed (e.g., required fields, Service Name format).
*   **"Edit..."**: Opens the same dialog populated with the selected service's data for modification. The Service Name field is read-only during edit mode, as it's the primary identifier.
*   **"Remove"**: Removes the selected service configuration from the list (after a confirmation dialog).
*   **"Save Changes"**: Saves all modifications (additions, edits, removals) back to the `server_config.json` file and closes the editor. The main window will then refresh its display.
*   **"Cancel"**: Discards any changes made in the editor and closes it.

## 9. Logging (Shared)

*   **Application Logs:** The stdout and stderr output of each launched application (that you've configured to be managed) are redirected to `.log` files. These are stored in the directory specified by the `LogDirectory` field in `server_config.json` for that application, with a timestamp in the filename (e.g., `MyApplication_2023-10-27_14-30-00.log`).
*   **Service Events:** Standard Windows Service events (start, stop, failure, recovery actions for the service wrappers) are logged to the Windows Event Log (typically under `System` or `Application`). Use `Event Viewer` (eventvwr.msc) to view these.
*   **Management Script Output (PowerShell):** The PowerShell management scripts write their output to the console. This can be redirected to a file if needed (e.g., `.\scripts\Install-ServerParts.ps1 ... > registration.log`).
*   **GUI Feedback:** Error messages or operational feedback from Python GUI actions are typically displayed in message boxes or the status bar.

## 10. Troubleshooting

*   **Paths:** Double-check that all paths in `server_config.json` (especially `AppPath` for your existing application and `LogDirectory`) are **full, absolute, and correct**. Remember to use double backslashes (`\\`) for paths in JSON. `AppPath` must point to an executable or batch file that is already on your system.
*   **Application Logs:** Examine the log files in the configured `LogDirectory` for your specific application. These logs contain the direct output from your `.bat` or `.exe` and will show any errors it reported when launched by the service.
*   **Services MMC:** Open the Services console (`services.msc`) to check the status of your registered service wrappers, their configuration (Log On As, Startup Type, Recovery settings), and dependencies.
*   **Windows Event Viewer:** Look in `Windows Logs > System` and `Windows Logs > Application` in Event Viewer for errors related to your service names.
*   **Administrator Privileges:** Ensure you are running scripts or the GUI (if performing actions like start/stop/edit config) with sufficient privileges.
*   **Script Parameters (PowerShell):** If you've changed the folder structure of this management system, ensure you are providing the correct paths to dependent scripts/files when calling `Install-ServerParts.ps1` or `Start-StatusWebServer.ps1`.
*   **Python GUI Issues:**
    *   Ensure Python is installed and the required dependencies are installed using `pip install -r python_gui/requirements.txt`.
    *   Verify `main_gui.py`, `service_utils.py`, and `service_path_cues.py` are in the expected locations relative to each other and `server_config.json`.
    *   If the GUI doesn't load or show data: Check the console output when running `python main_gui.py` for errors.
*   **Web Dashboard Issues:** If the web dashboard doesn't load or show data:
    *   Ensure `Start-StatusWebServer.ps1` is running and didn't report errors on startup.
    *   Check the browser's developer console (usually F12) for JavaScript errors or network errors when trying to fetch `/status`.
    *   Verify `Get-ServerPartStatus.ps1` runs correctly on its own and produces valid JSON.

```
