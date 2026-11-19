"""Build one Anki package per topic from flashcards/<topic>/ and quizzes/<topic>/.

Usage: python3 tools/build_anki.py [out_dir]
Writes <out_dir>/<topic>.apkg for every topic folder (default out_dir: build/).
A trailing "(§x.y)" on a flashcard back, or a quiz "section" field, renders as a
small source footer. The deck title comes from the first heading of the topic README.

Topics in QA_TOPICS use question-and-answer cards: a leading "[Foundation]", "[Core]"
or "[Advanced]" on a flashcard front or quiz question becomes a level badge and an Anki tag,
and answers may use **bold**, `code`, "- " bullet lines and ``` code fences, with a
literal \\n separating lines (a TSV field can't hold a newline).
"""
import hashlib
import html
import json
import pathlib
import re
import sys

import genanki

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSS = (ROOT / "tools" / "card.css").read_text(encoding="utf-8")
SECTION = re.compile(r"\s*\((§[^)]*)\)\s*$")
# Topics whose flashcards and quiz for one unit share a sub-deck named by the unit
# ("Title::Architecture"). Other topics keep one sub-deck per file, so their decks update in place.
UNIT_DECKS = {"engineering-agent-harnesses"}
QA_TOPICS = {"engineering-agent-harnesses"}
LEVEL = re.compile(r"^\[(Foundation|Core|Advanced)\]\s+")

BASIC = genanki.Model(
    1_794_660_011, "Study Basic v2",
    fields=[{"name": "Front"}, {"name": "Back"}, {"name": "Source"}],
    templates=[{
        "name": "Card",
        "qfmt": "<div class=term>{{Front}}</div>",
        "afmt": "{{FrontSide}}<hr id=answer><div class=body>{{Back}}</div>"
                "{{#Source}}<div class=src>{{Source}}</div>{{/Source}}",
    }],
    css=CSS,
)
MCQ = genanki.Model(
    1_794_660_012, "Study MCQ v2",
    fields=[{"name": "Question"}, {"name": "Options"}, {"name": "Answer"}, {"name": "Source"}],
    templates=[{
        "name": "Card",
        "qfmt": "<div class=q>{{Question}}</div>{{Options}}",
        "afmt": "{{FrontSide}}<hr id=answer><div class=body>{{Answer}}</div>"
                "{{#Source}}<div class=src>{{Source}}</div>{{/Source}}",
    }],
    css=CSS,
)

QA_CSS = CSS + (ROOT / "tools" / "qa.css").read_text(encoding="utf-8")
LEVEL_BADGE = "{{#Level}}<div class=level>{{Level}}</div>{{/Level}}"
QA_BASIC = genanki.Model(
    1_794_660_013, "Study QA v1",
    fields=[{"name": "Level"}, {"name": "Front"}, {"name": "Back"}, {"name": "Source"}],
    templates=[{
        "name": "Card",
        "qfmt": LEVEL_BADGE + "<div class=q>{{Front}}</div>",
        "afmt": "{{FrontSide}}<hr id=answer><div class=body>{{Back}}</div>"
                "{{#Source}}<div class=src>{{Source}}</div>{{/Source}}",
    }],
    css=QA_CSS,
)
QA_MCQ = genanki.Model(
    1_794_660_014, "Study QA MCQ v1",
    fields=[{"name": "Level"}, {"name": "Question"}, {"name": "Options"}, {"name": "Answer"}, {"name": "Source"}],
    templates=[{
        "name": "Card",
        "qfmt": LEVEL_BADGE + "<div class=q>{{Question}}</div>{{Options}}",
        "afmt": "{{FrontSide}}<hr id=answer><div class=body>{{Answer}}</div>"
                "{{#Source}}<div class=src>{{Source}}</div>{{/Source}}",
    }],
    css=QA_CSS,
)


def stable_id(text):
    """Deterministic 31-bit id so rebuilds update decks instead of duplicating them."""
    return int(hashlib.sha1(text.encode()).hexdigest()[:8], 16) >> 1


def title_from(path):
    return path.stem.replace("_", " ").replace("mcq", "quiz").strip().capitalize()


def unit_from(path):
    return path.stem.removesuffix("_flashcards").removesuffix("_mcq").replace("_", " ").strip().capitalize()


def topic_title(topic):
    for base in ("flashcards", "quizzes"):
        readme = ROOT / base / topic / "README.md"
        if readme.exists():
            first = readme.read_text(encoding="utf-8").splitlines()[0]
            return first.lstrip("# ").strip()
    return topic


def source_label(title, section):
    return f"{html.escape(title)} {html.escape(section)}" if section else ""


