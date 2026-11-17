# Qwen on 8082 after reboot — proposal only

The running server is WSL Ubuntu-24.04, Linux user ai, tmux `hegel-server`.
It uses the already installed b11429 CUDA binary and the existing Qwen3.8
GGUF, no adapter, 49,152 total context / three slots, host 0.0.0.0, port8082.
The exact launcher is preserved at
`C:\hegel\handover\codex-tasks-20261012\serve-qwen.sh`.

Do not apply the old `pc/CODEX.md` startup recipe unchanged: it starts the
Windows Bonsai model on 8081 as SYSTEM, alongside which Qwen will not fit.
No startup task has been altered by this work.

Proposed administrator change, for Welt's authorization and review:

1. Export/back up the existing “Hegel mind” task and inspect its action and
   account. Disable its Bonsai launch only when the Qwen replacement is
   ready; preserve the task/export so rollback is possible.
2. Register a startup task in the Windows account that owns Ubuntu-24.04.
   Its action invokes `wsl.exe -d Ubuntu-24.04 -u ai -- bash` with a persistent,
   idempotent Qwen launcher. Do not assume the old SYSTEM principal can
   access this user's registered WSL distribution. Select a no-login logon
   method in Task Scheduler with Welt; no password or secret is collected
   or stored by Codex. This account/logon behavior needs an actual boot test.
3. The launcher starts Qwen only when no server already owns 8082, verifies
   that any existing server is this model with an empty adapter inventory,
   writes startup errors to a stable Windows log, and leaves the process
   attached to the task or tmux. Allow restart on failure, with bounded
   retries. Reserve the same three slots for world and tests.
4. In mirrored networking, use the reviewed `pc/open-hegel-port.ps1` for the
   Windows and Hyper-V rules. Welt runs it; Codex does not change firewall
   or power settings. No NAT portproxy is needed in the observed mode.
5. With no GPU jobs pending, reboot once, do not log in, and have the Pi
   poll `http://192.168.188.21:8082/health` and `/lora-adapters` (must be `[]`).
   Record time-to-ready and verify exactly one Qwen server and no Bonsai.
   Only that test can establish the no-login reboot requirement.

Current blockers: administrator firewall access, task/account setup and the
no-login boot test. Windows loopback is healthy; LAN health timed out. There
is no safe claim that a tmux session alone satisfies boot persistence.
