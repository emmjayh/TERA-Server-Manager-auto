<#
.SYNOPSIS
Installs multiple Windows Services based on a JSON configuration file.

.DESCRIPTION
This script reads server part configurations from a specified JSON file and uses
New-AppWindowsService.ps1 to create and configure a Windows Service for each entry.
It requires administrative privileges to run.

.PARAMETER ConfigFilePath
Path to the JSON configuration file (e.g., ".\server_config.json"). Mandatory.

.PARAMETER LauncherScriptDirectory
Path to the directory containing launch_bat.ps1 and launch_exe.ps1. Mandatory.

.PARAMETER ServiceScriptPath
Path to New-AppWindowsService.ps1. Mandatory.

.EXAMPLE
.\Install-ServerParts.ps1 -ConfigFilePath ".\server_config.json" -LauncherScriptDirectory ".\launch_scripts" -ServiceScriptPath ".\New-AppWindowsService.ps1"

.NOTES
Requires administrative privileges.
Assumes New-AppWindowsService.ps1, launch_bat.ps1, and launch_exe.ps1 are available and correctly implemented.
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param (
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ConfigFilePath,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$LauncherScriptDirectory,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ServiceScriptPath
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

if (-not (Test-Path -Path $LauncherScriptDirectory -PathType Container)) {
    Write-Error "Launcher script directory not found: $LauncherScriptDirectory"
    exit 1
}

$launcherBat = Join-Path -Path $LauncherScriptDirectory -ChildPath "launch_bat.ps1"
$launcherExe = Join-Path -Path $LauncherScriptDirectory -ChildPath "launch_exe.ps1"

if (-not (Test-Path -Path $launcherBat -PathType Leaf)) {
    Write-Error "launch_bat.ps1 not found in $LauncherScriptDirectory"
    exit 1
}
if (-not (Test-Path -Path $launcherExe -PathType Leaf)) {
    Write-Error "launch_exe.ps1 not found in $LauncherScriptDirectory"
    exit 1
}

if (-not (Test-Path -Path $ServiceScriptPath -PathType Leaf)) {
    Write-Error "Service creation script not found: $ServiceScriptPath"
    exit 1
}

# Resolve paths to be absolute
try {
    $ConfigFilePath = Resolve-Path -Path $ConfigFilePath -ErrorAction Stop
    $LauncherScriptDirectory = Resolve-Path -Path $LauncherScriptDirectory -ErrorAction Stop
    $ServiceScriptPath = Resolve-Path -Path $ServiceScriptPath -ErrorAction Stop
    $launcherBat = Resolve-Path -Path $launcherBat -ErrorAction Stop
    $launcherExe = Resolve-Path -Path $launcherExe -ErrorAction Stop
}
catch {
    Write-Error "Error resolving script or directory paths: $($_.Exception.Message)"
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


# 3. Iterate and Create Services
$totalEntries = $serverConfigs.Count
$servicesCreatedSuccessfully = 0
$servicesFailed = 0

Write-Host "Starting server part installation. Processing $totalEntries entries from '$ConfigFilePath'."

foreach ($entry in $serverConfigs) {
    # Validate essential properties in the entry
    if (-not $entry.PSObject.Properties['ServiceName'] -or [string]::IsNullOrWhiteSpace($entry.ServiceName)) {
        Write-Warning "Skipping entry due to missing or empty 'ServiceName'. Entry details: $($entry | Out-String)"
        $servicesFailed++
        continue
    }
    $serviceName = $entry.ServiceName

    if (-not $entry.PSObject.Properties['AppPath'] -or [string]::IsNullOrWhiteSpace($entry.AppPath)) {
        Write-Warning "Skipping service '$serviceName' due to missing or empty 'AppPath'. Entry details: $($entry | Out-String)"
        $servicesFailed++
        continue
    }

    $displayName = if ($entry.PSObject.Properties['FriendlyName'] -and -not [string]::IsNullOrWhiteSpace($entry.FriendlyName)) { $entry.FriendlyName } else { $serviceName }
    $description = if ($entry.PSObject.Properties['Description']) { $entry.Description } else { "Service for $displayName" }
    $appPath = $entry.AppPath
    $appArguments = if ($entry.PSObject.Properties['AppArguments']) { $entry.AppArguments } else { "" } # Handle null/missing
    $logDirectory = if ($entry.PSObject.Properties['LogDirectory'] -and -not [string]::IsNullOrWhiteSpace($entry.LogDirectory)) { $entry.LogDirectory } else { Join-Path $LauncherScriptDirectory "$serviceName-Logs" } # Default if missing

    Write-Host "Processing Service: '$serviceName' (Display: '$displayName')"

    # Check if service already exists before attempting to create
    if (Get-Service -Name $serviceName -ErrorAction SilentlyContinue) {
        Write-Warning "Service '$serviceName' already exists. Skipping creation."
        # Consider this a success for the summary if it already exists as per config? Or a separate counter?
        # For now, not incrementing success, as we didn't create it in this run.
        continue
    }

    $params = @{
        ServiceName           = $serviceName
        DisplayName           = $displayName
        Description           = $description
        AppPath               = $appPath
        LogDirectory          = $logDirectory
        LauncherBatPath       = $launcherBat
        LauncherExePath       = $launcherExe
        ErrorAction           = 'SilentlyContinue' # To capture output and check $LASTEXITCODE
        WarningAction         = 'Continue'
    }
    if (-not [string]::IsNullOrWhiteSpace($appArguments)) {
        $params.AppArguments = $appArguments
    }

    try {
        Write-Verbose "Attempting to create service '$serviceName' using '$ServiceScriptPath'."
        if ($PSCmdlet.ShouldProcess($serviceName, "Install Service via $ServiceScriptPath")) {
            # Using Start-Process to capture output and have more control, as directly invoking
            # might mix output streams or terminate this script on error.
            $processArgs = "-NoProfile -ExecutionPolicy Bypass -File ""$ServiceScriptPath"""
            foreach ($key in $params.Keys) {
                # Ensure proper quoting for parameters passed to the new PowerShell process
                $value = $params[$key]
                if ($value -match "\s" -or $value -match "'" -or $value -match '"') { # if value contains space or quotes
                    $processArgs += " -$key ""$($value -replace '"','`"')""" # escape internal quotes if any
                } else {
                     $processArgs += " -$key $value"
                }
            }

            $process = Start-Process powershell.exe -ArgumentList $processArgs -Wait -NoNewWindow -PassThru -RedirectStandardOutput ".\$($serviceName)_install.log" -RedirectStandardError ".\$($serviceName)_install.error.log"

            $stdout = Get-Content ".\$($serviceName)_install.log" -ErrorAction SilentlyContinue
            $stderr = Get-Content ".\$($serviceName)_install.error.log" -ErrorAction SilentlyContinue

            Remove-Item ".\$($serviceName)_install.log" -ErrorAction SilentlyContinue
            Remove-Item ".\$($serviceName)_install.error.log" -ErrorAction SilentlyContinue

            if ($process.ExitCode -eq 0) {
                Write-Host "Successfully initiated creation for service '$serviceName'."
                # Further check if service actually exists now
                 if (Get-Service -Name $serviceName -ErrorAction SilentlyContinue) {
                    Write-Host "Service '$serviceName' confirmed created."
                    $servicesCreatedSuccessfully++
                 } else {
                    Write-Warning "New-AppWindowsService.ps1 for '$serviceName' exited successfully but service not found. Output: $($stdout -join '; ')"
                    if($stderr){ Write-Warning "Errors: $($stderr -join '; ')"}
                    $servicesFailed++
                 }
            } else {
                Write-Warning "Failed to create service '$serviceName'. New-AppWindowsService.ps1 exited with code $($process.ExitCode)."
                Write-Warning "Output from New-AppWindowsService.ps1 for '$serviceName': $($stdout -join '; ')"
                if($stderr){ Write-Warning "Errors: $($stderr -join '; ')"}
                $servicesFailed++
            }
        } else {
            Write-Host "Skipped creation of service '$serviceName' due to -WhatIf preference."
        }
    }
    catch {
        Write-Error "An unexpected error occurred while processing service '$serviceName': $($_.Exception.Message)"
        $servicesFailed++
    }
    Write-Host "--------------------------------------------------"
}

# 4. Summary
Write-Host "=================================================="
Write-Host "Server Part Installation Summary:"
Write-Host "Total entries processed: $totalEntries"
Write-Host "Services created successfully in this run: $servicesCreatedSuccessfully"
Write-Host "Services failed or skipped: $servicesFailed"
Write-Host "=================================================="

if ($servicesFailed -gt 0) {
    Write-Warning "Some services could not be created. Please review the logs above."
    exit 1 # Indicate partial failure
}

exit 0
