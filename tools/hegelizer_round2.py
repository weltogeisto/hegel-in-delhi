"""Round-two corpus and recipe4. Original pilot filenames are never opened for writing."""
import argparse
from collections import Counter, defaultdict, deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from threading import Event
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import hegelizer as hg
from tools.recorded_llama import RecordedClient, LatencyGuard, TransportError, freeze_plan, json_bytes, write_new

UNITS = "hegelizer2-units.jsonl"
DONE = "hegelizer2.jsonl"
FAILED = "hegelizer2-failed.jsonl"
RECIPE = 4
TEMPERATURES = (0.3, 0.7)


def strict_rows(path):
    path = Path(path)
    if not path.exists():
        return []
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        raise ValueError(str(path) + ": incomplete final line; preserve and reconcile it")
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(str(path) + ": every line must be an object")
    return rows


def unigram_overlap(original, plain):
    """Multiset unigram F1, as STRAP's SQuAD-based lexical filter; repeated words count once per occurrence."""
    a, b = Counter(hg.folded_words(original)), Counter(hg.folded_words(plain))
    shared = sum((a & b).values())
    return 2 * shared / max(1, sum(a.values()) + sum(b.values()))


def kendall_tau(original, plain):
    """Correlation of shared-word occurrence order: +1 unchanged, -1 reversed.

    Repeated occurrences match to the earliest unused source occurrence. This fixes
    ties deterministically and prevents one occurrence from matching several words.
    Fewer than two shared occurrences supplies no evidence of retained order (0).
    """
    positions = defaultdict(deque)
    for i, word in enumerate(hg.folded_words(original)):
        positions[word].append(i)
    order = []
    for word in hg.folded_words(plain):
        if positions[word]:
            order.append(positions[word].popleft())
    pairs = len(order) * (len(order) - 1) // 2
    if not pairs:
        return 0.0
    inversions = sum(order[i] > order[j] for i in range(len(order)) for j in range(i + 1, len(order)))
    return 1 - 2 * inversions / pairs


def diversity(original, plain):
    overlap, tau = unigram_overlap(original, plain), kendall_tau(original, plain)
    problems = []
    if overlap > 0.60:
        problems.append("word overlap above 0.60")
    # tau is recorded, not filtered: across a whole passage the kept order of the argument holds it high (round one's 206 pairs: median 0.61,
    # only 24 at or below 0.50), so a cap would reject faithful versions. STRAP measured single sentences. Claude, reviewing T30.
    return {"unigram_f1": overlap, "kendall_tau": tau, "problems": problems}


def short_pieces(text):
    """Consecutive authentic 1–3 sentence spans, 40–120 words; never cut or rewrite a sentence."""
    sentences = hg.shelf.sentences(text)
    out, i = [], 0
    while i < len(sentences):
        choices = []
        for count in range(1, min(3, len(sentences) - i) + 1):
            piece = " ".join(sentences[i:i + count])
            if 40 <= hg.words_of(piece) <= 120:
                choices.append((count, piece))
        if choices:
            count, piece = choices[-1]
            out.append(piece)
            i += count
        else:
            i += 1
    return out


