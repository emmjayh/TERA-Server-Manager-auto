<#
.SYNOPSIS
Creates and configures a Windows Service to monitor and run a given application.

.DESCRIPTION
This script creates a new Windows Service that will launch a specified .bat or .exe file
using provided launcher scripts. It configures the service for automatic startup and
sets up recovery options to restart the service on failure.

.PARAMETER ServiceName
The name for the Windows Service (e.g., "HubServerSvc"). Mandatory. No spaces.

.PARAMETER DisplayName
The display name for the service (e.g., "Hub Server Application"). Mandatory.

.PARAMETER Description
An optional description for the service.

.PARAMETER AppPath
The full path to the .bat or .exe file to be launched. Mandatory.

.PARAMETER AppArguments
Optional arguments to pass to the application/script.

.PARAMETER LogDirectory
The directory path for logs (passed to the launcher script). Mandatory.

.PARAMETER LauncherBatPath
Full path to launch_bat.ps1. Mandatory.

.PARAMETER LauncherExePath
Full path to launch_exe.ps1. Mandatory.

.EXAMPLE
.\New-AppWindowsService.ps1 -ServiceName "MyBatSvc" -DisplayName "My Batch Service" -AppPath "C:\apps\my_task.bat" -LogDirectory "C:\app_launcher_logs" -LauncherBatPath "C:\launch_scripts\launch_bat.ps1" -LauncherExePath "C:\launch_scripts\launch_exe.ps1" -AppArguments "/debug"

.EXAMPLE
.\New-AppWindowsService.ps1 -ServiceName "MyExeSvc" -DisplayName "My Exe Service" -AppPath "C:\apps\my_program.exe" -LogDirectory "C:\app_launcher_logs" -LauncherBatPath "C:\launch_scripts\launch_bat.ps1" -LauncherExePath "C:\launch_scripts\launch_exe.ps1"

.NOTES
Requires administrative privileges to create and configure services.
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param (
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ServiceName,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$DisplayName,

    [string]$Description,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$AppPath,

    [string]$AppArguments,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$LogDirectory,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$LauncherBatPath,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$LauncherExePath
)

try {
    # 1. Parameter Validation
    # Check if service already exists
    if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
        Write-Error "Service '$ServiceName' already exists."
        exit 1
    }

    # Validate AppPath
    if (-not (Test-Path -Path $AppPath -PathType Leaf)) {
        Write-Error "Application file not found: $AppPath"
        exit 1
    }

    # Validate LauncherBatPath
    if (-not (Test-Path -Path $LauncherBatPath -PathType Leaf)) {
        Write-Error "Launcher script not found: $LauncherBatPath"
        exit 1
    }

    # Validate LauncherExePath
    if (-not (Test-Path -Path $LauncherExePath -PathType Leaf)) {
        Write-Error "Launcher script not found: $LauncherExePath"
        exit 1
    }

    # Validate LogDirectory (basic validation, launcher scripts handle creation)
    if ([string]::IsNullOrWhiteSpace($LogDirectory)) {
        Write-Error "LogDirectory cannot be empty."
        exit 1
    }
    # Attempt to resolve path to catch obviously invalid paths early
    try {
        $resolvedLogDir = Resolve-Path -Path $LogDirectory -ErrorAction Stop
        $LogDirectory = $resolvedLogDir.Path # Use resolved path
    } catch {
        # If path doesn't exist, it's fine, launcher will create. But if Resolve-Path fails for other reasons (invalid chars etc.)
        if ($_.Exception -isnot [System.Management.Automation.ItemNotFoundException]) {
            Write-Error "Invalid LogDirectory path: $LogDirectory. Error: $($_.Exception.Message)"
            exit 1
        }
        # For ItemNotFoundException, we proceed, as the launcher scripts are designed to create it.
        # However, it's good to ensure the parent of the intended LogDirectory exists if it's a multi-level path.
        # This is a simple check, more robust logic might be needed for complex scenarios.
        $parentLogDir = Split-Path -Path $LogDirectory
        if ($parentLogDir -and (-not (Test-Path -Path $parentLogDir -PathType Container))) {
             Write-Warning "Parent of LogDirectory '$parentLogDir' does not exist. Ensure the path is creatable by the launcher scripts."
        }
    }


    # 2. Determine Launcher
    $appExtension = [System.IO.Path]::GetExtension($AppPath).ToLower()
    $selectedLauncherPath = ""

    if ($appExtension -eq ".bat") {
        $selectedLauncherPath = $LauncherBatPath
    }
    elseif ($appExtension -eq ".exe") {
        $selectedLauncherPath = $LauncherExePath
    }
    else {
        Write-Error "Unsupported application type: $appExtension. Only .bat and .exe are supported."
        exit 1
    }

    # 3. Construct Service Command
    # Ensure paths are double-quoted within the command string for BinaryPathName
    $binaryPathName = "powershell.exe -ExecutionPolicy Bypass -NoProfile -File ""$selectedLauncherPath"" -TargetFilePath ""$AppPath"" -LogDirectory ""$LogDirectory"""
    if (-not [string]::IsNullOrWhiteSpace($AppArguments)) {
        # Ensure AppArguments are also quoted if they might contain spaces.
        # The launcher scripts should be robust enough to handle arguments passed this way.
        $binaryPathName += " -LaunchArguments ""$($AppArguments.Replace('"', '\""))"""
    }

    # 4. Create Windows Service
    $serviceParams = @{
        Name           = $ServiceName
        DisplayName    = $DisplayName
        BinaryPathName = $binaryPathName
        StartupType    = 'Automatic'
        ErrorAction    = 'Stop' # Stop script on error for New-Service
    }
    if (-not [string]::IsNullOrWhiteSpace($Description)) {
        $serviceParams.Description = $Description
    }

    if ($PSCmdlet.ShouldProcess($ServiceName, "Create Service")) {
        Write-Verbose "Creating service '$ServiceName' with command: $binaryPathName"
        $null = New-Service @serviceParams
        Write-Host "Service '$ServiceName' created successfully."

        # 5. Configure Service Recovery Options
        # sc.exe failure <ServiceName> reset= <reset period in seconds> actions= <action>/<delay in ms>/<action>/<delay in ms>/...
        $resetPeriodSeconds = 86400 # 1 day
        $restartDelayMs = 60000   # 1 minute
        $failureActions = "restart/$restartDelayMs/restart/$restartDelayMs/restart/$restartDelayMs"
        
        $scCommand = "sc.exe failure ""$ServiceName"" reset= $resetPeriodSeconds actions= $failureActions"
        Write-Verbose "Configuring recovery options for '$ServiceName': $scCommand"
        
        Invoke-Expression $scCommand
        $scExitCode = $LASTEXITCODE
        if ($scExitCode -ne 0) {
            Write-Warning "Failed to configure service recovery options for '$ServiceName'. SC.exe exit code: $scExitCode. Manual configuration may be required."
        } else {
            Write-Verbose "Service recovery options configured successfully for '$ServiceName'."
        }
    }
}
catch {
    Write-Error "An error occurred: $($_.Exception.Message)"
    # Attempt to clean up if service was partially created (optional, might be risky)
    # if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
    #     Write-Warning "Attempting to remove partially created service '$ServiceName' due to error."
    #     try { Remove-Service -Name $ServiceName -Force -ErrorAction Stop } catch { Write-Warning "Failed to remove service '$ServiceName'."}
    # }
    exit 1
}

# Note: This script does not start the service. It can be started manually or via `Start-Service $ServiceName`.
Write-Host "To start the service, run: Start-Service -Name ""$ServiceName"""
exit 0
