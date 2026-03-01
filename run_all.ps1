Param(
    [ValidateSet("start","stop","status","restart")]
    [string]$Action = "start"
)

# Root of the repository
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$RunDir = Join-Path $Root ".run"
$pidsFile = Join-Path $RunDir "pids.json"

if (-not (Test-Path $RunDir)) { New-Item -ItemType Directory -Path $RunDir | Out-Null }

function Save-Pids($obj) {
    $json = $obj | ConvertTo-Json -Depth 4
    $json | Set-Content -Path $pidsFile -Encoding UTF8
}
function Load-Pids() {
    if (Test-Path $pidsFile) { Get-Content -Path $pidsFile -Raw | ConvertFrom-Json } else { @{} }
}

function Start-Services {
    Write-Host "Starting services..."

    # Python executable from virtualenv
    $venvPython = Join-Path $Root "sme_env\Scripts\python.exe"

    if (-not (Test-Path $venvPython)) {
        Write-Warning "Virtualenv python not found at $venvPython. Try creating the venv or install Python and recreate the venv."
    }

    # Start Python AI service (AI_Backend/api.py)
    if (Test-Path $venvPython) {
        $ai = Start-Process -FilePath $venvPython -ArgumentList 'AI_Backend\api.py' -WorkingDirectory $Root -PassThru
        Write-Host "AI service started (PID: $($ai.Id))"
    } else {
        $ai = $null
    }

    # Start Node backend (backend_server/server.js)
    $nodeCmd = (Get-Command node -ErrorAction SilentlyContinue)
    if ($nodeCmd) {
        $backend = Start-Process -FilePath 'node' -ArgumentList 'server.js' -WorkingDirectory (Join-Path $Root 'backend_server') -PassThru
        Write-Host "Node backend started (PID: $($backend.Id))"
    } else {
        Write-Warning "Node not found in PATH. Install Node.js or add it to PATH to start backend."
        $backend = $null
    }

    # Start simple static server for UI on port 3000
    if (Test-Path $venvPython) {
        $ui = Start-Process -FilePath $venvPython -ArgumentList '-m', 'http.server', '3000' -WorkingDirectory (Join-Path $Root 'sme-ui') -PassThru
        Write-Host "UI server started on port 3000 (PID: $($ui.Id))"
    } else {
        Write-Warning "Cannot start UI server: python executable not available."
        $ui = $null
    }

    $toSave = @{}
    if ($ai) { $toSave.ai = $ai.Id }
    if ($backend) { $toSave.backend = $backend.Id }
    if ($ui) { $toSave.ui = $ui.Id }

    if ($toSave.Keys.Count -gt 0) { Save-Pids $toSave }
    Write-Host "Start complete. Use './run_all.ps1 status' to check processes."
}

function Stop-Services {
    Write-Host "Stopping services..."
    $p = Load-Pids

    if ($null -eq $p -or $p.PSObject.Properties.Count -eq 0) {
        Write-Host "No PID file found. Nothing to stop."
        return
    }

    foreach ($name in $p.PSObject.Properties.Name) {
        $processId = [int]$p.$name
        $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue

        if ($proc) {
            try {
                Stop-Process -Id $processId -Force -ErrorAction Stop
                Write-Host ("Stopped {0} (PID {1})" -f $name, $processId)
            }
            catch {
                Write-Warning ("Failed to stop {0} (PID {1}): {2}" -f $name, $processId, $_)
            }
        }
        else {
            Write-Host ("{0} (PID {1}) not running" -f $name, $processId)
        }
    }   # ← THIS WAS MISSING

    if (Test-Path $pidsFile) {
        Remove-Item $pidsFile -Force
    }

    Write-Host "Stop complete."
}
function Status-Services {
    Write-Host "Checking status..."
    $p = Load-Pids
    if ($null -eq $p -or $p.PSObject.Properties.Count -eq 0) { Write-Host "No PID file found. Services may not be running."; return }

    foreach ($name in $p.PSObject.Properties.Name) {
        $processid = [int]$p.$name
        $proc = Get-Process -Id $processid -ErrorAction SilentlyContinue
        if ($proc) { Write-Host "${name}: RUNNING (PID $processid) - $($proc.ProcessName)" }
        else { Write-Host "${name}: NOT RUNNING (expected PID $processid)" }
    }
}

switch ($Action) {
    'start' { Start-Services }
    'stop' { Stop-Services }
    'status' { Status-Services }
    'restart' { Stop-Services; Start-Sleep -Seconds 1; Start-Services }
}
