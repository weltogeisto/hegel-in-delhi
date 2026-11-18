# A notebook of the age

**Why.** It was an idea in `DECISIONS.md` that wasn't yet decided. His prompt remembers only his last moments and the owl's gist of three nights, so what he learned about this century weeks ago fades from view, though the 1831 gate allows it. Built on the night of 18 November, on Welt's "move us forward" and "i trust you". The switch stays off.

## What `HEGEL_NOTEBOOK=1` does

1. **Each night the owl rewrites it,** after the diary, from the old notebook and the day. It covers what he has come to understand about this century (machines, institutions, events, customs and people) and how his view of each has moved. The owl keeps what still holds, adds what the day taught him and drops what no longer matters.
2. **It records, never steers:** only what he met and thought, in his own terms, never advice or what he should do next.
3. **It is short:** at most 1,500 characters, cut after a sentence (`world/owl.py`, `notebook_text`). The owl's answer gets 500 more tokens for it.
4. **It passes the same gate as the diary:** a name or a thing from after 1831 that he has not met sends the owl back to write it again.
5. **It is in his prompt every step of the next day,** after "You remember", headed "Your notebook of this age, as you keep it each night" (`world/contract.py`).
6. **It is kept** in `state["notebook"]`, with the day it was written, and in the owl's record of the night.

**Off, nothing changes:** not the owl's call, not the state, not his prompt (`tests/test_notebook.py`).

## Before it goes on

It changes his prompt, so it gets the street's kind of test first: forks of two days, so the second day sees the first night's notebook. Five seeds with it on and five with it off, from the first complete day after the museums, read for doctrine, echoes, refusals and what he refers back to from earlier days. Its place in the order comes after the file's next act, on Welt's word.

Its texts are world content written by the model. They are never training data.
