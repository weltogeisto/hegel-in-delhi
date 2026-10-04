# Codex on the PC: train Hegel's own mind

Goal: a LoRA adapter that makes the installed Qwen3.8-27B sound like Hegel and know the world's format, served on port 8082 on top of the Qwen GGUF the PC already has. Bonsai (8081) and the plain Qwen (8080) stay as they are, so the Hegel test can compare all three.

The adapter learns from two sources only: Hegel's own books (the shelf, public domain) and Qwen's own best decisions in rehearsal days, chosen by the world. One more source keeps it from forgetting general skills: human-written answers from a public dataset. **No training data may be written by Claude or any other outside model**: don't add, edit or "improve" any example by hand or with another AI. If a file looks wrong, report it.

Do the steps in order and report each result to Welt in one line, with the exact error text if something fails. Don't improvise around a failure; stop and report. Windows commands run in PowerShell as Administrator; Linux commands run in the WSL2 Ubuntu shell.

**Before you start.** This runbook builds on `pc/CODEX.md` (llama.cpp in `C:\hegel\llama`, Bonsai as the "Hegel mind" task, the sleep watchdog). If parts of it were never done, say so in step 1 and skip the lines here that touch "Hegel mind", the watchdog or `C:\hegel\awake.flag`; everything else stands. Welt is needed at these points, so ask and wait: the reboot and the Ubuntu user name in step 2, the base model in step 3 if there is no exact match, the go after the samples in step 4, and the projection in step 5 if it is over 20 hours. The long runs (the distillation, the training) go into tmux: start them, report that they are running with the first progress line, and end your turn. When Welt asks you to check, attach, report the last progress line, and carry on with the next step once the run says it is done; after a crash, run the same command again (step 4) or add `--resume` (step 5).

| Step | What | PC time |
|---|---|---|
| 1 | Report what is installed | 5 min |
| 2 | WSL2, CUDA, Python | 30–60 min, about 10 GB of downloads |
| 3 | The base model in Hugging Face format | 20–90 min, 17–55 GB of downloads |
| 4 | The data: books, general set, distillation with Qwen | 10 min, then **5–8 hours** with Qwen on the GPU |
| 5 | Dry run, then the training | 30 min, then **8–16 hours** |
| 6 | Convert the adapter, serve it on 8082 | 20 min |
| 7 | Hand over to Hermes for the Hegel test | 20–60 min of PC time |

Steps 4 and 5 run for hours unattended. During them the GPU is busy, so **the world on the Pi must not be live**: ask Welt to pause it before step 4 and to say when it may run again.

## 1. Report what is installed

The training needs llama.cpp's `llama-server` twice: to serve Qwen for the rehearsal days (step 4) and to serve the finished adapter (step 6). If `C:\hegel\llama\llama-server.exe` is missing, that is expected on a PC where `pc/CODEX.md` was never run: install it, don't stop. From https://github.com/ggml-org/llama.cpp/releases/latest download the Windows x64 CUDA build and the matching `cudart` package (same CUDA version) and unzip both into `C:\hegel\llama`. A current release reads Qwen3.8 (architecture `qwen35`).

**If Windows blocks it** (Smart App Control refuses the unsigned llama.cpp DLLs), or Qwen already runs on llama.cpp inside WSL: use llama.cpp in WSL for everything and skip the Windows build. Don't turn Smart App Control off; once off, Windows cannot turn it back on. Report the WSL server's build and the GGUF it serves (`ps aux | grep llama-server`). Step 4 talks to it on `127.0.0.1:8080` as written; step 6 serves the adapter from WSL (see there).

```powershell
nvidia-smi
Get-PSDrive C | Format-Table Used, Free
(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB
[System.Environment]::OSVersion.Version
C:\hegel\llama\llama-server.exe --version
Get-PSDrive -PSProvider FileSystem | ForEach-Object { Get-ChildItem "$($_.Root)" -Filter *.gguf -Recurse -ErrorAction SilentlyContinue } | Format-Table FullName, @{n='GB';e={[math]::Round($_.Length/1GB,1)}}
Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'llama|ollama|lm ?studio|lms' } | Format-List Name, ProcessId, CommandLine
```

If the Qwen server is running, also:

```powershell
curl.exe http://127.0.0.1:8080/v1/models
curl.exe http://127.0.0.1:8080/props
```

Report to Welt: GPU and driver version, free disk on C:, RAM, the Windows build, the llama.cpp build number, the full path of the Qwen3.8-27B GGUF, and what serves Qwen today (llama-server, Ollama, LM Studio or something else) with its command line. If Qwen lives only in Ollama, its GGUF is the largest file under `%USERPROFILE%\.ollama\models\blobs` (no extension): report that path; llama-server reads it as it is. Training needs about **90 GB free** on the disk that holds WSL; if there is less, stop and report.

