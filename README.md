# Windows App Launcher and Service Manager

## 1. Overview

The Windows App Launcher and Service Manager is a suite of PowerShell scripts designed to manage your existing `.bat` or `.exe` applications by running them as robust Windows services. It ensures that these pre-existing applications are always running by providing automatic restart-on-failure capabilities (handled by the Windows Service Control Manager when the application is registered as a service). The system also includes a web-based user interface to easily view the status of all configured applications.

## 2. Features

*   Manages both existing `.bat` and `.exe` applications as Windows Services.
*   Automatic restart on application/service failure (configured via standard Windows Service recovery options once registered).
*   Individual, timestamped log files for each managed application's console output (stdout and stderr).
*   PowerShell scripts for easy registration, starting, stopping, status checking, and uninstallation of all configured services.
*   A web-based dashboard to view the real-time status and Process ID (PID) of all configured applications.
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
│   ├── status_dashboard.html       # The HTML, CSS, and JS for the web UI
│   └── Start-StatusWebServer.ps1   # Script to start the web server for the UI
├── server_config.template.json     # Template for the configuration file
└── README.md                       # This documentation file
```

## 4. Prerequisites

*   **Operating System:** Windows 10 / Windows Server 2016 or later.
*   **PowerShell:** Version 5.1 or later (typically pre-installed).
*   **User's Applications:** The actual `.bat` or `.exe` files you wish to manage must already be present on your system at known locations. This system *does not* install your application software.
*   **Administrative Privileges:** Required for registering, starting, stopping, and uninstalling Windows services, and for running the web server on some ports or network configurations.

## 5. Setup and Configuration

### Download/Copy Management Scripts
Copy all the files and folders of this management system (maintaining the structure above) to a directory on your Windows server (e.g., `C:\Tools\WindowsAppLauncher`).

### Configure `server_config.json`
1.  Copy `server_config.template.json` and rename it to `server_config.json` in the root directory of the management system (or a designated configuration directory if you prefer, just ensure you update paths in commands).
2.  Edit `server_config.json` to define the existing applications you want to manage as services. It's a JSON array of objects, where each object represents an application to be managed.

    **Fields for each application object:**
    *   `FriendlyName` (string): A human-readable name for the application (e.g., "My Awesome App"). Used in logs and the UI.
    *   `AppPath` (string): The **full and absolute path** to your **pre-existing** `.bat` or `.exe` application file (e.g., `C:\MyExistingApps\start_my_app.bat` or `D:\MyLegacyApp\run.exe`). **This is crucial and must point to an application file already on your disk.** Use double backslashes in JSON (e.g., `C:\\Path\\To\\Your\\ExistingApp.exe`).
    *   `AppArguments` (string, optional): Any command-line arguments to pass to your application. If none, use an empty string `""`.
    *   `LogDirectory` (string): The **full and absolute path** to the directory where this managed application's console output log files will be stored (e.g., `C:\AppLauncherLogs\MyAwesomeAppLogs`). The launcher scripts will create this directory if it doesn't exist. Use double backslashes in JSON.
    *   `ServiceName` (string): A unique name for the Windows service that will wrap your application (e.g., `MyAwesomeAppSvc`). Must not contain spaces or special characters. Keep it short and descriptive.

    **Example `server_config.json` snippet:**
    ```json
    [
      {
        "FriendlyName": "Hub Server Application",
        "AppPath": "C:\\MyCompany\\Apps\\HubServer\\hubServer.bat",
        "AppArguments": "/config:hub.json",
        "LogDirectory": "C:\\AppLauncherLogs\\HubServer",
        "ServiceName": "HubServerSvc"
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
The main management scripts (`Install-ServerParts.ps1`, `Start-StatusWebServer.ps1`) require paths to their dependencies (other PowerShell scripts or HTML files within this management system).
*   If you maintain the documented folder structure (e.g., all PowerShell scripts in a `scripts` subfolder, `status_dashboard.html` in `web_frontend`), the example commands provided below should work with relative paths from the root `WindowsAppLauncher` directory.
*   If you rearrange the file structure of this management system, you **must** provide the correct full or relative paths for parameters like `-LauncherScriptDirectory`, `-ServiceScriptPath`, `-GetStatusScriptPath`, `-HtmlFilePath` when calling these scripts.

## 6. Registering Applications as Services

To take your existing applications (defined in `server_config.json`) and register them as Windows services for management:

1.  Open PowerShell as **Administrator**.
2.  Navigate to the root directory where you copied the management system files (e.g., `cd C:\Tools\WindowsAppLauncher`).
3.  Run the service registration script:

    ```powershell
    .\scripts\Install-ServerParts.ps1 -ConfigFilePath ".\server_config.json" -LauncherScriptDirectory ".\scripts" -ServiceScriptPath ".\scripts\New-AppWindowsService.ps1"
    ```

    This command **does not install your application software**. Instead, `Install-ServerParts.ps1` reads your `server_config.json` and, for each entry, it:
    *   Uses `New-AppWindowsService.ps1` to create a new Windows Service.
    *   This service is configured to launch your specified existing application (using `launch_bat.ps1` or `launch_exe.ps1` as helpers).
    *   This registration enables your application to be managed by the Windows Service Control Manager (for auto-restarts, etc.) and by the other scripts in this suite.

## 7. Usage

All commands should be run from a PowerShell prompt in the root directory of the management system (e.g., `C:\Tools\WindowsAppLauncher`). Administrative privileges are required for most operations.

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

### Web Dashboard for Managed Applications
1.  **Start the Web Server:**
    (May require Admin privileges depending on the port and network configuration)
    ```powershell
    .\web_frontend\Start-StatusWebServer.ps1 -ConfigFilePath ".\server_config.json" -GetStatusScriptPath ".\scripts\Get-ServerPartStatus.ps1" -HtmlFilePath ".\web_frontend\status_dashboard.html"
    ```
    This command tells `Start-StatusWebServer.ps1`:
    *   Where your main server configuration is (`server_config.json`).
    *   Where the `Get-ServerPartStatus.ps1` script is (to fetch data for the `/status` API).
    *   Where the `status_dashboard.html` file is.

2.  **Access the Dashboard:**
    Open a web browser and navigate to `http://localhost:8088` (or the port you configured if you used the `-Port` parameter).

### Uninstalling (Unregistering) Services
(Requires Admin privileges)
This will stop and remove the Windows Service wrappers for all applications defined in the configuration file. It **does not** uninstall your actual application software.
```powershell
.\scripts\Uninstall-ServerParts.ps1 -ConfigFilePath ".\server_config.json"
```

## 8. Logging

*   **Application Logs:** The stdout and stderr output of each launched application (that you've configured to be managed) are redirected to `.log` files. These are stored in the directory specified by the `LogDirectory` field in `server_config.json` for that application, with a timestamp in the filename (e.g., `MyApplication_2023-10-27_14-30-00.log`).
*   **Service Events:** Standard Windows Service events (start, stop, failure, recovery actions for the service wrappers) are logged to the Windows Event Log (typically under `System` or `Application`). Use `Event Viewer` (eventvwr.msc) to view these.
*   **Management Script Output:** The PowerShell management scripts write their output to the console. This can be redirected to a file if needed (e.g., `.\scripts\Install-ServerParts.ps1 ... > registration.log`).

## 9. Troubleshooting

*   **Paths:** Double-check that all paths in `server_config.json` (especially `AppPath` for your existing application and `LogDirectory`) are **full, absolute, and correct**. Remember to use double backslashes (`\\`) for paths in JSON. `AppPath` must point to an executable or batch file that is already on your system.
*   **Application Logs:** Examine the log files in the configured `LogDirectory` for your specific application. These logs contain the direct output from your `.bat` or `.exe` and will show any errors it reported when launched by the service.
*   **Services MMC:** Open the Services console (`services.msc`) to check the status of your registered service wrappers, their configuration (Log On As, Startup Type, Recovery settings), and dependencies.
*   **Windows Event Viewer:** Look in `Windows Logs > System` and `Windows Logs > Application` in Event Viewer for errors related to your service names.
*   **Administrator Privileges:** Ensure you are running scripts that register or modify services from a PowerShell prompt that was "Run as Administrator".
*   **Script Parameters:** If you've changed the folder structure of this management system, ensure you are providing the correct paths to dependent scripts/files when calling `Install-ServerParts.ps1` or `Start-StatusWebServer.ps1`.
*   **Web Dashboard Issues:** If the web dashboard doesn't load or show data:
    *   Ensure `Start-StatusWebServer.ps1` is running and didn't report errors on startup.
    *   Check the browser's developer console (usually F12) for JavaScript errors or network errors when trying to fetch `/status`.
    *   Verify `Get-ServerPartStatus.ps1` runs correctly on its own and produces valid JSON.

```
