"""Configuration from ~/.config/hegel/env (the same file the bash scripts source) and the environment."""
import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def read_env_file(path):
    values = {}
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return values
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        value = re.sub(r"\s+#.*$", "", value).strip().strip('"').strip("'")
        values[key] = value
    return values


class Config:
    def __init__(self, overrides=None):
        env_path = os.environ.get("HEGEL_ENV", str(Path.home() / ".config/hegel/env"))
        v = read_env_file(env_path)
        v.update({k: val for k, val in os.environ.items() if k.isupper()})
        v.update(overrides or {})
        self.values = v
        self.repo = Path(v.get("HEGEL_REPO", REPO)).expanduser()
        self.docs = self.repo / "docs"
        soul_file = Path(v.get("HEGEL_SOUL_FILE", "mind/soul.md")).expanduser()
        self.soul_file = soul_file if soul_file.is_absolute() else self.repo / soul_file
        self.branch = v.get("HEGEL_BRANCH", "main")
        self.push = v.get("HEGEL_PUSH", "1") not in ("0", "no", "false", "")
        self.state = Path(v.get("HEGEL_STATE", Path.home() / ".local/state/hegel")).expanduser()
        self.lead = int(v.get("LEAD_MIN", "15"))
        self.clock_shift_min = int(v.get("HEGEL_CLOCK_SHIFT_MIN", "0") or 0)    # rehearsals only: his clock runs this far ahead of Delhi
        self.feeds = v.get("HEGEL_FEEDS", "1") not in ("0", "no", "false", "")
        self.shelf = v.get("HEGEL_SHELF", "1") not in ("0", "no", "false", "")          # his books in front of him (mind/shelf)
        self.shelf_whole = v.get("HEGEL_SHELF_WHOLE", "0").strip().lower() in ("1", "yes", "true")   # whole passages, not excerpts
        self.shelf_additions = v.get("HEGEL_SHELF_ADDITIONS", "0").strip().lower() in ("1", "yes", "true")   # M2: a label names an editor's addition; off until Welt's word
        self.culture = v.get("HEGEL_CULTURE", "0").strip().lower() in ("1", "yes", "true")   # museums, concerts and plays (pc/CULTURE.md); off until switched on
        self.street = v.get("HEGEL_STREET", "0").strip().lower() in ("1", "yes", "true")   # a card from the street deck at an empty moment (pc/WORLD-2-WEEK1.md P4); off until switched on
        self.street_file = v.get("HEGEL_STREET_FILE", "").strip() or None   # another deck than world/data/street.json (a rehearsal's)
        self.correspondent = v.get("HEGEL_CORRESPONDENT", "0").strip().lower() in ("1", "yes", "true")   # Niethammer writes from Munich (pc/CORRESPONDENT.md); off until switched on
        self.voice_facts = v.get("HEGEL_VOICE_FACTS", "0").strip().lower() in ("1", "yes", "true")   # a voice is told its own side of the record, its pronoun, and the right person answers (pc/WORLD-2-WEEK1.md P2); off until switched on
        self.voice_repairs = v.get("HEGEL_VOICE_REPAIRS", "0").strip().lower() in ("1", "yes", "true")   # four repairs to the voices: no own presence line, no goods where none are sold, who answers, checked `does` lines (tests/test_voice_repairs.py); off until switched on
        self.letter_register = v.get("HEGEL_LETTER_REGISTER", "0").strip().lower() in ("1", "yes", "true")   # a letter is written as a letter of that evening, not an essay (DECISIONS 60); off until switched on
        self.world_repairs = v.get("HEGEL_WORLD_REPAIRS", "0").strip().lower() in ("1", "yes", "true")   # five repairs from the review of Days 47–49 (DECISIONS 57); off until switched on
        self.ramesh_days = v.get("HEGEL_RAMESH_DAYS", "0").strip().lower() in ("1", "yes", "true")   # Ramesh may offer to come every day again (DECISIONS 47); off until switched on
        self.file_act = v.get("HEGEL_FILE_ACT", "0").strip().lower() in ("1", "yes", "true")   # the file moves after the query: three doors and a copy (pc/FILE-NEXT-ACT.md, part 1); off until switched on
        self.keep_time = v.get("HEGEL_KEEP_TIME", "0").strip().lower() in ("1", "yes", "true")   # an appointment elsewhere ends what he is doing in time to walk there, and a missed talk at the IIC is offered once more (Day 53); off until switched on
        self.talk_scene = v.get("HEGEL_TALK_SCENE", "0").strip().lower() in ("1", "yes", "true")   # a talk at the IIC is a scene: the programme officer answers, a voice is told whether its place is open today, the lecture is given and one question comes from the hall (pc/TALK-SCENE.md); off until switched on
        self.exits = v.get("HEGEL_EXITS", "0").strip().lower() in ("1", "yes", "true")   # ways out of the money trouble: a second pupil, a course of lectures, Ramesh's early offer, Sunil's slate, Shri Hegde's plate (pc/EXITS.md); off until switched on
        self.promises = v.get("HEGEL_PROMISES", "0").strip().lower() in ("1", "yes", "true")   # a promise is a record: the voice may make one in `act`, the engine keeps it (pc/WORLD-2-WEEK1.md P1); off until switched on
        self.consumed = v.get("HEGEL_CONSUMED", "0").strip().lower() in ("1", "yes", "true")   # what he ate is an entry of its own, which the page shows and the owl reads (DECISIONS 48); off until someone has looked at what they do with it
        self.pause_away = v.get("HEGEL_PAUSE_AWAY", "0").strip().lower() in ("1", "yes", "true")   # hold his world at waking while the PC is away (pc/PAUSE.md); off until switched on
        self.wants = v.get("HEGEL_WANTS", "0").strip().lower() in ("1", "yes", "true")   # he may name what he wishes the city had (pc/WANTS-SCREEN.md); written down, no effect; off until switched on
        self.borrowed_lookup = v.get("HEGEL_BORROWED_LOOKUP", "0").strip().lower() in ("1", "yes", "true")   # with no phone of his own, someone he knows who is with him looks a thing up on theirs (pc/BORROWED-LOOKUP.md); off until switched on
        self.papers_record = v.get("HEGEL_PAPERS_RECORD", "0").strip().lower() in ("1", "yes", "true")   # the day's papers kept in full in the state folder, nothing he is told changes (pc/PAPERS.md); off until switched on
        self.papers = v.get("HEGEL_PAPERS", "0").strip().lower() in ("1", "yes", "true")   # `read` at home gives him the next piece of the day's papers, and what he read is remembered (pc/PAPERS.md); off until switched on
        self.papers_archive = v.get("HEGEL_PAPERS_ARCHIVE", "").strip() or None   # a rehearsal's papers: a folder of papers-*.json, cycled by day (pc/PAPERS.md)
        self.news_feeds = [u.strip() for u in v.get("NEWS_FEEDS", (
            "https://www.thehindu.com/news/national/feeder/default.rss,"
            "https://indianexpress.com/section/india/feed/")).split(",") if u.strip()]
        host, port = v.get("PC_HOST"), v.get("MIND_PORT", "8081")
        self.mind_url = v.get("MIND_URL") or (f"http://{host}:{port}" if host else None)
        self.owl_url = v.get("OWL_URL") or (f"http://{host}:{v.get('OWL_PORT', port)}" if host else self.mind_url)
        self.wake = str(self.repo / "scripts/wake_pc.sh") if v.get("PC_MAC") else None
        self.owl_at = v.get("OWL_AT", "09:10")         # the morning after, as he wakes: the PC is up from nine
        self.depesche_day = v.get("DEPESCHE_DAY", "Saturday")
        self.timeout = int(v.get("MIND_TIMEOUT", "300"))
        voice_scale = v.get("HEGEL_VOICE_ADAPTER_SCALE", "").strip()
        if voice_scale not in ("", "0", "1"):
            raise ValueError("HEGEL_VOICE_ADAPTER_SCALE must be empty, 0 or 1")
        self.voice_adapter_scale = int(voice_scale) if voice_scale else None
        self.writing_reasoning_tokens = int(v.get("HEGEL_WRITE_REASONING_TOKENS", "0"))
        if not 0 <= self.writing_reasoning_tokens <= 2048:
            raise ValueError("HEGEL_WRITE_REASONING_TOKENS must be from 0 to 2048")
        writing_scale = v.get("HEGEL_WRITE_ADAPTER_SCALE", "").strip()
        if writing_scale not in ("", "0", "1"):
            raise ValueError("HEGEL_WRITE_ADAPTER_SCALE must be empty, 0 or 1")
        self.writing_adapter_scale = int(writing_scale) if writing_scale else None
        self.decision_reasoning_tokens = int(v.get("HEGEL_DECISION_REASONING_TOKENS", "0"))
        if not 0 <= self.decision_reasoning_tokens <= 2048:
            raise ValueError("HEGEL_DECISION_REASONING_TOKENS must be from 0 to 2048")
        decision_scale = v.get("HEGEL_DECISION_ADAPTER_SCALE", "").strip()
        if decision_scale not in ("", "0", "1"):
            raise ValueError("HEGEL_DECISION_ADAPTER_SCALE must be empty, 0 or 1")
        self.decision_adapter_scale = int(decision_scale) if decision_scale else None
        self.owl_reasoning_tokens = int(v.get("HEGEL_OWL_REASONING_TOKENS", "0"))
        if not 0 <= self.owl_reasoning_tokens <= 2048:
            raise ValueError("HEGEL_OWL_REASONING_TOKENS must be from 0 to 2048")
        self.thesis_reminders = v.get("HEGEL_THESIS_REMINDERS", "1") not in ("0", "no", "false", "")
        self.echo_guard = v.get("HEGEL_ECHO_GUARD", "0").strip().lower() in ("1", "yes", "true")       # T36 arm B; off until it passes the ratchet
        self.decision_dry = float(v.get("HEGEL_DECISION_DRY", "0") or 0)                                # T36 arm C: the DRY sampler's multiplier, 0 off
        if not 0 <= self.decision_dry <= 2:
            raise ValueError("HEGEL_DECISION_DRY must be from 0 to 2")
        self.notebook = v.get("HEGEL_NOTEBOOK", "0").strip().lower() in ("1", "yes", "true")   # the owl keeps his notebook of the age, in his prompt each day (pc/NOTEBOOK.md); off until switched on
        self.keep_draws = v.get("HEGEL_KEEP_DRAWS", "0").strip().lower() in ("1", "yes", "true")   # the filter's draws kept in the state folder as preference data (pc/FILTER-PAIRS.md); off until switched on
        self.decision_draws = int(v.get("HEGEL_DECISION_DRAWS", "1") or 1)                              # T49: replies to choose among, 1 off
        if not 1 <= self.decision_draws <= 6:
            raise ValueError("HEGEL_DECISION_DRAWS must be from 1 to 6")
        self.seed = int(v["HEGEL_SEED"]) if v.get("HEGEL_SEED", "").strip() else None                    # a base seed: every call to the mind sends one derived from it (world/mind.py); unset, none is sent
        self.record_calls = v.get("HEGEL_RECORD_CALLS", "0").strip().lower() in ("1", "yes", "true")   # every request to the mind and its reply written down in order (world/calls.py); off until switched on
        self.seed_streams = v.get("HEGEL_SEED_STREAMS", "0").strip().lower() in ("1", "yes", "true")    # seeds by (moment, kind, draw), not by running call number (pc/FAST-LANE.md, C); off until switched on
        cache = v.get("HEGEL_CACHE_PROMPT", "").strip().lower()                                          # the server's prompt cache, per request: unset leaves the field out; 0 sends false, 1 true (a same-seed rehearsal needs false)
        if cache not in ("", "0", "no", "false", "1", "yes", "true"):
            raise ValueError("HEGEL_CACHE_PROMPT must be empty, 0/no/false or 1/yes/true")
        self.cache_prompt = None if not cache else cache in ("1", "yes", "true")
        self.write_mode = "plain" if v.get("HEGEL_WRITE_MODE", "chat").strip().lower() == "plain" else "chat"      # his writings: the chat call (default), or a plain-text completion
        self.outcome_memory = v.get('HEGEL_OUTCOME_MEMORY','0') not in ('0','no','false','')
        self.evidence_view = 'compact' if v.get('HEGEL_EVIDENCE_VIEW', 'full').strip().lower() == 'compact' else 'full'      # how the writers see the records: grouped and short, or every record with its id
        # Explicit opt-in until the isolated results have been reviewed. Missing
        # calibration must fail rather than invent a temperature at runtime.
        self.claim_check = v.get('HEGEL_CLAIM_CHECK','0') not in ('0','no','false','')
        if self.claim_check and not self.outcome_memory:
            raise ValueError('HEGEL_CLAIM_CHECK requires HEGEL_OUTCOME_MEMORY')
        self.claim_calibration = Path(v.get('HEGEL_CLAIM_CALIBRATION',self.repo/'pc/claim-calibration.json')).expanduser()

    def get(self, key, default=None):
        return self.values.get(key, default)
