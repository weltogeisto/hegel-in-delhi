# Starts Hegel's day mind: Ternary Bonsai 27B on llama-server, port 8081.
# Runs in the foreground (-Wait) so Task Scheduler sees it as running.
param(
  [string]$Llama = "C:\hegel\llama\llama-server.exe",
  [string]$Model = "C:\hegel\models\Ternary-Bonsai-27B-Q2_g64.gguf",
  [int]$Port = 8081,
  [int]$Ctx = 16384
)
$logs = "C:\hegel\logs"
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$argList = @("-m", "`"$Model`"", "-ngl", "99", "-c", "$Ctx", "--host", "0.0.0.0", "--port", "$Port", "--alias", "bonsai")
Start-Process -FilePath $Llama -ArgumentList $argList -NoNewWindow -Wait `
  -RedirectStandardOutput "$logs\mind.out.log" -RedirectStandardError "$logs\mind.err.log"
