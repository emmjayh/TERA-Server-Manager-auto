<#
.SYNOPSIS
Stops and removes multiple Windows Services based on a JSON configuration file.

.DESCRIPTION
This script reads server part configurations from a specified JSON file,
stops the corresponding Windows Service if it is running, and then removes it.
Requires administrative privileges.

.PARAMETER ConfigFilePath
Path to the JSON configuration file (e.g., ".\server_config.json"). Mandatory.
The JSON file should contain an array of objects, each with a "ServiceName" property.

.PARAMETER Force
Optional switch. Currently not implemented for interactive confirmation, but included for future use.
It implies non-interactive operation where applicable.

.EXAMPLE
.\Uninstall-ServerParts.ps1 -ConfigFilePath ".\server_config.json"
.\Uninstall-ServerParts.ps1 -ConfigFilePath ".\server_config.json" -Force

.NOTES
Requires administrative privileges to stop and remove services.
Assumes services listed in the JSON file have already been created.
Be cautious when using this script, as it removes services.
#>
[CmdletBinding(SupportsShouldProcess = $true)] # SupportsShouldProcess adds -WhatIf, -Confirm
param (
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ConfigFilePath,

    [Parameter(Mandatory = $false)]
    [switch]$Force # For -Confirm behavior with ShouldProcess
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
    $ResolvedConfigFilePath = Resolve-Path -Path $ConfigFilePath -ErrorAction Stop
}
catch {
    Write-Error "Error resolving configuration file path: $($_.Exception.Message)"
    exit 1
}

# 2. Read Configuration
$serverConfigs = $null
try {
    $jsonContent = Get-Content -Path $ResolvedConfigFilePath -Raw -ErrorAction Stop
    $serverConfigs = ConvertFrom-Json -InputObject $jsonContent -ErrorAction Stop
}
catch {
    Write-Error "Failed to read or parse configuration file '$ResolvedConfigFilePath': $($_.Exception.Message)"
    exit 1
}

if ($null -eq $serverConfigs) {
    Write-Warning "No configurations found or configuration file is empty: $ResolvedConfigFilePath"
    exit 0 # Exit cleanly, no data to process
}
# Ensure it's an array, even if JSON has single object
if ($serverConfigs -isnot [array]) {
    $serverConfigs = @($serverConfigs)
}

# 3. Iterate, Stop, and Remove Services
$totalEntries = $serverConfigs.Count
$servicesRemoved = 0
$servicesNotFound = 0
$servicesFailedStop = 0
$servicesFailedRemove = 0

Write-Host "Starting service uninstallation. Processing $totalEntries entries from '$ResolvedConfigFilePath'."
Write-Host "--------------------------------------------------"

# Consider processing in reverse if dependencies matter, but for now, as-is.
# $serverConfigs = $serverConfigs | Sort-Object -Property SomeDependencyProperty -Descending

foreach ($entry in $serverConfigs) {
    if (-not $entry.PSObject.Properties['ServiceName'] -or [string]::IsNullOrWhiteSpace($entry.ServiceName)) {
        Write-Warning "Skipping entry due to missing or empty 'ServiceName'. Entry details: $($entry | Out-String)"
        continue
    }
    $serviceName = $entry.ServiceName

    Write-Host "Processing Service: '$serviceName'"
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

    if ($service) {
        $wasStopped = $false
        # Stop the Service if it's running
        if ($service.Status -ne 'Stopped') {
            Write-Verbose "Service '$serviceName' is in state '$($service.Status)'. Attempting to stop."
            if ($PSCmdlet.ShouldProcess($serviceName, "Stop Service")) {
                try {
                    Stop-Service -Name $serviceName -Force -ErrorAction Stop

                    # Wait for the service to actually stop
                    $timeoutSeconds = 30
                    $stopWatch = [System.Diagnostics.Stopwatch]::StartNew()
                    while ($service.Status -ne 'Stopped' -and $stopWatch.Elapsed.TotalSeconds -lt $timeoutSeconds) {
                        Start-Sleep -Milliseconds 500
                        $service = Get-Service -Name $serviceName # Refresh service object
                    }
                    $stopWatch.Stop()

                    if ($service.Status -eq 'Stopped') {
                        Write-Host "Service '$serviceName' stopped successfully."
                        $wasStopped = $true
                    } else {
                        Write-Warning "Service '$serviceName' did not stop within $timeoutSeconds seconds. Current status: '$($service.Status)'. Removal will be attempted anyway."
                        $servicesFailedStop++
                    }
                }
                catch {
                    Write-Error "ERROR: Could not stop service '$serviceName': $($_.Exception.Message)"
                    $servicesFailedStop++
                    # Continue to attempt removal even if stop fails, as service might be in a problematic state
                }
            } else {
                Write-Host "Skipped stopping service '$serviceName' due to -WhatIf/-Confirm preference. Cannot proceed with removal for this service."
                continue # Skip to next service if user chose not to stop
            }
        } else {
            Write-Host "Service '$serviceName' is already stopped."
            $wasStopped = $true # Considered stopped for removal purposes
        }

        # Remove the Service
        # We attempt removal if it was stopped in this run, was already stopped, or if stop failed (it might be stuck)
        if ($wasStopped -or $servicesFailedStop -gt 0) { # Condition for attempting removal
            Write-Verbose "Attempting to remove service '$serviceName'."
            if ($PSCmdlet.ShouldProcess($serviceName, "Remove Service")) {
                try {
                    # Using sc.exe delete for directness
                    $deleteProcess = Start-Process "sc.exe" -ArgumentList "delete ""$serviceName""" -Wait -NoNewWindow -PassThru
                    if ($deleteProcess.ExitCode -eq 0) {
                        Write-Host "Service '$serviceName' removed successfully."
                        $servicesRemoved++
                    } else {
                        # Attempt to get error message from sc.exe if possible (can be tricky)
                        Write-Error "ERROR: sc.exe failed to remove service '$serviceName'. Exit code: $($deleteProcess.ExitCode)."
                        $servicesFailedRemove++
                    }
                }
                catch { # Catch errors from Start-Process itself
                    Write-Error "ERROR: Exception while trying to remove service '$serviceName' using sc.exe: $($_.Exception.Message)"
                    $servicesFailedRemove++
                }
            } else {
                 Write-Host "Skipped removing service '$serviceName' due to -WhatIf/-Confirm preference."
            }
        }
    }
    else {
        Write-Host "Service '$serviceName' not found, nothing to uninstall."
        $servicesNotFound++
    }
    Write-Host "--------------------------------------------------"
}

# 4. Summary
Write-Host "=================================================="
Write-Host "Service Uninstallation Summary:"
Write-Host "Total entries processed: $totalEntries"
Write-Host "Services removed successfully: $servicesRemoved"
Write-Host "Services not found (already uninstalled or never installed): $servicesNotFound"
Write-Host "Services that failed to stop (removal might have been attempted): $servicesFailedStop"
Write-Host "Services that failed to be removed (after stop attempt): $servicesFailedRemove"
Write-Host "=================================================="

if ($servicesFailedStop -gt 0 -or $servicesFailedRemove -gt 0) {
    Write-Warning "Some services could not be stopped or removed properly. Please review the logs above."
    # exit 1 # Indicate partial failure
}

exit 0
