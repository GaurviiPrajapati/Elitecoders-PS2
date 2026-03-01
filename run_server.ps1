<#
Simple PowerShell utility to start/stop the SME Web UI backend.

Usage:
  .\run_server.ps1 -action start    # launch uvicorn in background and record PID
  .\run_server.ps1 -action stop     # kill process previously started
  .\run_server.ps1 -action status   # show current state

This uses the .venv environment that's already present in the workspace.
The script writes the PID to "server.pid" in the same folder so that it can
be stopped later.  Running "start" when the server is already running will
warn you and do nothing.
#>

param(
    [ValidateSet('start','stop','status')]
    [string]$action = 'status'
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $root 'server.pid'
$python = Join-Path $root '.venv\Scripts\python.exe'
$uvicornArgs = '-m uvicorn AI_Backend.api:app --host 0.0.0.0 --port 8000'

function Start-Server {
    if (Test-Path $pidFile) {
        Write-Warning "PID file exists; server may already be running."
        return
    }

    $proc = Start-Process -FilePath $python -ArgumentList $uvicornArgs -PassThru -WindowStyle Hidden
    $proc.Id | Out-File $pidFile -Encoding ascii
    Write-Host "Started server (PID $($proc.Id))."
}

function Stop-Server {
    if (-not (Test-Path $pidFile)) {
        Write-Warning "No PID file found; is the server running?"
        return
    }
    $pidValue = Get-Content $pidFile | Out-String
    Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
    Remove-Item $pidFile -ErrorAction SilentlyContinue
    Write-Host "Stopped server (PID $pidValue)."
}

function Status-Server {
    if (Test-Path $pidFile) {
        $pidValue = Get-Content $pidFile | Out-String
        if (Get-Process -Id $pidValue -ErrorAction SilentlyContinue) {
            Write-Host "Server running (PID $pidValue)."
        } else {
            Write-Warning "Stale PID file found; server not running. Removing file."
            Remove-Item $pidFile -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "Server not running."
    }
}

switch ($action) {
    'start' { Start-Server }
    'stop'  { Stop-Server }
    'status'{ Status-Server }
}
