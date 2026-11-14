"""Build one Anki package per topic from flashcards/<topic>/ and quizzes/<topic>/.

Usage: python3 tools/build_anki.py [out_dir]
Writes <out_dir>/<topic>.apkg for every topic folder (default out_dir: build/).
A trailing "(§x.y)" on a flashcard back, or a quiz "section" field, renders as a
small source footer. The deck title comes from the first heading of the topic README.
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


def stable_id(text):
    """Deterministic 31-bit id so rebuilds update decks instead of duplicating them."""
    return int(hashlib.sha1(text.encode()).hexdigest()[:8], 16) >> 1


def title_from(path):
    return path.stem.replace("_", " ").replace("mcq", "quiz").strip().capitalize()


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


def build_topic(topic, out_dir):
    title = topic_title(topic)
    decks = []
    sources = [(p, flashcard_notes) for p in sorted((ROOT / "flashcards" / topic).glob("*.tsv"))]
    sources += [(p, quiz_notes) for p in sorted((ROOT / "quizzes" / topic).glob("*.json"))]
    for path, notes in sources:
        name = f"{title}::{title_from(path)}"
        deck = genanki.Deck(stable_id(name), name)
        for note in notes(path, title):
            deck.add_note(note)
        decks.append(deck)
    out = out_dir / f"{topic}.apkg"
    genanki.Package(decks).write_to_file(str(out))
    return out, sum(len(d.notes) for d in decks)


def main():
    out_dir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "build")
    out_dir.mkdir(parents=True, exist_ok=True)
    topics = {p.name for base in ("flashcards", "quizzes") for p in (ROOT / base).iterdir() if p.is_dir()}
    for topic in sorted(topics):
        out, count = build_topic(topic, out_dir)
        print(f"wrote {out} ({count} notes)")


if __name__ == "__main__":
    main()
