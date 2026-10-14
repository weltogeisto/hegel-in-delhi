# Welt's 14 October handover: verified results and remaining Windows block

## 1. GPU restored — DONE

After Welt's explicit scoped exception, the idle CPU-only PID390 was gracefully stopped between ticks while holding the Pi's existing tick lock. The same saved command, cwd, model, port8082 and three 16384-token slots started once in tmux `hegel-server-cuda-20261014-162609`, PID6683. Only this process received the existing paired CUDA library directory:

`/home/ai/local-ai/llama/release-b11429/cudart-llama-b11429-bin-ubuntu-cuda-12.8-x64`

Saved argv plus trailing NUL SHA256 remains `1944b782a1c3557851d1c3639e04e43072e6c2a6e8eff6e96978f96d6e48d6b0`. The CUDA backend is mapped, the RTX3090 reports about19282MiB in use, and health returns200/OK. One authorized slot1 test produced110 tokens in3.259022625s: **33.75 tokens/s** including prompt time; server generation timing was39.08tokens/s, versus about1.95 on the CPU-only session. The test response and original logs remain sealed outside Git. No adapter, model, package or global environment change.

## 2. Reboot startup — BLOCKED at Windows elevation

`C:\hegel\awake.flag` is present. A fresh PowerShell shell successfully invoked the prepared duplicate-safe launcher, which reused the running GPU server with **zero additional launches**. That verifies idempotence, not a cold start or reboot startup.

The one Windows UAC launch of `C:\hegel\handover\codex-tasks-20261014\Install-HegelStartup-And-UpdatePolicy.ps1` was reported cancelled: `Der Vorgang wurde durch den Benutzer abgebrochen.` No elevated installer receipt or scheduled task was created. The outer shell's exit0 is not installation success. The prompt was not reopened automatically.

The installer is prepared to register the current-user S4U task **Hegel Qwen 8082 GPU**, with boot delay30s, logon delay15s, no stored password, hidden execution, no wake, and duplicate prevention. It then tests the task and a fresh-shell cold start under the existing Pi tick lock. The stable launcher is `/home/ai/.local/bin/hegel-qwen-8082-start.py`; the Windows entry point is `C:\hegel\scripts\Start-HegelQwen8082.ps1`. Administrator execution of the prepared installer is still needed. No deliberate Windows reboot occurred.

## 3. Windows Update — BLOCKED; no policy applied

**Nothing was set in Windows Update.** The same cancelled elevation prevented this phase. The following are the exact prepared values, not applied settings:

| Registry location / DWORD | Planned value |
|---|---:|
| Policies/Microsoft/Windows/WindowsUpdate/AU: NoAutoUpdate | 0 |
| AU: AUOptions | 3 |
| AU: AlwaysAutoRebootAtScheduledTime | 0 |
| Policies/Microsoft/Windows/WindowsUpdate: SetActiveHours | 1 |
| WindowsUpdate: ActiveHoursStart / ActiveHoursEnd | 18 / 12 |
| WindowsUpdate: SetComplianceDeadlineForQU / SetComplianceDeadlineForFU / SetComplianceDeadline | 0 / 0 / 0 |
| Microsoft/WindowsUpdate/UX/Settings: SmartActiveHoursState | 0 |
| UX/Settings: ActiveHoursStart / ActiveHoursEnd | 18 / 12 |
| UX/Settings: IsExpedited | 0 |
| UX/Settings: RestartNotificationsAllowed2 | 1 |

These intend auto-download with notification before installation, protected18:00–12:00 local hours, disabled deadline-enforcement enables, adaptive hours and expedited restart, and restart notifications. The installer backs up prior values before applying anything and reads them back after a computer-policy refresh. No night-restart protection is claimed before successful application. The policy design was checked against this host's Windows Update ADMX and [Microsoft's restart guidance](https://learn.microsoft.com/en-us/windows/deployment/update/waas-restart).

No unrelated power, wake, startup-task, firewall or secret change was made. Historical power-control installers and private token/key files were not used.

## 4. T13 — DONE

Shadow `39148ae` genuinely merges mainf82 and containsc61daf3. The first natural tick finished16:56:05UTC, with later16:58:05 exit0 captured; all day/state JSON and22original CSV byte sequences remained unchanged. The old Pi page is preserved and the three new fan files are absent. Day14 is still asleep with zero decisions, so no live quiet stretch came up. See `pc/T13-SHADOW-MAIN-20261014.md/json` and the original four-test run under `mind/results/t13-main-integration-20261014`.

## 5. Day13 owl — DONE, naturally before the GPU work

The existing hourly retry started16:01:04UTC and wrote Day13's owl at **16:05:17UTC**, service completed16:05:20, commit `14c7e9ea416c937295a06c0ade133ba396428fed`. This happened before GPU restoration and was not caused or forced by Codex. The earlier15:00–15:05 timeout remains preserved in `pc/DAY13-OWL-TIMEOUT-20261014.md/json`.

Post-owl Day13 SHA256 is `93759aa56be96a46a89b31380cdfab6a1b4e7161fcf16e45dd8c563244cda104`. All original steps and entries equal the frozen pre-owl record:35decisions, four non-null thoughts and31away/null decisions. The original44243-byte T10 input retains SHA256 `39f649efc628a9169a2e26fdecd12a7320777320a3eee972b267a99c1cb911cd`. Claude can now review both the completed day and owl under T11; no owl quality score is assigned here.

## 6. T10 — OPEN

Wait for the first actual complete day with at least30non-null thoughts, expected Day14 but not guaranteed. Auditor SHA256 remains `bb77f3afc99ea2459e111e78bb8ac8f23adef68a74c79795d615c1ba5ba0439a`. Day13 remains **not measurable** and was not rerun; no share, top ten or55% decision was computed. The completed T9 regression remains unchanged and was not repeated. Public world remains paused, shift300; standing watch stays active.

Machine-readable evidence and exact sealed receipt hashes: `pc/WELT-HANDOVER-20261014.json`.
