<#
.SYNOPSIS
Starts multiple Windows Services based on a JSON configuration file.

.DESCRIPTION
This script reads server part configurations from a specified JSON file and
starts the corresponding Windows Service for each entry if it is not already running.
It requires administrative privileges to run.

.PARAMETER ConfigFilePath
Path to the JSON configuration file (e.g., ".\server_config.json"). Mandatory.
The JSON file should contain an array of objects, each with a "ServiceName" property.

.EXAMPLE
.\Start-AllServerParts.ps1 -ConfigFilePath ".\server_config.json"

.NOTES
Requires administrative privileges to start services.
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

# 3. Iterate and Start Services
$totalEntries = $serverConfigs.Count
$servicesStarted = 0
$servicesAlreadyRunning = 0
$servicesNotFound = 0
$servicesFailedToStart = 0

Write-Host "Starting service management. Processing $totalEntries entries from '$ConfigFilePath'."
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
        if ($service.Status -eq 'Stopped') {
            Write-Verbose "Service '$serviceName' is stopped. Attempting to start."
            if ($PSCmdlet.ShouldProcess($serviceName, "Start Service")) {
                try {
                    Start-Service -Name $serviceName -ErrorAction Stop
                    # Verify it started
                    $updatedService = Get-Service -Name $serviceName
                    if ($updatedService.Status -eq 'Running') {
                        Write-Host "Service '$serviceName' started successfully."
                        $servicesStarted++
                    } else {
                        Write-Warning "Service '$serviceName' status is '$($updatedService.Status)' after start attempt."
                        $servicesFailedToStart++
                    }
                }
                catch {
                    Write-Error "ERROR: Could not start service '$serviceName': $($_.Exception.Message)"
                    $servicesFailedToStart++
                }
            } else {
                 Write-Host "Skipped starting service '$serviceName' due to -WhatIf preference."
            }
        }
        elseif ($service.Status -eq 'Running') {
            Write-Host "Service '$serviceName' is already running."
            $servicesAlreadyRunning++
        }
        else {
            Write-Host "Service '$serviceName' is in state '$($service.Status)' (not 'Stopped' or 'Running'). No action taken."
        }
    }
    else {
        Write-Warning "Service '$serviceName' not found. It may need to be installed."
        $servicesNotFound++
    }
    Write-Host "--------------------------------------------------"
}

# 4. Summary
Write-Host "=================================================="
Write-Host "Service Start Summary:"
Write-Host "Total entries processed: $totalEntries"
Write-Host "Services started successfully in this run: $servicesStarted"
Write-Host "Services already running: $servicesAlreadyRunning"
Write-Host "Services not found: $servicesNotFound"
Write-Host "Services that failed to start: $servicesFailedToStart"
Write-Host "=================================================="

if ($servicesFailedToStart -gt 0 -or $servicesNotFound -gt 0) {
    Write-Warning "Some services could not be started or were not found. Please review the logs above."
    # Optionally, exit with an error code to indicate issues
    # exit 1
}

exit 0
