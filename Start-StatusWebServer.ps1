<#
.SYNOPSIS
Starts a simple HTTP server to display server part statuses.

.DESCRIPTION
This script launches a basic HTTP server that serves an HTML dashboard and a JSON endpoint
for server statuses. The status is retrieved by invoking Get-ServerPartStatus.ps1.

.PARAMETER Port
The port number for the web server. Defaults to 8088.

.PARAMETER ConfigFilePath
Path to the server_config.json file. Mandatory.

.PARAMETER GetStatusScriptPath
Path to Get-ServerPartStatus.ps1. Mandatory.

.PARAMETER HtmlFilePath
Path to status_dashboard.html. Mandatory.

.EXAMPLE
.\Start-StatusWebServer.ps1 -ConfigFilePath ".\server_config.json" -GetStatusScriptPath ".\Get-ServerPartStatus.ps1" -HtmlFilePath ".\status_dashboard.html" -Port 8080

.NOTES
Runs continuously until stopped (Ctrl+C).
Ensure Get-ServerPartStatus.ps1 and the HTML file are accessible.
Firewall rules may need adjustment for non-localhost access.
For production use, a more robust web server solution is recommended.
#>
[CmdletBinding()]
param (
    [Parameter(Mandatory = $false)]
    [int]$Port = 8088,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ConfigFilePath,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$GetStatusScriptPath,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$HtmlFilePath
)

# Validate paths
if (-not (Test-Path -Path $ConfigFilePath -PathType Leaf)) {
    Write-Error "Configuration file not found: $ConfigFilePath"
    exit 1
}
if (-not (Test-Path -Path $GetStatusScriptPath -PathType Leaf)) {
    Write-Error "GetStatusScriptPath not found: $GetStatusScriptPath"
    exit 1
}
if (-not (Test-Path -Path $HtmlFilePath -PathType Leaf)) {
    Write-Error "HtmlFilePath not found: $HtmlFilePath"
    exit 1
}

# Resolve paths to absolute
try {
    $ConfigFilePath = Resolve-Path -Path $ConfigFilePath -ErrorAction Stop
    $GetStatusScriptPath = Resolve-Path -Path $GetStatusScriptPath -ErrorAction Stop
    $HtmlFilePath = Resolve-Path -Path $HtmlFilePath -ErrorAction Stop
}
catch {
    Write-Error "Error resolving script or file paths: $($_.Exception.Message)"
    exit 1
}


$listener = New-Object System.Net.HttpListener
$prefix = "http://localhost:$Port/" # Listen on localhost only
$listener.Prefixes.Add($prefix)
# For listening on all interfaces: "http://*:$Port/" - requires admin and URL ACL configuration (netsh http add urlacl)
# For this task, localhost is sufficient and generally doesn't require special permissions on non-privileged ports.