def flashcard_notes(path, title):
    for line in path.read_text(encoding="utf-8").splitlines():
        term, back = line.split("\t")
        match = SECTION.search(back)
        section = match.group(1) if match else ""
        back = SECTION.sub("", back)
        yield genanki.Note(model=BASIC,
                           fields=[html.escape(term), html.escape(back), source_label(title, section)],
                           guid=genanki.guid_for(path.stem, term))


def quiz_notes(path, title):
    for item in json.loads(path.read_text(encoding="utf-8")):
        opts = "".join(f"<li>{html.escape(o)}</li>" for o in item["options"])
        letter = "ABCDEF"[item["answer"]]
        correct = html.escape(item["options"][item["answer"]])
        answer = f"<div class=correct>{letter}. {correct}</div><div>{html.escape(item['explanation'])}</div>"
        yield genanki.Note(model=MCQ,
                           fields=[html.escape(item["q"]), f"<ol type=A class=opts>{opts}</ol>", answer,
                                   source_label(title, item.get("section", ""))],
                           guid=genanki.guid_for(path.stem, item["q"]))


def inline(text):
    """Escape text, then render `code` and **bold**."""
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for part in parts:
        if len(part) > 1 and part.startswith("`") and part.endswith("`"):
            out.append(f"<code>{html.escape(part[1:-1])}</code>")
        else:
            out.append(re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(part)))
    return "".join(out)


def render(text):
    """Render a model answer: paragraphs, "- " bullet lines and ``` code fences."""
    out, items, code = [], [], None
    for line in text.replace("\\n", "\n").split("\n"):
        if code is not None:
            if line.strip().startswith("```"):
                out.append(f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>")
                code = None
            else:
                code.append(line)
            continue
        if line.startswith("- "):
            items.append(f"<li>{inline(line[2:])}</li>")
            continue
        if items:
            out.append(f"<ul class=plan>{''.join(items)}</ul>")
            items = []
        if line.strip().startswith("```"):
            code = []
        elif line.strip():
            out.append(f"<p>{inline(line.strip())}</p>")
    if items:
        out.append(f"<ul class=plan>{''.join(items)}</ul>")
    if code is not None:
        raise ValueError(f"unclosed code fence in: {text[:60]}")
    return "".join(out)


def split_level(text):
    match = LEVEL.match(text)
    return (match.group(1), text[match.end():]) if match else ("", text)


def qa_flashcard_notes(path, title):
    for line in path.read_text(encoding="utf-8").splitlines():
        front, back = line.split("\t")
        match = SECTION.search(back)
        section = match.group(1) if match else ""
        level, question = split_level(front)
        yield genanki.Note(model=QA_BASIC,
                           fields=[level, inline(question), render(SECTION.sub("", back)),
                                   source_label(title, section)],
                           guid=genanki.guid_for(path.stem, front), tags=[level] if level else [])


def qa_quiz_notes(path, title):
    for item in json.loads(path.read_text(encoding="utf-8")):
        level, question = split_level(item["q"])
        opts = "".join(f"<li>{inline(o)}</li>" for o in item["options"])
        letter = "ABCDEF"[item["answer"]]
        answer = (f"<div class=correct>{letter}. {inline(item['options'][item['answer']])}</div>"
                  f"{render(item['explanation'])}")
        yield genanki.Note(model=QA_MCQ,
                           fields=[level, inline(question), f"<ol type=A class=opts>{opts}</ol>", answer,
                                   source_label(title, item.get("section", ""))],
                           guid=genanki.guid_for(path.stem, item["q"]), tags=[level] if level else [])


def build_topic(topic, out_dir):
    title = topic_title(topic)
    decks = {}
    qa = topic in QA_TOPICS
    cards, quiz = (qa_flashcard_notes, qa_quiz_notes) if qa else (flashcard_notes, quiz_notes)
    sources = [(p, cards) for p in sorted((ROOT / "flashcards" / topic).glob("*.tsv"))]
    sources += [(p, quiz) for p in sorted((ROOT / "quizzes" / topic).glob("*.json"))]
    for path, notes in sources:
        name = f"{title}::{unit_from(path) if topic in UNIT_DECKS else title_from(path)}"
        deck = decks.setdefault(name, genanki.Deck(stable_id(name), name))
        for note in notes(path, title):
            deck.add_note(note)
    out = out_dir / f"{topic}.apkg"
    genanki.Package(list(decks.values())).write_to_file(str(out))
    return out, sum(len(d.notes) for d in decks.values())


def main():
    out_dir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "build")
    out_dir.mkdir(parents=True, exist_ok=True)
    topics = {p.name for base in ("flashcards", "quizzes") for p in (ROOT / base).iterdir() if p.is_dir()}
    for topic in sorted(topics):
        out, count = build_topic(topic, out_dir)
        print(f"wrote {out} ({count} notes)")


if __name__ == "__main__":
    main()
