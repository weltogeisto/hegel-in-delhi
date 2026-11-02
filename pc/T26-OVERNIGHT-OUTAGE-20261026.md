# T26: the overnight mind outage

**Cause: the existing PC Power Guard shut Windows down at its 12-hour safety limit.** User32 event1074 names that guard in the shutdown comment. The saved Windows events record an actual shutdown followed by the next morning's OS boot. Power settings remain unchanged.

| Event | UTC |
|---|---|
| Power Guard requests shutdown, with its existing60-second cancellation window |25Oct21:16:49.0825921|
| Windows shuts down (Kernel-General13) |25Oct21:17:57.1699021|
| Windows boots (Kernel-General12/LastBoot) |26Oct07:18:13.5000000|
| Saved Windows startup launcher begins |26Oct07:18:55.6102265|
| Linux launcher starts the exact saved plain-Qwen/CUDA command once |26Oct07:18:59.159833|
| Launcher records GPU_READY, PID501, exit0 |26Oct07:20:37.967237|
| Later launcher reuses PID501, zero launches, exit0 |26Oct07:34:47|

The current fetched shadow source c3be47f contains30decisions, including20away/null steps. The first away step starts08:03 world time; the last starts17:33 and ends18:03. Every away step records the unavailable8082health endpoint. The Pi continued its fallback while Windows was off; natural mind steps resumed after the recorded startup. The earlier sealed07:36snapshot had27decisions, including the same20away steps. Both snapshots remain original partial days, with no repetition or quality score.

The enabled task is **Hegel Qwen 8082 GPU**, whose action runs the saved startup launcher. The receipts prove automatic recovery after an actual OS boot. TaskScheduler Operational returned no matching events, so the exact BootTrigger versus LogonTrigger attribution remains unproved.

This analysis reuses the original Windows and launcher receipts already captured this morning. Six exact source files and their hashes accompany this report under mind/results/t26-outage-20261026/. The original event and startup readings, including the earlier incorrect task-name lookup, remain outside Git in C:/hegel/handover/codex-tasks-20261026/outcome-status-20261026-073600.

No new Windows query, Pi SSH, model/health request, timer/server/power/config/clock/state change, reboot, forced tick/owl or test was needed. Readiness checks within the copied receipts were the saved launcher's ordinary behavior. The independent Power Guard and awake.flag remain unchanged.
