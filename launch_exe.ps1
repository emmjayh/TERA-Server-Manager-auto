<#
.SYNOPSIS
Launches an executable file with logging and returns its PID.

.DESCRIPTION
This script launches a specified .exe file, redirects its stdout and stderr to a log file,
sets its working directory, and returns the Process ID (PID) of the launched executable.

.PARAMETER TargetFilePath
The full path to the .exe file to be executed. This parameter is mandatory.

.PARAMETER LogDirectory
The directory where log files will be stored. This parameter is mandatory.
The directory will be created if it does not exist.

.PARAMETER LaunchArguments
Optional arguments to pass to the executable.

.PARAMETER WorkingDirectory
Optional working directory for the executable. If not provided,
the directory of the executable will be used.

.EXAMPLE
.\launch_exe.ps1 -TargetFilePath "C:\MyProgram\app.exe" -LogDirectory "C:\AppLogs" -LaunchArguments "-config C:\config.xml" -WorkingDirectory "C:\MyProgram"

.OUTPUTS
System.String
The PID of the launched executable as a string, or an error message if the launch fails.
#>
[CmdletBinding()]
param (
    [Parameter(Mandatory = $true)]
    [string]$TargetFilePath,

    [Parameter(Mandatory = $true)]
    [string]$LogDirectory,

    [string]$LaunchArguments,

    [string]$WorkingDirectory
)

# Check if the target file path exists
if (-not (Test-Path -Path $TargetFilePath -PathType Leaf)) {
    Write-Error "ERROR: Target file not found: $TargetFilePath"
    exit 1
}

# Create the log directory if it doesn't exist
if (-not (Test-Path -Path $LogDirectory -PathType Container)) {
    try {
        New-Item -ItemType Directory -Path $LogDirectory -Force -ErrorAction Stop | Out-Null
    }
    catch {
        Write-Error "ERROR: Could not create log directory: $LogDirectory. $_"
        exit 1
    }
}

# Construct the log file name
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$baseName = [System.IO.Path]::GetFileNameWithoutExtension($TargetFilePath)
$logFileName = "${baseName}_${timestamp}.log"
$logFilePath = Join-Path -Path $LogDirectory -ChildPath $logFileName

# Determine the working directory
if ([string]::IsNullOrWhiteSpace($WorkingDirectory)) {
    $WorkingDirectory = Split-Path -Path $TargetFilePath -Parent
}

# Launch the executable
try {
    $process = Start-Process -FilePath $TargetFilePath -ArgumentList $LaunchArguments -WorkingDirectory $WorkingDirectory -PassThru -RedirectStandardOutput $logFilePath -RedirectStandardError $logFilePath -WindowStyle Normal -ErrorAction Stop

    if ($process -and $process.Id) {
        Write-Output $process.Id.ToString()
    } else {
        # This case should ideally not be hit if Start-Process succeeds and -PassThru is used,
        # but included for robustness.
        Write-Output "ERROR: Launch succeeded but PID could not be determined."
    }
}
catch {
    Write-Output "ERROR: Launch failed. $($_.Exception.Message)"
    # Attempt to write error to log file as well, if possible
    if ($logFilePath) {
        try {
            "ERROR: Launch failed. $($_.Exception.Message)" | Out-File -FilePath $logFilePath -Append -Encoding UTF8 -ErrorAction SilentlyContinue
        } catch {}
    }
    exit 1 # Exit with an error code if Start-Process failed
}

exit 0