## 2. WSL2, CUDA, Python

```powershell
wsl --install -d Ubuntu-24.04
```

Reboot if asked, open Ubuntu, create the user. Then give WSL enough memory and let it reach the Windows servers on `127.0.0.1`. Write `%UserProfile%\.wslconfig` (set `memory` to about three quarters of the RAM from step 1, at most 48GB):

```powershell
@"
[wsl2]
memory=24GB
swap=32GB
networkingMode=mirrored
"@ | Set-Content -Encoding ascii $env:USERPROFILE\.wslconfig
wsl --shutdown
```

`networkingMode=mirrored` needs Windows 11 22H2 or later. On older Windows, leave that line out; in step 4 use the PC's own LAN address instead of `127.0.0.1`.

In Ubuntu:

```bash
nvidia-smi                      # must show the 3090. Never install a Linux NVIDIA driver inside WSL: the Windows driver serves it.
sudo apt update && sudo apt install -y python3-venv python3-pip git tmux build-essential
git clone https://github.com/weltogeisto/hegel-in-delhi ~/hegel-in-delhi
cd ~/hegel-in-delhi && git log -1 --oneline
python3 -m unittest discover -s tests   # prints OK (about two minutes)
```

The training stack goes into its own virtual environment:

```bash
python3 -m venv ~/hegel-train && source ~/hegel-train/bin/activate
pip install --upgrade pip
pip install unsloth "huggingface_hub[cli]" gguf
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
python -c "import transformers, unsloth; print('transformers', transformers.__version__, 'unsloth', unsloth.__version__)"
mkdir -p ~/hegel-in-delhi/pc/out && pip freeze > ~/hegel-in-delhi/pc/out/requirements.txt
```

Versions are not pinned by hand. Unsloth pins torch, transformers, trl, peft and bitsandbytes to a combination it has tested, and the model family decides the minimum transformers version. `pc/out/requirements.txt` records what was installed; the training also writes the versions into `pc/out/hegel-lora/training.json`. Report both lines: the torch line must end in `True NVIDIA GeForce RTX 3090`, and transformers must be 5 or later (Qwen3.8 uses the `qwen3_5` architecture, which needs Transformers v5). If it is older, run `pip install -U unsloth unsloth_zoo "transformers>=5"` once and report again. Send Welt `pc/out/requirements.txt`.

## 3. The base model in Hugging Face format

