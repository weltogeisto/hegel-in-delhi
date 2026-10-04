# Puts the PC to sleep when Hegel's mind and Welt have both been idle.
# Runs as SYSTEM at startup. When in doubt, it stays awake.
#   - Mind activity: any established connection to the llama-server ports (8080 Qwen, 8081 Bonsai, 8082 the trained Hegel on Qwen).
#   - User activity: C:\hegel\logs\user-idle.txt, written by idle-reporter.ps1.
#   - Override: while C:\hegel\awake.flag exists, the PC never sleeps.
param(
  [int]$IdleMinutes = 10,
  [int[]]$Ports = @(8080, 8081, 8082),
  [int]$PollSeconds = 15
)
Add-Type -AssemblyName System.Windows.Forms
$root = "C:\hegel"
$flag = "$root\awake.flag"
$log = "$root\logs\watchdog.log"
$idleFile = "$root\logs\user-idle.txt"
$inv = [Globalization.CultureInfo]::InvariantCulture
New-Item -ItemType Directory -Force -Path "$root\logs" | Out-Null
function Log([string]$m) { Add-Content -Path $log -Value ("{0} {1}" -f (Get-Date -Format s), $m) }

function UserIdleMinutes {
  # No fresh report means nobody is logged on: treat as idle.
  if (-not (Test-Path $idleFile)) { return [double]::PositiveInfinity }
  $age = ((Get-Date) - (Get-Item $idleFile).LastWriteTime).TotalMinutes
  if ($age -gt 2) { return [double]::PositiveInfinity }
  $v = 0.0
  $text = (Get-Content $idleFile -Raw).Trim()
  if ([double]::TryParse($text, [Globalization.NumberStyles]::Float, $inv, [ref]$v)) { return $v }
  return 0.0   # unreadable: assume Welt is active
}

$lastActive = Get-Date
$lastTick = Get-Date
Log "start: idle $IdleMinutes min, ports $($Ports -join ',')"
while ($true) {
  Start-Sleep -Seconds $PollSeconds
  $now = Get-Date
  if (($now - $lastTick).TotalSeconds -gt 3 * $PollSeconds) {
    $lastActive = $now      # just woke up: give the Pi time to ask its question
    Log "resumed"
  }
  $lastTick = $now

  $busy = Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue |
          Where-Object { $Ports -contains $_.LocalPort }
  if ($busy -or (Test-Path $flag)) { $lastActive = $now; continue }

  $mindIdle = ($now - $lastActive).TotalMinutes
  $userIdle = UserIdleMinutes
  if ($mindIdle -ge $IdleMinutes -and $userIdle -ge $IdleMinutes) {
    Log ("sleep: mind idle {0:N1} min, user idle {1}" -f $mindIdle, $userIdle)
    $ok = [System.Windows.Forms.Application]::SetSuspendState([System.Windows.Forms.PowerState]::Suspend, $false, $false)
    if (-not $ok) {
      Log "SetSuspendState refused; trying powrprof"
      & rundll32.exe powrprof.dll,SetSuspendState 0,1,0
    }
    $lastActive = Get-Date
    $lastTick = Get-Date
  }
}
