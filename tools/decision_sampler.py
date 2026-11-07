#!/usr/bin/env python3
"""Training 3 candidate recording, independent of the live world's state.

There is deliberately no network default. A runtime owns admission, deadlines and
the durable request/response chain; pass its guarded post(request_id, payload).
This module never wakes, pauses or starts a server. Four seeds are the study,
not retries. A failed/uncertain transport stops the caller, preserving its files.
"""
import copy
import hashlib
import json
import os
from datetime import date, datetime
from pathlib import Path

from world import contract
from world.mind import HTTPMind
from tools.decision_pairs import check_row
from tools.train_data import RecordingWorld

SEEDS = (1831, 2718, 3141, 4271)
REHEARSAL_SITUATIONS = 391


class DatasetComplete(Exception):
    """The frozen fresh-rehearsal count is filled; stop before another decision call."""

LIVE_TEMPERATURE = 0.7
FIRST_REHEARSAL_DATE = date(2026, 11, 10)
TEST_DAYS = frozenset((12, 27))


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write_new(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def checked(path):
    path = Path(path)
    raw = path.read_bytes()
    expected = path.with_suffix(path.suffix + ".sha256").read_text().strip()
    if digest(raw) != expected:
        raise ValueError("record changed: " + str(path))
    return json.loads(raw)


def save(path, row):
    raw = json_bytes(row)
    write_new(path, raw)
    write_new(Path(path).with_suffix(Path(path).suffix + ".sha256"), (digest(raw) + "\n").encode())


def frozen_context(situation, context, state):
    """Copy before each checker call; World.check may normalize its input."""
    # Only the fields consumed by World.check, not transient engine helpers.
    context = {key: copy.deepcopy(context[key]) for key in
               ("t", "present", "public", "recent", "known_text") if key in context}
    context["t"] = context["t"].isoformat()
    return dict(situation=copy.deepcopy(situation), context=context, state=copy.deepcopy(state))


def restored_context(row):
    result = copy.deepcopy(row)
    result["context"]["t"] = datetime.fromisoformat(result["context"]["t"])
    return result["situation"], result["context"], result["state"]


def context_id(source, day, step):
    if source not in ("shadow", "rehearsal"):
        raise ValueError("unknown situation source")
    if type(day) is not int or type(step) is not int or day < 1 or step < 0:
        raise ValueError("day and step must be nonnegative integers (day >= 1)")
    if source == "shadow" and day in TEST_DAYS:
        raise ValueError("T39 test days cannot train")
    return f"{source}:{day}:{step}"


def situation_record(source, day, step, when, messages, earlier, sit, ctx, state, provenance):
    ident = context_id(source, day, step)
    when = date.fromisoformat(when)
    if source == "rehearsal" and when < FIRST_REHEARSAL_DATE:
        raise ValueError("new rehearsals must start on or after 10 November; no T9 data")
    if len(messages) != 2 or [m.get("role") for m in messages] != ["system", "user"]:
        raise ValueError("one original decision prompt is required; no refusal history")
    if any(not isinstance(m.get("content"), str) or not m["content"] for m in messages):
        raise ValueError("empty prompt")
    if any(not isinstance(thought, str) for thought in earlier):
        raise ValueError("earlier_thoughts must be recorded text")
    if sit["id"][:10] != when.isoformat() or ctx["t"].date() != when:
        raise ValueError("situation date mismatch")
    return dict(id=ident, source=source, day=day, step=step, date=when.isoformat(),
                messages=copy.deepcopy(messages), earlier_thoughts=list(earlier),
                check=frozen_context(sit, ctx, state), provenance=copy.deepcopy(provenance))


def decision_schema(sit):
    """Match the frozen runtime: main SCHEMA or the PC situation-aware schema."""
    factory = getattr(contract, "decision_schema", None)
    return copy.deepcopy(factory(sit) if factory else contract.SCHEMA)


def decision_payload(messages, sit, seed):
    if seed not in SEEDS:
        raise ValueError("unregistered candidate seed")
    return dict(model="qwen", id_slot=1, seed=seed, stream=False,
                messages=copy.deepcopy(messages), max_tokens=700,
                temperature=LIVE_TEMPERATURE,
                chat_template_kwargs={"enable_thinking": False},
                response_format={"type": "json_schema", "json_schema": {
                    "name": "answer", "schema": decision_schema(sit)}})


class Sampler:
    def __init__(self, root, world, post):
        self.root = Path(root)
        self.world = world
        self.post = post

    def sample(self, situation):
        ident = context_id(situation["source"], situation["day"], situation["step"])
        if ident != situation["id"]:
            raise ValueError("situation identity mismatch")
        if situation["source"] == "rehearsal" and date.fromisoformat(situation["date"]) < FIRST_REHEARSAL_DATE:
            raise ValueError("old rehearsal or T9 data")
        # Hash-named paths avoid caller-controlled path traversal.
        folder = self.root / digest(ident.encode())
        frozen = json_bytes(situation)
        path = folder / "SITUATION.json"
        if path.exists():
            if path.read_bytes() != frozen or checked(path) != situation:
                raise ValueError("saved situation differs; do not reinterpret a reply")
        else:
            if folder.exists():
                raise ValueError("partial situation evidence; preserve and reconcile")
            save(path, situation)
        output = folder / "ROW.json"
        candidates = []
        for seed in SEEDS:
            dest = folder / f"candidate-{seed}.json"
            sit, ctx, state = restored_context(situation["check"])
            payload = decision_payload(situation["messages"], sit, seed)
            if dest.exists():
                candidate = checked(dest)
                if candidate["seed"] != seed or candidate["payload_sha256"] != digest(json_bytes(payload)):
                    raise ValueError("candidate identity or prompt changed")
            else:
                # The transport MUST replay a completed response by exact key and
                # refuse any begun request with no known terminal result.
                answer, receipt = self.post(f"decision/{ident}/{seed}", payload)
                if not isinstance(receipt, dict) or not receipt.get("response_sha256"):
                    raise ValueError("durable response receipt required")
                choice = answer["choices"][0]
                raw = choice["message"].get("content")
                if not isinstance(raw, str):
                    raise ValueError("response has no text; preserve its chain")
                parsed = contract.extract_json(raw)
                errors, warnings, _ = self.world.check(parsed, sit, ctx, state)
                candidate = dict(seed=seed, raw=raw, answer=parsed, accepted=not errors,
                                 errors=errors, warnings=warnings, receipt=receipt,
                                 finish_reason=choice.get("finish_reason"),
                                 payload_sha256=digest(json_bytes(payload)))
                save(dest, candidate)
            candidates.append(candidate)
        row = {key: copy.deepcopy(situation[key])
               for key in ("id", "source", "day", "step", "date", "messages", "earlier_thoughts")}
        row.update(candidates=candidates, decision_schema=decision_schema(sit), situation_sha256=digest(frozen))
        check_row(row, set())
        if output.exists():
            if checked(output) != row:
                raise ValueError("completed row differs")
        else:
            save(output, row)
        return row


class CandidateWorld(RecordingWorld):
    """Use the same situation machinery as train_data --distill."""
    def situation(self, t, state, day, prev_step=None):
        self.current_day = day
        return super().situation(t, state, day, prev_step)


class CandidateMind:
    """Engine adapter: four decisions once, plus separately recorded support calls.

    The first accepted seed advances a new rehearsal. No preference score or model
    critic picks the trajectory. If all four are refused, returning the same first
    reply to Engine's refusal loop adds no candidates and no requests.
    """
    source = "mind"
    ready = True

    def __init__(self, sampler, world, auxiliary, limit=REHEARSAL_SITUATIONS):
        if type(limit) is not int or limit < 1:
            raise ValueError("positive rehearsal count required")
        self.sampler, self.world, self.auxiliary = sampler, world, auxiliary
        self.decisions = {}
        self.limit = limit
        self.completed_ids = {checked(p)["id"] for p in sampler.root.glob("*/ROW.json")
                              if checked(p)["source"] == "rehearsal"}
        if len(self.completed_ids) > limit:
            raise ValueError("existing rehearsal exceeds the frozen roster")

    def decide(self, messages, sit):
        day = self.world.current_day
        actual_sit, ctx, state = self.world.current
        if actual_sit is not sit:
            raise ValueError("decision no longer matches the world's current situation")
        earlier = [s["decision"]["thought"] for s in day["steps"]
                   if s.get("decision") and s["decision"].get("thought")]
        ident = context_id("rehearsal", day["n"], len(day["steps"]))
        prompt_digest = digest(json_bytes(dict(messages=messages[:2], earlier=earlier)))
        if ident in self.decisions:
            old_digest, raw = self.decisions[ident]
            if old_digest != prompt_digest:
                raise ValueError("rehearsal retry changed its original prompt/history")
            return raw
        if ident not in self.completed_ids and len(self.completed_ids) >= self.limit:
            raise DatasetComplete("391 fresh situations filled; no further call")
        row = situation_record(
            "rehearsal", day["n"], len(day["steps"]), day["date"],
            messages[:2], earlier, sit, ctx, state,
            dict(kind="new train_data rehearsal", prefix_sha256=digest(json_bytes(day))))
        recorded = self.sampler.sample(row)
        chosen = next((c for c in recorded["candidates"] if c["accepted"]),
                      recorded["candidates"][0])
        self.decisions[ident] = (prompt_digest, chosen["raw"])
        self.completed_ids.add(ident)
        return chosen["raw"]

    def chat(self, messages, schema=None, max_tokens=700, temperature=None, **kwargs):
        # The runtime records plans, voices, writings and owl calls separately;
        # none of these support calls becomes a preference-training example.
        return self.auxiliary(messages, schema=schema, max_tokens=max_tokens,
                              temperature=temperature, **kwargs)


def export_rows(root, ordered_ids, output):
    """Export only a complete frozen roster, never truncate/repair an old JSONL."""
    root, output = Path(root), Path(output)
    if len(ordered_ids) != len(set(ordered_ids)):
        raise ValueError("duplicate roster identity")
    existing = sorted(root.glob("*/ROW.json"))
    expected = [root / digest(ident.encode()) / "ROW.json" for ident in ordered_ids]
    if set(existing) != set(expected):
        raise ValueError("roster is incomplete or has extra rows")
    rows = [checked(p) for p in expected]
    for ident, row in zip(ordered_ids, rows):
        if row["id"] != ident or tuple(c["seed"] for c in row["candidates"]) != SEEDS:
            raise ValueError("record membership differs")
        folder = root / digest(ident.encode())
        situation = checked(folder / "SITUATION.json")
        if row["situation_sha256"] != digest(json_bytes(situation)):
            raise ValueError("situation digest differs")
        for candidate in row["candidates"]:
            if checked(folder / f"candidate-{candidate['seed']}.json") != candidate:
                raise ValueError("row candidate differs from its durable record")
    body = b"".join(json_bytes(row) for row in rows)
    write_new(output, body)
    summary = dict(situations=len(rows), candidates=4 * len(rows),
                   sha256=digest(body), seeds=list(SEEDS), test_days_excluded=sorted(TEST_DAYS))
    save(output.with_suffix(".manifest.json"), summary)
    return summary
