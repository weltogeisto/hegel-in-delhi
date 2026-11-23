# One live morning against its replay

Asked on PR #1 on 21 November, and answered there by Claude in the cloud. Built the same night, off. The question is whether the engine, given the same inputs and the same replies, writes the same morning offline as it did live. Reading a live day against the fast lane's forks rests on this.

## What is built (off until switched on)

- **`HEGEL_RECORD_CALLS=1`** (`world/calls.py`, `world/mind.py`, `world/engine.py`) writes `state/calls/calls-<UTC date>.jsonl`. It holds:
  - a header: the hash of `world/` and `mind/`, the switches (no paths, nothing named as a secret), and whether the owl has a mind of its own;
  - a line for each tick that does something: the `now` the engine was given, and the hash of the feed cache;
  - a line for each request to the mind, in order: its moment, its kind (decision, voice, writing, complete, chat, tokens), the full request, and the reply or the error. Retries, refused draws and the owl are included.
- **Off, nothing changes.** The engine names no moment, and the mind writes nothing. The stand-in days stay byte-identical.
- **`tools/replay_morning.py`** runs the engine on a copy of the starting days and replays the recorded morning:
  - Ticks come at the recorded times, the feeds are read offline from the cache, and the mind is answered from the record. No model is called.
  - Every request must equal the recorded one, field by field.
  - After five accepted decisions it compares the replay's steps with the live ones, field by field (the stopwatch left out).
  - It says **match**, **mismatch** (with the first difference), or **inconclusive**. Inconclusive means the recording ends early, the code or the switches differ, or the feed cache changed inside the window.
- `tests/test_calls.py` records a stand-in morning ticked each minute as the Pi ticks, replays it to a match, and finds a changed reply and a recording cut short.

## The morning: Day 55, his Wednesday 25 November

Berlin Tuesday 24 November, first step about 08:59. Day 53 is the museums' first whole day, and Day 54 is the earliest day for `HEGEL_FILE_ACT`. Day 55 changes nothing.

1. **On Welt's word only:** `HEGEL_RECORD_CALLS=1` on the Pi before the waking. Off again after the fifth accepted decision of Day 55. Nothing else changes.
2. **Kept:**
   - shadow's commit before the first recorded tick, which gives `--start` its `days/`;
   - the commit of the fifth decision, which gives `--live`;
   - the Pi's `state/feeds` and `state/lookup` as they are then;
   - the calls file.
3. **The run:** on the PC or the Pi, on main at the recorded code: `python3 tools/replay_morning.py --start <start> --calls <calls file> --live <live> --out <folder>`.
4. **What is published:** the raw records stay where they were made. PR #1 gets the coverage, the hashes and the result (`REPORT.md`).

Evaluation only. No record is ever training data.
