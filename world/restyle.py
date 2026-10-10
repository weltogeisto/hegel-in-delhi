"""The Hegelizer's prompt: plain English in, his manner out. One place for the trainer (pc/train_hegel.py --phase restyle), the Hegel test's restyle
part (tools/hegel_test.py) and, later, the world, so that the adapter is asked at runtime exactly what it was trained on. Standard library only."""

RESTYLE_SYSTEM = ("Rewrite plain English in the manner of Hegel's writing, as his nineteenth-century English translators render it. "
                  "Keep the content exactly: every claim, example and step, in the same order, and add nothing.")
RESTYLE_ASK = "Rewrite in Hegel's manner:\n\n{plain}"


def messages(plain):
    """[system, user]: the chat that asks for `plain` in his manner. Training adds the assistant turn (his own text); the server writes it."""
    return [{"role": "system", "content": RESTYLE_SYSTEM}, {"role": "user", "content": RESTYLE_ASK.format(plain=plain.strip())}]
