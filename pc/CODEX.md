# Codex on the PC: set up Hegel's mind

Goal: Ternary Bonsai 27B served by llama.cpp on port 8081. It starts at boot without anyone logging in, the PC wakes on a magic packet from the Pi, and it goes back to sleep when idle.

Run PowerShell as Administrator. Do the steps in order and report each result to Welt in one line, with the exact error text if something fails. Don't improvise around a failure; stop and report.

## 1. Folders and scripts

```powershell
New-Item -ItemType Directory -Force -Path C:\hegel\llama, C:\hegel\models, C:\hegel\logs, C:\hegel\scripts | Out-Null
icacls C:\hegel\logs /grant "Users:(OI)(CI)M" | Out-Null
foreach ($f in "start-mind.ps1","sleep-watchdog.ps1","idle-reporter.ps1") {
  curl.exe -fsSL -o "C:\hegel\scripts\$f" "https://raw.githubusercontent.com/weltogeisto/hegel-in-delhi/main/pc/$f"
}
Get-ChildItem C:\hegel\scripts
```

## 2. llama.cpp (CUDA build)

From https://github.com/ggml-org/llama.cpp/releases/latest download the Windows x64 CUDA build and the matching `cudart` package (same CUDA version). Unzip both into `C:\hegel\llama`.

```powershell
C:\hegel\llama\llama-server.exe --version
```

Report the build number.

## 3. The model (about 7.6 GB)

```powershell
curl.exe -L -o C:\hegel\models\Ternary-Bonsai-27B-Q2_g64.gguf https://huggingface.co/prism-ml/Ternary-Bonsai-27B-gguf/resolve/main/Ternary-Bonsai-27B-Q2_g64.gguf
(Get-Item C:\hegel\models\Ternary-Bonsai-27B-Q2_g64.gguf).Length / 1GB
```

## 4. First run

Stop the Qwen server first if it is running; the two don't fit in 24 GB together.

```powershell
Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File C:\hegel\scripts\start-mind.ps1'
Start-Sleep 60
curl.exe http://127.0.0.1:8081/health
Get-Content C:\hegel\logs\mind.err.log -Tail 20
```

Expected: `{"status":"ok"}`. If the model fails to load with an unknown tensor or quantization type, the llama.cpp build is too old for the ternary format: take a newer release and retry. Report the error line.

## 5. Firewall (home network only)

```powershell
Get-NetConnectionProfile          # the LAN must be "Private"
New-NetFirewallRule -DisplayName "Hegel mind 8081" -Direction Inbound -Protocol TCP -LocalPort 8081 -Action Allow -Profile Private
```

## 6. Autostart without login

```powershell
$s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$p = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
$a = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\hegel\scripts\start-mind.ps1"
Register-ScheduledTask -TaskName "Hegel mind" -Trigger (New-ScheduledTaskTrigger -AtStartup) -Action $a -Principal $p -Settings $s -Force
```

Reboot, don't log in, and ask Welt to check from the Pi: `curl http://<PC IP>:8081/health`.

## 7. Wake on LAN

The PC must be on Ethernet; Wake on LAN over Wi-Fi rarely works.

```powershell
powercfg /a                        # must list "Standby (S3)"; report the full output
powercfg /hibernate off
Get-NetAdapter -Physical | Where-Object Status -eq Up | Format-Table Name, InterfaceDescription, MacAddress, LinkSpeed
Get-NetIPAddress -AddressFamily IPv4 | Where-Object PrefixOrigin -eq Dhcp | Format-Table InterfaceAlias, IPAddress
```

For the Ethernet adapter (replace `Ethernet` with its name):

```powershell
Set-NetAdapterPowerManagement -Name "Ethernet" -WakeOnMagicPacket Enabled -WakeOnPattern Disabled
Get-NetAdapterAdvancedProperty -Name "Ethernet" | Where-Object DisplayName -match "Wake|WOL|Energy|Green"
```

Set any "Wake on Magic Packet" property to Enabled and any "Energy Efficient Ethernet" / "Green Ethernet" to Disabled, then:

```powershell
powercfg /devicequery wake_armed   # the Ethernet adapter must be listed
```

Report to Welt: the MAC address, the IPv4 address, and the `powercfg /a` output. Welt then reserves that IP in the router and enables Wake on LAN in the BIOS (often "Power On By PCI-E"; turn off "ErP" if the board has it).

## 8. Sleep watchdog

Test week: 3 idle minutes. After the test, re-register with `-IdleMinutes 10`.

```powershell
$s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$p = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
$a = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\hegel\scripts\sleep-watchdog.ps1 -IdleMinutes 3"
Register-ScheduledTask -TaskName "Hegel sleep watchdog" -Trigger (New-ScheduledTaskTrigger -AtStartup) -Action $a -Principal $p -Settings $s -Force

$ua = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File C:\hegel\scripts\idle-reporter.ps1"
Register-ScheduledTask -TaskName "Hegel idle reporter" -Trigger (New-ScheduledTaskTrigger -AtLogOn) -Action $ua -Settings $s -Force

Start-ScheduledTask "Hegel sleep watchdog"; Start-ScheduledTask "Hegel idle reporter"
```

Check after a minute: `Get-Content C:\hegel\logs\watchdog.log -Tail 5` and `Get-Content C:\hegel\logs\user-idle.txt`.

To keep the PC awake while Welt works or plays: `New-Item C:\hegel\awake.flag`. Delete the file to let the watchdog work again.
