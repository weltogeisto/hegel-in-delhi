# Starts Hegel's trained mind: the installed Qwen 27B GGUF with the Hegel LoRA on top, llama-server, port 8082 (pc/TRAINING.md, step 6).
# Runs in the foreground (-Wait), like start-mind.ps1. It is started by hand for the tests: the "Hegel mind" task keeps starting Bonsai.
param(
  [string]$Llama = "C:\hegel\llama\llama-server.exe",
  [string]$Model = "C:\hegel\models\QWEN-GGUF-FILENAME.gguf",   # Codex: the installed Qwen file that step 1 reported
  [string]$Lora = "C:\hegel\models\hegel-lora.gguf",
  [int]$Port = 8082,
  [string]$Alias = "hegel",
  [int]$Ctx = 16384,
  [switch]$Force
)
$logs = "C:\hegel\logs"
New-Item -ItemType Directory -Force -Path $logs | Out-Null
foreach ($f in @($Llama, $Model, $Lora)) {
  if (-not (Test-Path $f)) { Write-Error "missing: $f"; exit 1 }       # an unfilled QWEN-GGUF-FILENAME stops here
}
# One 27B fits in the 24 GB at a time: any other llama-server must be stopped first.
$others = Get-NetTCPConnection -State Listen -LocalPort 8080, 8081, 8082 -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -ne $Port }
if ($others -and -not $Force) {
  Write-Error ("a llama-server is already listening on port " + (($others.LocalPort | Sort-Object -Unique) -join ", ") + "; stop it first, or pass -Force")
  exit 1
}
$argList = @("-m", "`"$Model`"", "--lora", "`"$Lora`"", "-ngl", "99", "-c", "$Ctx", "--host", "0.0.0.0", "--port", "$Port", "--alias", $Alias)
Start-Process -FilePath $Llama -ArgumentList $argList -NoNewWindow -Wait `
  -RedirectStandardOutput "$logs\$Alias.out.log" -RedirectStandardError "$logs\$Alias.err.log"
