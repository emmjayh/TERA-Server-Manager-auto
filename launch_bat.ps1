<#
.SYNOPSIS
Launches a batch file with logging and returns the PID of the cmd.exe process.

.DESCRIPTION
This script launches a specified .bat file, redirects its stdout and stderr to a log file,
and attempts to return the Process ID (PID) of the cmd.exe process that runs the batch file.

.PARAMETER TargetFilePath
The full path to the .bat file to be executed. This parameter is mandatory.

.PARAMETER LogDirectory
The directory where log files will be stored. This parameter is mandatory.
The directory will be created if it does not exist.

.PARAMETER LaunchArguments
Optional arguments to pass to the batch file.

.EXAMPLE
.\launch_bat.ps1 -TargetFilePath "C:\MyScripts\MyBatch.bat" -LogDirectory "C:\AppLogs" -LaunchArguments "/param1 value1"

.OUTPUTS
System.String
The PID of the launched cmd.exe process as a string, or an error message if the launch fails.
#>
[CmdletBinding()]
param (
    [Parameter(Mandatory = $true)]
    [string]$TargetFilePath,

    [Parameter(Mandatory = $true)]
    [string]$LogDirectory,

    [string]$LaunchArguments
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

# Prepare the command to execute
$command = "cmd.exe"
$arguments = "/c ""$TargetFilePath"" $LaunchArguments" # Ensure TargetFilePath is quoted

# Launch the batch file
try {
    # Start-Process is used to launch in a new window and get the process ID.
    # We redirect output within the cmd.exe call itself to capture the batch file's output.
    # Note: Getting the PID of cmd.exe that *reliably* stays around for the whole batch duration is tricky.
    # cmd.exe might exit, but child processes of the batch file might continue.
    # This will get the PID of the initial cmd.exe process.

    $process = Start-Process -FilePath $command -ArgumentList "$arguments *>&1> `"$logFilePath`"" -PassThru -WindowStyle Normal -ErrorAction Stop

    if ($process -and $process.Id) {
        Write-Output $process.Id.ToString()
    } else {
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