try {
    $listener.Start()
    Write-Host "Status dashboard web server running on $prefix"
    Write-Host "Access the dashboard at ${prefix}status_dashboard.html or $prefix"
    Write-Host "Press Ctrl+C to stop the server."

    while ($listener.IsListening) {
        try {
            $context = $listener.GetContext() # Blocks until a request comes in
            $request = $context.Request
            $response = $context.Response

            Write-Verbose "Received request: $($request.HttpMethod) $($request.Url.AbsolutePath)"

            switch ($request.Url.AbsolutePath) {
                "/" {
                    $response.ContentType = "text/html"
                    $htmlContent = Get-Content -Path $HtmlFilePath -Raw -ErrorAction SilentlyContinue
                    if ($null -eq $htmlContent) {
                        $response.StatusCode = 500
                        $errorMessage = "Error: Could not read HTML file at $HtmlFilePath"
                        $buffer = [System.Text.Encoding]::UTF8.GetBytes($errorMessage)
                        $response.ContentLength64 = $buffer.Length
                        $response.OutputStream.Write($buffer, 0, $buffer.Length)
                        Write-Warning $errorMessage
                    } else {
                        $buffer = [System.Text.Encoding]::UTF8.GetBytes($htmlContent)
                        $response.ContentLength64 = $buffer.Length
                        $response.OutputStream.Write($buffer, 0, $buffer.Length)
                    }
                }
                "/status_dashboard.html" {
                     $response.ContentType = "text/html"
                    $htmlContent = Get-Content -Path $HtmlFilePath -Raw -ErrorAction SilentlyContinue
                    if ($null -eq $htmlContent) {
                        $response.StatusCode = 500
                        $errorMessage = "Error: Could not read HTML file at $HtmlFilePath"
                        $buffer = [System.Text.Encoding]::UTF8.GetBytes($errorMessage)
                        $response.ContentLength64 = $buffer.Length
                        $response.OutputStream.Write($buffer, 0, $buffer.Length)
                        Write-Warning $errorMessage
                    } else {
                        $buffer = [System.Text.Encoding]::UTF8.GetBytes($htmlContent)
                        $response.ContentLength64 = $buffer.Length
                        $response.OutputStream.Write($buffer, 0, $buffer.Length)
                    }
                }
                "/status" {
                    $response.ContentType = "application/json"
                    # Execute Get-ServerPartStatus.ps1 and capture its JSON output
                    # Using Start-Process to ensure it runs in a separate scope and captures standard output correctly.
                    $pwshArgs = "-NoProfile -ExecutionPolicy Bypass -File ""$GetStatusScriptPath"" -ConfigFilePath ""$ConfigFilePath"" -OutputToJson"
                    
                    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
                    $processInfo.FileName = "powershell.exe"
                    $processInfo.Arguments = $pwshArgs
                    $processInfo.RedirectStandardOutput = $true
                    $processInfo.RedirectStandardError = $true
                    $processInfo.UseShellExecute = $false
                    $processInfo.CreateNoWindow = $true
                    
                    $process = New-Object System.Diagnostics.Process
                    $process.StartInfo = $processInfo
                    
                    $process.Start() | Out-Null
                    $jsonOutput = $process.StandardOutput.ReadToEnd()
                    $jsonError = $process.StandardError.ReadToEnd()
                    $process.WaitForExit()

                    if ($process.ExitCode -ne 0 -or -not [string]::IsNullOrWhiteSpace($jsonError)) {
                        $response.StatusCode = 500
                        $errorMsg = "Error executing Get-ServerPartStatus.ps1. ExitCode: $($process.ExitCode). Errors: $jsonError. Output: $jsonOutput"
                        Write-Warning $errorMsg
                        $buffer = [System.Text.Encoding]::UTF8.GetBytes("{""error"": ""Failed to retrieve status. Check server logs.""}")
                    } elseif ([string]::IsNullOrWhiteSpace($jsonOutput)) {
                        $response.StatusCode = 500 # Or 204 No Content, but client expects JSON
                        Write-Warning "Get-ServerPartStatus.ps1 returned empty output."
                        $buffer = [System.Text.Encoding]::UTF8.GetBytes("{""error"": ""Status script returned empty output.""}")
                    } else {
                        $buffer = [System.Text.Encoding]::UTF8.GetBytes($jsonOutput)
                    }
                    $response.ContentLength64 = $buffer.Length
                    $response.OutputStream.Write($buffer, 0, $buffer.Length)
                }
                default {
                    $response.StatusCode = 404
                    $response.ContentType = "text/plain"
                    $errorMessage = "Error 404: Not Found"
                    $buffer = [System.Text.Encoding]::UTF8.GetBytes($errorMessage)
                    $response.ContentLength64 = $buffer.Length
                    $response.OutputStream.Write($buffer, 0, $buffer.Length)
                }
            }
        }
        catch [System.Net.HttpListenerException] {
            # This exception can occur if the listener is stopped while GetContext() is blocking.
            if ($_.Exception.ErrorCode -eq 995) { # ERROR_OPERATION_ABORTED
                Write-Host "Listener operation aborted (likely due to stopping the server)."
            } else {
                Write-Warning "HttpListenerException in request loop: $($_.Exception.Message) (ErrorCode: $($_.Exception.ErrorCode))"
            }
            # Continue if listener is still listening, otherwise loop will exit.
        }
        catch {
            Write-Warning "Error in request processing loop: $($_.Exception.Message)"
            # Attempt to send a generic 500 error to the client if response is still writable
            if ($response -and -not $response.OutputStream.CanWrite) {
                 # Cannot write to response, maybe already closed or in error state.
            } elseif ($response) {
                try {
                    $response.StatusCode = 500
                    $response.ContentType = "text/plain"
                    $errorBuffer = [System.Text.Encoding]::UTF8.GetBytes("Internal Server Error")
                    $response.ContentLength64 = $errorBuffer.Length
                    $response.OutputStream.Write($errorBuffer, 0, $errorBuffer.Length)
                } catch {
                    Write-Warning "Failed to send 500 error to client: $($_.Exception.Message)"
                }
            }
        }
        finally {
            if ($response) {
                try {
                    $response.OutputStream.Close()
                } catch {
                    # Ignore errors closing an already closed or errored stream
                }
            }
        }
    }
}
catch [System.Net.Sockets.SocketException] {
    # Common issue: port already in use
    if ($_.Exception.SocketErrorCode -eq 'AddressAlreadyInUse') {
        Write-Error "Failed to start listener: Port $Port is already in use. (SocketErrorCode: $($_.Exception.SocketErrorCode))"
    } else {
        Write-Error "Failed to start listener: $($_.Exception.Message) (SocketErrorCode: $($_.Exception.SocketErrorCode))"
    }
}
catch {
    Write-Error "An unexpected error occurred: $($_.Exception.Message)"
}
finally {
    if ($listener -and $listener.IsListening) {
        Write-Host "Stopping the web server..."
        $listener.Stop()
        $listener.Close() # Release resources
        Write-Host "Web server stopped."
    }
}
