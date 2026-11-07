"""Run the frozen shadow set and fresh isolated rehearsal through one guarded post.

The injected post is the same durable, serial spare-slot transport for decision
and support calls. It must enforce natural-step latency/deadlines, replay exact
completed keys and refuse unknown replies. There is no direct HTTP fallback.
This module never starts/stops a server, changes a timer or publishes a world day.
"""
import copy
from datetime import date, timedelta
from pathlib import Path

from tools.decision_sampler import (
    CandidateMind, CandidateWorld, DatasetComplete, REHEARSAL_SITUATIONS,
    Sampler, checked, digest, export_rows, json_bytes, save, write_new,
)
from world.engine import Days, Engine, until_of
from world.feeds import Feeds
from world.memory import Memory
from world.world import at_dt

ROSTER_SHA256 = "a7f6c59b8038d4fbf38f7e57aea6ddb6e5458f6db256ec82b1c7f872b407e264"


def sample_shadow(freeze, sampler):
    freeze = Path(freeze)
    manifest = checked(freeze / "MANIFEST.json")
    ids_raw = (freeze / "SHADOW-IDS.json").read_bytes()
    if digest(ids_raw) != ROSTER_SHA256 or manifest["roster_sha256"] != ROSTER_SHA256:
        raise ValueError("the owner-approved 109-row roster changed")
    if manifest["situations"] != 109 or len(manifest["rows"]) != 109:
        raise ValueError("expected the approved 109 shadow situations")
    ids = []
    for ref in manifest["rows"]:
        path = (freeze / ref["path"]).resolve()
        if freeze.resolve() not in path.parents or digest(path.read_bytes()) != ref["sha256"]:
            raise ValueError("shadow situation path or hash differs")
        row = checked(path)
        if row["id"] != ref["id"] or row["source"] != "shadow":
            raise ValueError("shadow identity changed")
        sampler.sample(row)
        ids.append(row["id"])
    if json_bytes(ids) != ids_raw:
        raise ValueError("shadow roster order differs")
    return ids


class PreservedDays(Days):
    """Normal rehearsal working files, with every saved version retained."""
    def __init__(self, docs):
        super().__init__(docs, shift_min=0)
        self.history = Path(docs) / "versions"

    def save(self, day):
        # Preserve both the prior working bytes and the final refreshed version.
        previous = self.path(day["date"])
        if previous.exists():
            self.preserve(previous.read_bytes())
        super().save(day)
        self.preserve(previous.read_bytes())

    def preserve(self, raw):
        dest = self.history / (digest(raw) + ".json")
        if dest.exists():
            if dest.read_bytes() != raw:
                raise ValueError("immutable rehearsal history changed")
        else:
            write_new(dest, raw)


class Auxiliary:
    """Saved support calls, excluded from the preference rows."""
    def __init__(self, world, post):
        self.world, self.post = world, post

    def __call__(self, messages, schema=None, max_tokens=700, temperature=None, **kwargs):
        if kwargs:
            raise ValueError("unsupported auxiliary options: " + ", ".join(sorted(kwargs)))
        payload = dict(model="qwen", id_slot=1, seed=1831, stream=False,
                       messages=copy.deepcopy(messages), max_tokens=max_tokens,
                       temperature=.7 if temperature is None else temperature,
                       chat_template_kwargs={"enable_thinking": False})
        if schema is not None:
            payload["response_format"] = {"type": "json_schema", "json_schema":
                                          {"name": "answer", "schema": schema}}
        # Exact support prompts in the same step replay after interruption.
        day = getattr(self.world, "current_day", None)
        location = (str(day["n"]) + "/" + str(len(day["steps"]))) if day else "before-first-step"
        key = "support/" + location + "/" + digest(json_bytes(payload))
        answer, receipt = self.post(key, payload)
        if not receipt.get("response_sha256"):
            raise ValueError("support response has no durable receipt")
        raw = answer["choices"][0]["message"].get("content")
        if not isinstance(raw, str):
            raise ValueError("support call returned no text; preserve its chain")
        return raw


def rehearse(cfg, sampler_root, post, start=date(2026, 11, 10), max_days=30,
             engine_type=Engine, world_type=CandidateWorld):
    """The --distill five-minute advance loop, confined to the provided scratch.

    cfg.docs must already contain a frozen copy of preceding published days,
    prepared with rehearsal_setup or an equivalent byte-verified local copy.
    Never pass the live docs directory. All support calls use the same guard.
    """
    repo, docs = Path(cfg.repo).resolve(), Path(cfg.docs).resolve()
    if docs == repo / "docs" or repo in docs.parents or cfg.push or cfg.feeds:
        raise ValueError("isolated rehearsal docs, no push and feeds off required")
    if start < date(2026, 11, 10) or max_days < 1:
        raise ValueError("fresh dates from 10 November required")
    if getattr(cfg, "echo_guard", False) or getattr(cfg, "decision_dry", 0):
        raise ValueError("candidate generation is plain Qwen, without a T39 arm")
    cfg.write_mode = "chat"
    world = world_type(Feeds(cfg))
    sampler = Sampler(sampler_root, world, post)
    mind = CandidateMind(sampler, world, Auxiliary(world, post))
    if len(mind.completed_ids) == REHEARSAL_SITUATIONS:
        return sorted(mind.completed_ids, key=lambda x: tuple(map(int, x.split(":")[1:])))
    engine = engine_type(cfg, world, mind, git=None)
    engine.days = PreservedDays(docs)
    engine.memory = Memory(engine.days, world)
    # No external lookups in a fixed local rehearsal. The note is explicit,
    # not an invented source; calls to the model remain fully recorded.
    engine.lookup = lambda *a, **kw: {"note": "External lookup unavailable in this isolated rehearsal."}
    try:
        for offset in range(max_days):
            d = start + timedelta(days=offset)
            day = engine.days.load(d)
            if day and day.get("complete") and day.get("owl"):
                continue
            now, end = at_dt(d, 0), at_dt(d, 1440)
            if day:
                now = max(now, until_of(day) - timedelta(minutes=cfg.lead))
            while now < end:
                engine.advance(now)
                if len(mind.completed_ids) == REHEARSAL_SITUATIONS:
                    raise DatasetComplete()
                now += timedelta(minutes=5)
            day = engine.days.load(d)
            day["complete"] = True
            engine.days.save(day)
            # Auxiliary owl output is isolated rehearsal context, never a label.
            if not day.get("owl"):
                engine.run_owl(day, at_dt(d + timedelta(days=1), 90))
    except DatasetComplete:
        pass
    if len(mind.completed_ids) != REHEARSAL_SITUATIONS:
        raise RuntimeError("fresh rehearsal stopped before 391 situations; preserve it")
    return sorted(mind.completed_ids, key=lambda x: tuple(map(int, x.split(":")[1:])))


def run_dataset(freeze, sampler_root, cfg, post, output):
    """Produce exactly 109 + 391 rows; interruption leaves all receipts reusable."""
    shadow = sample_shadow(freeze, Sampler(sampler_root, CandidateWorld(), post))
    fresh = rehearse(cfg, sampler_root, post)
    return export_rows(sampler_root, shadow + fresh, output)
