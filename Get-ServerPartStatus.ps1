<#
.SYNOPSIS
Retrieves the status of multiple Windows Services based on a JSON configuration file.

.DESCRIPTION
This script reads server part configurations from a specified JSON file,
retrieves the status (and PID if running) of each corresponding Windows Service,
and outputs this information as PowerShell objects or a JSON string.

.PARAMETER ConfigFilePath
Path to the JSON configuration file (e.g., ".\server_config.json"). Mandatory.
The JSON file should contain an array of objects, each with at least "ServiceName"
and "FriendlyName" properties.

.PARAMETER OutputToJson
If present, the script's output will be a single JSON string representing an array
of service statuses. Otherwise, it outputs PowerShell custom objects.

.EXAMPLE
.\Get-ServerPartStatus.ps1 -ConfigFilePath ".\server_config.json"

.EXAMPLE
.\Get-ServerPartStatus.ps1 -ConfigFilePath ".\server_config.json" -OutputToJson

.EXAMPLE
.\Get-ServerPartStatus.ps1 -ConfigFilePath ".\server_config.json" -OutputToJson | Out-File ".\status.json"

.OUTPUTS
System.Management.Automation.PSCustomObject[] or System.String (JSON)
An array of objects containing service status information, or a JSON string representation.
#>
[CmdletBinding()]
param (
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ConfigFilePath,

    [Parameter(Mandatory = $false)]
    [switch]$OutputToJson
)

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

# 3. Iterate and Get Service Status
$statuses = @()

foreach ($entry in $serverConfigs) {
    # Validate essential properties in the entry
    if (-not $entry.PSObject.Properties['ServiceName'] -or [string]::IsNullOrWhiteSpace($entry.ServiceName)) {
        Write-Warning "Skipping entry due to missing or empty 'ServiceName'. Entry details: $($entry | Out-String)"
        continue
    }
    $serviceName = $entry.ServiceName
    $friendlyName = if ($entry.PSObject.Properties['FriendlyName'] -and -not [string]::IsNullOrWhiteSpace($entry.FriendlyName)) { $entry.FriendlyName } else { $serviceName }

    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    $pid = $null # Default PID

    if ($service) {
        $status = $service.Status.ToString()
        if ($status -eq 'Running') {
            try {
                # Get-CimInstance is generally preferred over Get-WmiObject
                $cimService = Get-CimInstance Win32_Service -Filter "Name='$serviceName'" -ErrorAction SilentlyContinue
                if ($cimService -and $cimService.ProcessId -ne 0) {
                    $pid = [int]$cimService.ProcessId
                } else {
                    $pid = 0 # Explicitly set to 0 if running but PID is 0 (e.g. shared process or no direct host)
                }
            }
            catch {
                Write-Warning "Could not retrieve PID for running service '$serviceName': $($_.Exception.Message)"
                $pid = 0 # Indicate running but PID fetch failed or not applicable
            }
        } else {
             $pid = 0 # Not running, so PID is 0
        }
        
        $statusObject = [PSCustomObject]@{
            FriendlyName = $friendlyName
            ServiceName  = $serviceName
            Status       = $status
            PID          = $pid
        }
    }
    else {
        $statusObject = [PSCustomObject]@{
            FriendlyName = $friendlyName
            ServiceName  = $serviceName
            Status       = "Not Found"
            PID          = $null # Using $null for PID when service not found
        }
    }
    $statuses += $statusObject
}

# 4. Output
if ($OutputToJson.IsPresent) {
    Write-Output ($statuses | ConvertTo-Json -Depth 3)
}
else {
    Write-Output $statuses
}

exit 0
