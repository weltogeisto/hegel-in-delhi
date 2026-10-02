# Runs in the logged-on user's session (Task Scheduler: at log on).
# Every 30 seconds it writes the minutes since the last keyboard or mouse input,
# so the sleep watchdog never puts the PC to sleep while Welt is using it.
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class HegelIdle {
  [StructLayout(LayoutKind.Sequential)] public struct LII { public uint cbSize; public uint dwTime; }
  [DllImport("user32.dll")] public static extern bool GetLastInputInfo(ref LII p);
  public static double Minutes() {
    LII l = new LII(); l.cbSize = (uint)Marshal.SizeOf(typeof(LII));
    GetLastInputInfo(ref l);
    return unchecked((uint)Environment.TickCount - l.dwTime) / 60000.0;
  }
}
"@
$file = "C:\hegel\logs\user-idle.txt"
$inv = [Globalization.CultureInfo]::InvariantCulture
while ($true) {
  Set-Content -Path $file -Value ([HegelIdle]::Minutes().ToString("0.0", $inv))
  Start-Sleep -Seconds 30
}
