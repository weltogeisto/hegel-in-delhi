# T21: Windows startup and Update verification, 25 October 2026

T21 DONE. Welt ran the prepared Administrator installer at11:08UTC. The original receipt ends STARTUP_AND_UPDATE_POLICY_VERIFIED at11:10:03UTC. An independent read-back at11:23:18UTC verifies the installed task and all14 planned DWORDs. No installer, server test or model request was repeated during verification.

The task **Hegel Qwen 8082 GPU** is enabled and Ready, with LastTaskResult0. It uses current-user S4U, hidden PowerShell, boot delay30s, logon delay15s, IgnoreNew, AllowHardTerminate=false and WakeToRun=false. Its action is the existing C:/hegel/scripts/Start-HegelQwen8082.ps1 wrapper. The installer's scheduled-task test exited0.

The original fresh-shell test held Pi tick.lock, observed an inactive service, stopped idlePID388 gracefully and launched the exact saved command once as PID4130 / hegel-server-auto-20261025-110831-345957. It finished0 and released the guard0. Current process argv plus trailing NUL still hashes1944b782a1c3557851d1c3639e04e43072e6c2a6e8eff6e96978f96d6e48d6b0; cwd, model,8082, three16384slots and the process-only CUDA path are unchanged. The saved launcher receipt reports GPU_READY/CUDA mapped. This reads existing evidence; no new health or speed call was made.

**A real reboot has not yet been observed.** The next natural reboot supplies the boot-trigger proof; fresh-shell cold start is verified separately. C:/hegel/awake.flag remains present.

| Registry location / value | Expected | Read back | Type |
|---|---:|---:|---|
| `Policies\Microsoft\Windows\WindowsUpdate\AU: NoAutoUpdate` | 0 | 0 | DWORD |
| `Policies\Microsoft\Windows\WindowsUpdate\AU: AUOptions` | 3 | 3 | DWORD |
| `Policies\Microsoft\Windows\WindowsUpdate\AU: AlwaysAutoRebootAtScheduledTime` | 0 | 0 | DWORD |
| `Policies\Microsoft\Windows\WindowsUpdate: SetActiveHours` | 1 | 1 | DWORD |
| `Policies\Microsoft\Windows\WindowsUpdate: ActiveHoursStart` | 18 | 18 | DWORD |
| `Policies\Microsoft\Windows\WindowsUpdate: ActiveHoursEnd` | 12 | 12 | DWORD |
| `Policies\Microsoft\Windows\WindowsUpdate: SetComplianceDeadlineForQU` | 0 | 0 | DWORD |
| `Policies\Microsoft\Windows\WindowsUpdate: SetComplianceDeadlineForFU` | 0 | 0 | DWORD |
| `Policies\Microsoft\Windows\WindowsUpdate: SetComplianceDeadline` | 0 | 0 | DWORD |
| `Microsoft\WindowsUpdate\UX\Settings: SmartActiveHoursState` | 0 | 0 | DWORD |
| `Microsoft\WindowsUpdate\UX\Settings: ActiveHoursStart` | 18 | 18 | DWORD |
| `Microsoft\WindowsUpdate\UX\Settings: ActiveHoursEnd` | 12 | 12 | DWORD |
| `Microsoft\WindowsUpdate\UX\Settings: IsExpedited` | 0 | 0 | DWORD |
| `Microsoft\WindowsUpdate\UX\Settings: RestartNotificationsAllowed2` | 1 | 1 | DWORD |

Applied values configure automatic download with notification before installation, active hours18:00-12:00local, disabled deadline enables, adaptive hours and expedited restart, and enabled restart notifications. These are registry read-backs, not a guarantee about every future Windows restart. The original computer-policy refresh exited0; the prior-value backup is preserved in the installer receipt.

Two later attempts at11:11:35 and11:13:16 refused with Task already exists; inspect before modifying before changing anything. Both original failure receipts remain; the successful installation was not undone or rerun here.

T16's natural mind proof preceded this separately authorized installer cold-start test. All original speed, natural and gap records remain. The14October elevation cancellation is historical; installation and read-back are now verified.

Exact receipt hashes: pc/T21-WINDOWS-VERIFICATION-20261025.json. Original receipts and independent read-back: mind/results/t21-windows-verification-20261025/. No deliberate reboot, power override, package/model/adapter or global environment change.