The adapter must be trained on exactly the model the PC serves: Qwen3.8-27B. Check that the GGUF says so (replace the path with the one from step 1; `C:\` is `/mnt/c/` in WSL):

```bash
source ~/hegel-train/bin/activate
gguf-dump --no-tensors "/mnt/c/path/to/the-qwen.gguf" | grep -E "general\.(architecture|name|basename|size_label|version|finetune|base_model)|\.context_length"
```

Expected: the architecture `qwen35` (Qwen3.8 uses the Qwen3.5 architecture), a size of 27B, and `general.base_model.0.repo_url` pointing at `Qwen/Qwen3.8-27B` (or the name and size saying Qwen3.8 27B). Report all the lines.

The base for training is Unsloth's pre-quantized 4-bit copy, `unsloth/Qwen3.8-27B-unsloth-bnb-4bit` (about 17 GB): the one their Qwen3.8 guide uses, and with which a 27B fits the 3090's 24 GB.

**Stop and report** if the GGUF is not Qwen3.8-27B, or is a community fine-tune of it (a `finetune` field with words like abliterated, uncensored, distill), or if that repository does not answer: `curl -s -o /dev/null -w '%{http_code}\n' https://huggingface.co/api/models/unsloth/Qwen3.8-27B-unsloth-bnb-4bit` must print `200`. Welt decides then; don't pick a near match.

```bash
hf download unsloth/Qwen3.8-27B-unsloth-bnb-4bit --local-dir ~/models/qwen-base
du -sh ~/models/qwen-base && ls ~/models/qwen-base
```

Report the repository and the size. `~/models/qwen-base` is the `--base` of steps 5 and 6.

## 4. The data

Keep the PC awake (the sleep watchdog does not see the training as activity), and keep Bonsai from starting, even after a reboot:

```powershell
New-Item -Force C:\hegel\awake.flag
Disable-ScheduledTask "Hegel mind" -ErrorAction SilentlyContinue | Out-Null
Stop-ScheduledTask "Hegel mind" -ErrorAction SilentlyContinue
Stop-Process -Name llama-server -ErrorAction SilentlyContinue
```

If Windows' own sleep timer is on (Settings → System → Power → when plugged in, sleep after), set it to Never for steps 4 and 5 and note the old value. Stop whatever served Qwen until now (Ollama, LM Studio), so that only one model is on the GPU, and serve Qwen with llama-server on port 8080 (the GGUF path from step 1):

```powershell
Start-Process C:\hegel\llama\llama-server.exe -ArgumentList '-m "C:\path\to\qwen3.8-27b.gguf" -ngl 99 -c 16384 --host 0.0.0.0 --port 8080 --alias qwen'
```

In Ubuntu (the data tool needs only Python's standard library, no virtual environment):

```bash
cd ~/hegel-in-delhi
python3 tools/train_data.py --corpus          # about 10 s: about 2,500 documents, about 3.4 M tokens: his books, his papers, his letters and two lives of him
python3 tools/train_data.py --general 1500    # a few minutes, needs the internet: human-written answers, Apache-2.0 and ODC-BY
curl -s http://127.0.0.1:8080/health          # must answer {"status":"ok"}; without mirrored networking use the PC's LAN address
```

Now the distillation. It rehearses 20 days of the world with Qwen as the mind, asks Qwen four times at every decision, lets the world reject what breaks its rules or knows too much after 1831, and keeps the best of the rest. Run it in tmux so that a closed window doesn't stop it:

```bash
tmux new -s distill
cd ~/hegel-in-delhi
python3 tools/train_data.py --distill --url http://127.0.0.1:8080 --days 20 --candidates 4 --start 2026-10-03 2>&1 | tee -a mind/train/distill.log
```

It prints one line per decision with an ETA. Expect 5 to 8 hours. Detach with `Ctrl-B d`, look again with `tmux attach -t distill`.

- **Pause or crash:** `Ctrl-C`, a reboot or a Qwen server that stops answering ends the run without losing a step. Run the same command again and it carries on.
- **Faster, optional:** restart Qwen with `-np 4` and four times its usual `-c`, then add `--workers 4` to the command. The four candidates are then asked at once, about twice as fast. If VRAM runs out, go back to the plain command; the run resumes.
- **It refuses to start** with "a rehearsal that started ...": an earlier run with other settings is in `mind/train/rehearsal`. Report it; don't delete it without Welt.

When it says `done`:

```bash
python3 tools/train_data.py --stats | tee mind/train/stats.txt
source ~/hegel-train/bin/activate && python pc/train_hegel.py --check-data --strict
```

`--check-data` must end with `data ok`. Send Welt `mind/train/stats.txt` (counts, token estimates and random samples) and wait for Welt's go before step 5. Welt reads the samples; if they read badly, training on them is wasted time. Stop the Qwen server once Welt has the samples.

## 5. Dry run, then the training

Nothing else may be on the GPU now: no Bonsai, no Qwen server. `C:\hegel\awake.flag` stays.

```bash
tmux new -s train
source ~/hegel-train/bin/activate && cd ~/hegel-in-delhi
python pc/train_hegel.py --base ~/models/qwen-base --dry-run 2>&1 | tee pc/out/dryrun.log
```

The dry run loads the model (5–10 minutes), runs five steps of each phase and prints, per phase, the peak VRAM and a projection (`projection: N s per step x M steps = H h`). Report both projection lines and the peak VRAM.

- **Out of memory:** add `--seq-format 3072` and try again; if it still runs out, also `--rank 16`. Report which settings ran and use the same for the real run. If `--seq-format 3072` makes the data check say that over a fifth of the examples are too long, stop and report.
- **Speed:** Unsloth already brings the speed-ups that are documented for this kind of run (its own kernels, its gradient checkpointing, the books packed into full blocks of 2048 tokens). What is left is training on fewer tokens: `--epochs-format 1` takes one pass over the decisions instead of two and saves a third of the time, more or less.
- **Projection over 20 hours** for both phases together: report it. Welt picks between fewer books (`python3 tools/train_data.py --corpus --max-chars 6000000`, about half), one pass over the decisions (`--epochs-format 1`), or the long run.
- **"the model's chat template does not render the prompt as the beginning of the full chat":** stop and report the whole message.

Then the real run, with the settings the dry run proved:

```bash
python pc/train_hegel.py --base ~/models/qwen-base 2>&1 | tee -a pc/out/train.log
```

Phase 1 trains on his books, his early papers, his letters (1785-1831, edited 1887) and two lives of him, Rosenkranz's and Caird's (about 3.4 M tokens, one pass), phase 2 on the decisions, plans, writings and voices mixed one to one with the general set (two passes). It prints a line per step with the loss. Expect 8 to 16 hours, or what the dry run projected. A checkpoint is saved every 25 steps.

- **After a crash or reboot:** the same command with `--resume`. A finished phase 1 is not trained again.
- **The loss** should fall in the first hundred steps of each phase and then flatten. Report it if it rises steadily, reads `nan`, or stays at 0.

When it says `adapter saved to .../pc/out/hegel-lora`, send Welt `pc/out/hegel-lora/training.json` and the last 30 lines of `pc/out/train.log`.

## 6. Convert the adapter and serve it on port 8082

llama.cpp's converter turns the adapter into a GGUF adapter. Use the same llama.cpp build as the Windows `llama-server` (the build number from step 1), in its own environment so that it doesn't disturb the training stack:

```bash
python3 -m venv ~/llama-convert && source ~/llama-convert/bin/activate
git clone --depth 1 --branch b<BUILD> https://github.com/ggml-org/llama.cpp ~/llama.cpp
pip install -r ~/llama.cpp/requirements/requirements-convert_lora_to_gguf.txt
cd ~/hegel-in-delhi
python ~/llama.cpp/convert_lora_to_gguf.py pc/out/hegel-lora --base ~/models/qwen-base --outtype f16 --outfile pc/out/hegel-lora.gguf
ls -lh pc/out/hegel-lora.gguf && cp pc/out/hegel-lora.gguf /mnt/c/hegel/models/
```

- If it complains about the base's config (a 4-bit `quantization_config`), run it again with `--base-model-id Qwen/Qwen3.8-27B` in place of `--base ~/models/qwen-base`.
- If it names an unsupported architecture or tensor: take the latest llama.cpp release for both the converter and the Windows server, and try once more. Report if that fails too.

**With llama.cpp in WSL** (step 1), serve it there instead of the Windows lines below, in tmux, with the GGUF the WSL server uses for Qwen:

```bash
tmux new -s hegel
llama-server -m /path/to/qwen3.8-27b.gguf --lora ~/hegel-in-delhi/pc/out/hegel-lora.gguf -ngl 99 -c 16384 --host 0.0.0.0 --port 8082 --alias hegel
```

The Pi must reach port 8082: add the Windows firewall rule below, and if WSL does not run with `networkingMode=mirrored`, forward the port (`netsh interface portproxy add v4tov4 listenport=8082 listenaddress=0.0.0.0 connectport=8082 connectaddress=<WSL address from 'wsl hostname -I'>`). Then check from Windows with `curl.exe http://127.0.0.1:8082/health` and ask the question below the same way.

On Windows:

```powershell
curl.exe -fsSL -o C:\hegel\scripts\start-hegel.ps1 https://raw.githubusercontent.com/weltogeisto/hegel-in-delhi/main/pc/start-hegel.ps1
curl.exe -fsSL -o C:\hegel\scripts\sleep-watchdog.ps1 https://raw.githubusercontent.com/weltogeisto/hegel-in-delhi/main/pc/sleep-watchdog.ps1
```

The new watchdog also counts port 8082 as activity; restart its task (`Stop-ScheduledTask "Hegel sleep watchdog"; Start-ScheduledTask "Hegel sleep watchdog"`). In `start-hegel.ps1`, set the default of `-Model` to the full path of the Qwen GGUF from step 1, then:

```powershell
Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File C:\hegel\scripts\start-hegel.ps1'
Start-Sleep 90
curl.exe http://127.0.0.1:8082/health
Select-String -Path C:\hegel\logs\hegel.err.log -Pattern "lora|adapter" | Select-Object -Last 5
New-NetFirewallRule -DisplayName "Hegel trained mind 8082" -Direction Inbound -Protocol TCP -LocalPort 8082 -Action Allow -Profile Private
```

Expected: `{"status":"ok"}` and log lines saying the LoRA adapter was loaded. Report both. Then one question:

```powershell
'{"messages":[{"role":"user","content":"What is the relation of the state to civil society? Two sentences."}],"max_tokens":150}' | Set-Content -Encoding ascii C:\hegel\logs\ask.json
curl.exe -s http://127.0.0.1:8082/v1/chat/completions -H "Content-Type: application/json" -d "@C:\hegel\logs\ask.json"
```

Send Welt the answer as it came.

## 7. Hand over to Hermes

Leave the trained mind running on 8082 and tell Welt it is ready. Hermes runs the Hegel test on it (HERMES.md, task 5b) and compares it with Bonsai and the plain Qwen; Welt and Claude judge the sheets, and Welt decides which mind goes live.

When Hermes is done:

```powershell
Remove-Item C:\hegel\awake.flag -ErrorAction SilentlyContinue
Stop-Process -Name llama-server -ErrorAction SilentlyContinue
Enable-ScheduledTask "Hegel mind" -ErrorAction SilentlyContinue | Out-Null
Start-ScheduledTask "Hegel mind" -ErrorAction SilentlyContinue
```

Bonsai is back on 8081, and the PC sleeps when idle again; put Windows' sleep timer back if step 4 changed it. Tell Welt the world on the Pi may run again. Keep `pc/out/hegel-lora/`, `C:\hegel\models\hegel-lora.gguf` and `mind/train/` until Welt says otherwise: a second round of training starts from them.
