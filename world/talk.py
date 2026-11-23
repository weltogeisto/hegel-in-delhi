"""HEGEL_TALK_SCENE: the lecture he gives at the IIC and the one question from the hall (pc/TALK-SCENE.md)."""
import re

from .contract import WRITE_SCHEMA
from .works import cut

TITLE = "Lecture at the IIC: "          # a lecture is filed under this, so that it is recognised among his writings
ABOUT = "A lecture, given to the hall at the India International Centre."
CAP = 6000                              # characters: about 800 words and a little over
MIN_WORDS = 100                         # a reply with fewer is not a lecture
TOKENS = 1600
LECTURE_ASK = ("The programme officer has shown you into the lecture hall and the talk is yours. Give the lecture now, spoken to the hall: "
               "about 600 to 800 words, in English, in your own voice, as a man speaks to a room and not as a letter. "
               "Draw on what you have written lately (your manuscripts, below, if there are any) and on where you stand tonight; "
               "do not invent journeys, meetings or events. Give it a short title; the kind is essay.")
LECTURE_FORMAT = 'Answer with the JSON object only: {"title": "...", "kind": "essay", "to": null, "continues": false, "text": "..."}'
LECTURE_SCHEMA = {**WRITE_SCHEMA, "properties": {**WRITE_SCHEMA["properties"], "text": {"type": "string", "maxLength": CAP + 500}}}


def clean(out):
    """The lecture from the mind's answer, filed as an essay under its own title, or None if it is unusable: a title and a talk's worth of words."""
    if not isinstance(out, dict) or not isinstance(out.get("title"), str) or not isinstance(out.get("text"), str):
        return None
    title, text = " ".join(out["title"].split()), out["text"].strip()
    if not title or len(text.split()) < MIN_WORDS:
        return None
    return {"title": (TITLE + title)[:100], "kind": "essay", "to": None, "continues": False, "text": cut(text, CAP), "about": ABOUT}


def last_paragraph(text):
    """The last paragraph of the lecture, or the whole of it cut to 600 characters when it has no paragraphs."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return cut(paras[-1] if paras else text.strip(), 600)


def question_lead(title, last):
    """What the listener is told in place of 'He says': the talk is over, and one question is wanted."""
    return (f"He has just finished a lecture to the hall, called “{title}”. Its last paragraph was: “{last}”\n"
            "You are one of the people in the hall. Ask him one question about what he said, in one or two sentences, plainly and politely. "
            "Do not answer it yourself, and do not speak of anything else.")
