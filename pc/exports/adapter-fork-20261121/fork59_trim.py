"""In the branch copy only: drop each run's day files before 2026-11-21 when they are byte-identical to the saved morning."""
import hashlib
from pathlib import Path
D = Path("/mnt/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/90b4347d-b5da-4fc9-99db-4ff38302b710/scratchpad/fork59-branch/pc/exports/adapter-fork-20261121/runs")
M = Path("/home/ai/fork59/morning/days")
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for run in sorted(D.iterdir()):
    dropped, kept, differ = 0, [], []
    for p in sorted((run / "days").glob("????-??-??.json")):
        if p.stem < "2026-11-21":
            if (M / p.name).exists() and sha(M / p.name) == sha(p):
                p.unlink(); dropped += 1
            else:
                differ.append(p.name)
        else:
            kept.append(p.name)
    print(run.name, "dropped", dropped, "kept", kept, "differ", differ)
