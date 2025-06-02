<#
.SYNOPSIS
Stops multiple Windows Services based on a JSON configuration file.

.DESCRIPTION
This script reads server part configurations from a specified JSON file and
stops the corresponding Windows Service for each entry if it is currently running or pending.
It requires administrative privileges to run.

.PARAMETER ConfigFilePath
Path to the JSON configuration file (e.g., ".\server_config.json"). Mandatory.
The JSON file should contain an array of objects, each with a "ServiceName" property.

.EXAMPLE
.\Stop-AllServerParts.ps1 -ConfigFilePath ".\server_config.json"

.NOTES
Requires administrative privileges to stop services.
Assumes services listed in the JSON file have already been created.
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param (
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ConfigFilePath
)

# 0. Administrative Privileges Check
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Administrator privileges are required to run this script. Please re-run as Administrator."
    exit 1
}

# 1. Parameter Validation
if (-not (Test-Path -Path $ConfigFilePath -PathType Leaf)) {
    Write-Error "Configuration file not found: $ConfigFilePath"
    exit 1
}

try {
    $ConfigFilePath = Resolve-Path -Path $ConfigFilePath -ErrorAction Stop
}
catch {
    Write-Error "Error resolving configuration file path: $($_.Exception.Message)"
    exit 1
}

# 2. Read Configuration
$serverConfigs = $null
try {
    $jsonContent = Get-Content -Path $ConfigFilePath -Raw -ErrorAction Stop
    $serverConfigs = ConvertFrom-Json -InputObject $jsonContent -ErrorAction Stop
}
catch {
    Write-Error "Failed to read or parse configuration file '$ConfigFilePath': $($_.Exception.Message)"
    exit 1
}

if ($null -eq $serverConfigs) {
    Write-Error "No configurations found or configuration file is empty: $ConfigFilePath"
    exit 1
}
# Ensure it's an array, even if JSON has single object
if ($serverConfigs -isnot [array]) {
    $serverConfigs = @($serverConfigs)
}

# 3. Iterate and Stop Services
$totalEntries = $serverConfigs.Count
$servicesStoppedSuccessfully = 0
$servicesAlreadyStopped = 0
$servicesNotFound = 0
$servicesFailedToStop = 0

Write-Host "Starting service stop process. Processing $totalEntries entries from '$ConfigFilePath'."
Write-Host "--------------------------------------------------"

foreach ($entry in $serverConfigs) {
    if (-not $entry.PSObject.Properties['ServiceName'] -or [string]::IsNullOrWhiteSpace($entry.ServiceName)) {
        Write-Warning "Skipping entry due to missing or empty 'ServiceName'. Entry details: $($entry | Out-String)"
        continue # Skip to next entry
    }
    $serviceName = $entry.ServiceName

    Write-Host "Processing Service: '$serviceName'"
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

    if ($service) {
        $stoppableStates = @('Running', 'Paused', 'StartPending', 'StopPending', 'ContinuePending', 'PausePending')
        if ($service.Status -in $stoppableStates) {
            Write-Verbose "Service '$serviceName' is in state '$($service.Status)'. Attempting to stop."
            if ($PSCmdlet.ShouldProcess($serviceName, "Stop Service")) {
                try {
                    # Stop-Service can sometimes hang, especially if a service is misbehaving.
                    # Adding a reasonable timeout.
                    Stop-Service -Name $serviceName -Force -ErrorAction Stop # -Force to stop services with dependent services
                    
                    # Wait for service to actually stop.
                    # Start-Sleep -Seconds 2 # Give it a moment
                    $service.WaitForStatus('Stopped', [TimeSpan]::FromSeconds(30)) # Wait up to 30 seconds

                    $updatedService = Get-Service -Name $serviceName
                    if ($updatedService.Status -eq 'Stopped') {
                        Write-Host "Service '$serviceName' stopped successfully."
                        $servicesStoppedSuccessfully++
                    } else {
                        Write-Warning "Service '$serviceName' status is '$($updatedService.Status)' after stop attempt. It may still be stopping or failed to stop."
                        $servicesFailedToStop++
                    }
                }
                catch [System.ServiceProcess.TimeoutException] {
                    Write-Error "ERROR: Timeout waiting for service '$serviceName' to stop. $($_.Exception.Message)"
                    $servicesFailedToStop++
                }
                catch {
                    Write-Error "ERROR: Could not stop service '$serviceName': $($_.Exception.Message)"
                    $servicesFailedToStop++
                }
            } else {
                 Write-Host "Skipped stopping service '$serviceName' due to -WhatIf preference."
            }
        }
        elseif ($service.Status -eq 'Stopped') {
            Write-Host "Service '$serviceName' is already stopped."
            $servicesAlreadyStopped++
        }
        else {
            Write-Host "Service '$serviceName' is in state '$($service.Status)' (e.g. 'Stopping'). No direct action taken, but previous attempt might be in progress."
        }
    }
    else {
        Write-Warning "Service '$serviceName' not found."
        $servicesNotFound++
    }
    Write-Host "--------------------------------------------------"
}

# 4. Summary
Write-Host "=================================================="
Write-Host "Service Stop Summary:"
Write-Host "Total entries processed: $totalEntries"
Write-Host "Services stopped successfully in this run: $servicesStoppedSuccessfully"
Write-Host "Services already stopped: $servicesAlreadyStopped"
Write-Host "Services not found: $servicesNotFound"
Write-Host "Services that failed to stop or timed out: $servicesFailedToStop"
Write-Host "=================================================="

if ($servicesFailedToStop -gt 0 -or $servicesNotFound -gt 0) {
    Write-Warning "Some services could not be stopped or were not found. Please review the logs above."
    # Optionally, exit with an error code to indicate issues
    # exit 1 
}

exit 0
