"""Is the 8082 server still the one recorded at the start (same pid, same pinned cmdline)?  Prints SAME or CHANGED <why>."""
import hashlib, json
from pathlib import Path

srv = json.loads(Path("/home/ai/night1/SERVER.json").read_text())
p = Path(f"/proc/{srv['pid']}")
try:
    same = p.joinpath("comm").read_text().strip() == "llama-server" and hashlib.sha256(p.joinpath("cmdline").read_bytes()).hexdigest() == srv["argv_sha256"]
    print("SAME" if same else "CHANGED: pid reused by another command")
except OSError:
    print(f"CHANGED: pid {srv['pid']} is gone")