def build_units(books, seed=hg.SPLIT_SEED, questions=hg.BLIND):
    full, report = hg.build_units(books, seed, questions)
    selected = {u["id"] for u in sorted(full, key=lambda u: hashlib.sha256((str(seed) + "|" + u["id"]).encode()).digest())[:len(full) // 3]}
    units, short_sources = [], 0
    for u in full:
        parent = dict(u, parent_id=u["id"], kind="full", recipe=RECIPE)
        units.append(parent)
        if u["id"] in selected:
            pieces = short_pieces(u["original"])
            short_sources += bool(pieces)
            for i, piece in enumerate(pieces):
                units.append(dict(parent, id=u["id"] + "/short" + str(i + 1), original=piece, kind="short"))
    return units, {"works": report, "full_units": len(full), "short_source_units": short_sources,
                   "selected_short_source_units": len(selected), "short_units": len(units) - len(full),
                   "split_rule": "short pieces inherit their full parent's split"}


def request_seed(unit_id, variant, attempt, seed=hg.SPLIT_SEED):
    # Parity separates variants; +2 separates their canonical retries.
    base = int.from_bytes(hashlib.sha256((str(seed) + "|" + unit_id).encode()).digest()[:4], "big") % 1_000_000_000
    return (2 * base + variant + 2 * attempt) % 2_147_483_647


def paraphrase_unit(unit, client, seed=hg.SPLIT_SEED):
    """Two versions, each with at most three canonical asks; all attempts remain in the recorded transport."""
    original, versions = unit["original"], []
    for variant, temperature in enumerate(TEMPERATURES):
        messages = [{"role": "system", "content": hg.PARAPHRASE_SYSTEM},
                    {"role": "user", "content": hg.PARAPHRASE_ASK.format(original=original)
                     + "\nRecast the syntax and shared-word order as well; keep every claim and technical term."}]
        attempts, accepted = [], None
        for attempt in range(hg.ASKS):
            request_id = "paraphrase/" + unit["id"] + "/v" + str(variant + 1) + "/ask" + str(attempt + 1)
            used_seed = request_seed(unit["id"], variant, attempt, seed)
            used_temperature = temperature if attempt == 0 else min(0.9, temperature + 0.4)
            reply, finish = client.chat(request_id, messages, used_temperature,
                                        math.ceil(hg.TOKENS_PER_WORD * hg.RATIO[1] * hg.words_of(original)), used_seed)
            plain, reason = hg.judge(original, reply, finish)
            measured = diversity(original, plain) if plain else None
            if plain and measured["problems"]:
                reason, plain = "; ".join(measured["problems"]), None
            if plain and variant and versions[0].get("plain") and hg.folded_words(plain) == hg.folded_words(versions[0]["plain"]):
                reason, plain = "the second version duplicates the first", None
            attempts.append({"request_id": request_id, "seed": used_seed, "temperature": used_temperature,
                             "finish_reason": finish, "reason": reason, "diversity": measured})
            if plain:
                accepted = {"plain": plain, "variant": variant + 1, "seed": used_seed,
                            "temperature": used_temperature, "attempts": attempts}
                break
            copied = hg.copied(original, reply)
            feedback = ("Copied stretches: " + "; ".join(copied) + ". ") if copied else ""
            messages = messages[:2] + [{"role": "assistant", "content": reply},
                        {"role": "user", "content": feedback + "The rewrite failed: " + str(reason)
                         + ". Rewrite the whole passage with different words and syntax, preserving every claim and adding nothing."}]
        versions.append(accepted or {"variant": variant + 1, "plain": None, "attempts": attempts})
    return dict(unit, versions=versions, accepted=all(v["plain"] for v in versions), recipe=RECIPE)


def validate_results(units, rows):
    by_id = {u["id"]: u for u in units}
    if len(by_id) != len(units):
        raise ValueError("duplicate unit id")
    seen = set()
    for row in rows:
        if row.get("id") in seen or row.get("id") not in by_id:
            raise ValueError("duplicate or unknown completed unit")
        seen.add(row["id"])
        unit = by_id[row["id"]]
        if any(row.get(k) != unit.get(k) for k in ("work", "ref", "original", "split", "parent_id", "kind")):
            raise ValueError("saved unit no longer matches the frozen corpus")
        if row.get("recipe") != RECIPE or len(row.get("versions", [])) != 2:
            raise ValueError("a round-two unit needs both recipe4 versions")
        versions = row["versions"]
        if [v.get("variant") for v in versions] != [1, 2]:
            raise ValueError("versions must be numbered one and two")
        texts = [v.get("plain") for v in versions]
        if row.get("accepted") != all(isinstance(t, str) and bool(t.strip()) for t in texts):
            raise ValueError("accepted status disagrees with version texts")
    return seen


def gate(units, good, failed):
    seen = validate_results(units, good + failed)
    if any(not row.get("accepted") for row in good) or any(row.get("accepted") for row in failed):
        raise ValueError("accepted and failed unit ledgers disagree")
    ratios = [hg.words_of(v["plain"]) / hg.words_of(row["original"]) for row in good for v in row["versions"]]
    mean = statistics.mean(ratios) if ratios else None
    share = len(failed) / max(1, len(units))
    pending = len(units) - len(seen)
    return {"units": len(units), "accepted_units": len(good), "accepted_pairs": 2 * len(good),
            "failed_units": len(failed), "pending_units": pending, "failed_share": share, "mean_ratio": mean,
            "passed": bool(units) and pending == 0 and mean is not None and share < 0.10 and 0.8 <= mean <= 1.2}


def generate_units(todo, client, workers, seed):
    """Bounded in-flight work; stop submissions and future asks on a transport failure."""
    stop, previous = Event(), client.before_request
    def before_request():
        if stop.is_set():
            raise TransportError("round-two worker stopped; no new request")
        if previous:
            previous()
    client.before_request = before_request
    pool = ThreadPoolExecutor(max_workers=workers)
    queue, pending, ready, emit = iter(enumerate(todo)), {}, {}, 0
    def failed(future):
        if not future.cancelled() and future.exception() is not None:
            stop.set()
    try:
        while True:
            while not stop.is_set() and len(pending) < workers:
                item = next(queue, None)
                if item is None:
                    break
                index, unit = item
                future = pool.submit(paraphrase_unit, unit, client, seed)
                future.add_done_callback(failed)
                pending[future] = index
            if not pending:
                break
            finished, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in finished:
                index = pending.pop(future)
                ready[index] = future.result()
            while emit in ready:
                yield ready.pop(emit)
                emit += 1
    finally:
        stop.set()
        for future in pending:
            future.cancel()
        pool.shutdown(wait=True, cancel_futures=True)
        client.before_request = previous


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build", action="store_true")
    p.add_argument("--paraphrase", action="store_true")
    p.add_argument("--stats", action="store_true")
    p.add_argument("--out", type=Path, default=hg.TRAIN)
    p.add_argument("--url")
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--limit", type=int)
    p.add_argument("--seed", type=int, default=hg.SPLIT_SEED)
    p.add_argument("--timeout", type=float, default=300)
    p.add_argument("--latency-observation", type=Path)
    p.add_argument("--latency-limit", type=float)
    a = p.parse_args(argv)
    if not (a.build or a.paraphrase or a.stats):
        p.error("choose --build, --paraphrase or --stats")
    if not 1 <= a.workers <= 2 or a.limit is not None and a.limit < 1:
        p.error("one or two workers; a positive limit")
    if not math.isfinite(a.timeout) or a.timeout <= 0:
        p.error("a positive finite timeout is required")
    if a.paraphrase and (not a.url or not a.latency_observation or not a.latency_limit or not math.isfinite(a.latency_limit) or a.latency_limit <= 0):
        p.error("--paraphrase needs --url and a frozen --latency-observation/--latency-limit")
    if a.build:
        books = hg.shelf.load()
        if not books:
            p.error("the shelf is missing")
        units, report = build_units(books, a.seed)
        # No overwrite, even for a CPU rebuild: a new source requires a new output root.
        write_new(a.out / UNITS, b"".join(json_bytes(u) for u in units))
        write_new(a.out / "hegelizer2-build.json", json_bytes(report))
        print(json.dumps(report, ensure_ascii=False))
    units = strict_rows(a.out / UNITS)
    if not units:
        p.error("build the round-two units first")
    good, failed = strict_rows(a.out / DONE), strict_rows(a.out / FAILED)
    done = validate_results(units, good + failed)
    if a.paraphrase:
        plan = {"recipe": RECIPE, "units_sha256": hashlib.sha256((a.out / UNITS).read_bytes()).hexdigest(),
                "seed": a.seed, "temperatures": TEMPERATURES, "asks_per_variant": hg.ASKS, "slot": 1,
                "latency_limit": a.latency_limit, "url": a.url.rstrip("/"), "timeout": a.timeout,
                "source_sha256": {name: hashlib.sha256((hg.REPO / name).read_bytes()).hexdigest() for name in
                    ["tools/hegelizer.py", "tools/hegelizer_round2.py", "tools/recorded_llama.py"]}}
        freeze_plan(a.out / "hegelizer2-generation-plan.json", plan)
        guard = LatencyGuard(a.latency_observation, limit=a.latency_limit)
        client = RecordedClient(a.url, a.out / "hegelizer2-raw", timeout=a.timeout, before_request=guard)
        order = list(units)
        random.Random(a.seed).shuffle(order)
        todo = [u for u in order if u["id"] not in done]
        if a.limit:
            todo = todo[:a.limit]
        for row in generate_units(todo, client, a.workers, a.seed):
            path = a.out / (DONE if row["accepted"] else FAILED)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("ab") as f:
                f.write(json_bytes(row))
                f.flush()
                import os
                os.fsync(f.fileno())
        good, failed = strict_rows(a.out / DONE), strict_rows(a.out / FAILED)
    result = gate(units, good, failed)
    print(json.dumps(result, ensure_ascii=False))
    return (0 if result["passed"] else 1) if a.stats else 0


if __name__ == "__main__":
    raise SystemExit(main())
