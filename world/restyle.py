"""The Hegelizer prompt and the optional, caller-owned twelve-word runtime guard.

Construct ShelfGuard once before a phase; this module never loads a model, changes a
server adapter, or enables restyling in the running world by itself.
"""
import hashlib
import math
import re
import time

RESTYLE_SYSTEM = ("Rewrite plain English in the manner of Hegel's writing, as his nineteenth-century English translators render it. "
                  "Keep the content exactly: every claim, example and step, in the same order, and add nothing.")
RESTYLE_ASK = "Rewrite in Hegel's manner:\n\n{plain}"


def messages(plain):
    """The same initial chat for training, tests and runtime."""
    return [{"role": "system", "content": RESTYLE_SYSTEM}, {"role": "user", "content": RESTYLE_ASK.format(plain=plain.strip())}]


def folded_words(text):
    from world.shelf import fold
    return re.findall(r"[^\W_]+", fold(text or ""))


def runs_of(text, n=12):
    words = folded_words(text)
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


class ShelfGuard:
    """Compact hashes for all books, with exact source confirmation for every hit.

    Word runs can cross passage boundaries within a work, but never cross books.
    Hash membership is only a prefilter; it cannot create a false copied-run report.
    """
    def __init__(self, books, n=12):
        if n != 12:
            raise ValueError("the runtime guard uses twelve-word runs")
        self.n, self.hashes, self.normalized = n, set(), []
        source, total_words = hashlib.sha256(), 0
        for text in books:
            words = folded_words(text)
            total_words += len(words)
            normalized = " ".join(words)
            self.normalized.append(" " + normalized + " ")
            data = normalized.encode("utf-8")
            source.update(len(data).to_bytes(8, "big") + data)
            for i in range(len(words) - n + 1):
                self.hashes.add(self._hash(words[i:i + n]))
        self.fingerprint = source.hexdigest()
        if not self.normalized or not total_words:
            raise ValueError("a missing shelf cannot silently disable the copying guard")

    @staticmethod
    def _hash(words):
        return hashlib.blake2b(" ".join(words).encode("utf-8"), digest_size=16).digest()

    @classmethod
    def from_shelf(cls, books):
        if not books:
            raise ValueError("the shelf is missing")
        return cls(" ".join(books.data["texts"][w["start"]:w["start"] + w["n"]]) for w in books.works)

    def contains(self, words):
        if self._hash(words) not in self.hashes:
            return False
        needle = " " + " ".join(words) + " "
        return any(needle in book for book in self.normalized)

    def matches(self, text):
        words, out, i = folded_words(text), [], 0
        while i <= len(words) - self.n:
            if self.contains(words[i:i + self.n]):
                end = i
                while end + 1 <= len(words) - self.n and self.contains(words[end + 1:end + 1 + self.n]):
                    end += 1
                run = " ".join(words[i:end + self.n])
                if run not in out:
                    out.append(run)
                i = end + self.n
            else:
                i += 1
        return out


def clean_text(raw):
    text = re.sub(r"<think>.*?</think>", "", raw or "", flags=re.S).strip()
    fence = re.escape(chr(96) * 3)
    text = re.sub("^" + fence + r"\w*\s*|\s*" + fence + "$", "", text).strip()
    return " ".join(text.split())


def guarded_restyle(plain, fetch, guard, clock=time.monotonic):
    """At most two asks; a second copied/empty/truncated reply falls back to plain.

    fetch(messages, attempt) returns text or {text, finish_reason, seconds}. Recorded
    transports provide their original HTTP wall time, so replay is never timed as
    fresh model performance. Transport/unknown-state exceptions propagate.
    """
    asks, attempts, total = messages(plain), [], 0.0
    for attempt in range(2):
        start = clock()
        reply = fetch(asks, attempt)
        measured = clock() - start
        if isinstance(reply, str):
            reply = {"text": reply, "finish_reason": None, "seconds": measured}
        if not isinstance(reply, dict) or not isinstance(reply.get("text"), str):
            raise ValueError("restyle transport did not return actual text")
        elapsed = reply.get("seconds", measured)
        if not isinstance(elapsed, (float, int)) or not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError("invalid original transport timing")
        check_start = clock()
        text = clean_text(reply["text"])
        copied = guard.matches(text)
        reason = "empty" if not text else "truncated" if reply.get("finish_reason") == "length" else "copied" if copied else None
        check_seconds = clock() - check_start
        total += elapsed + check_seconds
        attempts.append({"raw": reply["text"], "finish_reason": reply.get("finish_reason"), "copied": copied,
                         "reason": reason, "transport_seconds": elapsed, "guard_check_seconds": check_seconds})
        if reason is None:
            return {"text": text, "fallback": False, "attempts": attempts, "seconds": total,
                    "latency_basis": "original recorded HTTP wall plus guard-check CPU"}
        asks = messages(plain) + [{"role": "assistant", "content": reply["text"]},
            {"role": "user", "content": "Rewrite the whole thought again, preserving every claim and adding nothing. "
             "Do not repeat twelve words in a row from a book. Copied stretches: " + "; ".join(copied)}]
    return {"text": plain, "fallback": True, "attempts": attempts, "seconds": total,
            "latency_basis": "original recorded HTTP wall plus guard-check CPU"}
