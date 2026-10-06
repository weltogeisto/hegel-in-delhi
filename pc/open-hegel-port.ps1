# Lets the Pi reach Hegel's trained mind on port 8082 and turns Windows' own sleep timer off while it is tested (pc/TRAINING.md, steps 6 and 7).
# Welt runs it in PowerShell as Administrator: Codex's approval policy does not start Administrator windows. -Undo puts the timer back.
#   - llama-server.exe on Windows: the firewall rule is all it needs.
#   - llama-server in WSL with mirrored networking: the firewall rule and a rule in WSL's own (Hyper-V) firewall.
#   - llama-server in WSL with NAT networking (WSL's default): the firewall rule and a port forward from the PC's LAN address to WSL's.
#     WSL's address changes when WSL restarts: run this again after a reboot.
param(
  [int]$Port = 8082,
  [switch]$Undo
)
$ErrorActionPreference = "Stop"
$name = "Hegel trained mind $Port"
$saved = "C:\hegel\logs\sleep-timer-before.txt"
$wslVm = "{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}"      # WSL's id in the Hyper-V firewall
$net = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq "Up" } | Select-Object -First 1
$lan = @($net.IPv4Address)[0].IPAddress

if ($Undo) {
  netsh interface portproxy delete v4tov4 listenport=$Port listenaddress=$lan | Out-Null
  if (Test-Path $saved) {
    $minutes = [int](Get-Content $saved -Raw).Trim()
    powercfg /change standby-timeout-ac $minutes
    Remove-Item $saved
    "Windows' sleep timer is back at $minutes min (0 = never)."
  }
  "No port forward any more; the firewall rules stay for the next round."
  exit 0
}

if (-not (Test-Path $saved)) {                          # the value before the first run, not the 0 this script sets
  $hex = [regex]::Matches((powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE | Out-String), "0x[0-9a-fA-F]{8}")
  if ($hex.Count -lt 2) { throw "powercfg did not show the sleep timer" }
  New-Item -ItemType Directory -Force -Path (Split-Path $saved) | Out-Null
  Set-Content -Path $saved -Value ([int]([Convert]::ToInt64($hex[$hex.Count - 2].Value, 16) / 60))   # AC comes before DC
}
powercfg /change standby-timeout-ac 0

if (-not (Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue)) {
  New-NetFirewallRule -DisplayName $name -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow -Profile Private | Out-Null
}
if (Get-NetConnectionProfile | Where-Object { $_.NetworkCategory -eq "Public" }) {
  "Warning: this network is set to Public in Windows; the rule allows Private networks only. Set the home network to Private."
}

$listeners = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
               ForEach-Object { (Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName })
$cfg = Join-Path $env:USERPROFILE ".wslconfig"
$mirrored = (Test-Path $cfg) -and [bool](Select-String -Path $cfg -Pattern "^\s*networkingMode\s*=\s*mirrored" -Quiet)
if ($listeners -contains "llama-server") {
  $how = "llama-server.exe on Windows"
} elseif ($mirrored) {
  if (-not (Get-NetFirewallHyperVRule -Name "Hegel$Port" -ErrorAction SilentlyContinue)) {
    New-NetFirewallHyperVRule -Name "Hegel$Port" -DisplayName $name -Direction Inbound -VMCreatorId $wslVm -Protocol TCP -LocalPorts $Port | Out-Null
  }
  $how = "WSL with mirrored networking"
} else {
  $wsl = (wsl.exe -e hostname -I) -split "\s+" | Where-Object { $_ -match "^\d+\.\d+\.\d+\.\d+$" } | Select-Object -First 1
  if (-not $wsl) { throw "WSL did not give its address: is Ubuntu running?" }
  Start-Service iphlpsvc                                # the service that carries the port forward
  netsh interface portproxy delete v4tov4 listenport=$Port listenaddress=$lan | Out-Null
  netsh interface portproxy add v4tov4 listenport=$Port listenaddress=$lan connectport=$Port connectaddress=$wsl
  $how = "WSL with NAT networking, forwarded ${lan}:$Port -> ${wsl}:$Port"
}
"Port ${Port}: $how. Check from the Pi: curl -s http://${lan}:$Port/health"
"Windows' sleep timer is off (it was $(Get-Content $saved) min). After the Hegel test, run this again with -Undo."
