"""Build one Anki package per topic from flashcards/<topic>/ and quizzes/<topic>/.

Usage: python3 tools/build_anki.py [out_dir]
Writes <out_dir>/<topic>.apkg for every topic folder (default out_dir: build/).
"""
import hashlib
import html
import json
import pathlib
import sys

import genanki

ROOT = pathlib.Path(__file__).resolve().parent.parent

BASIC = genanki.Model(
    1_794_660_001, "Study Basic",
    fields=[{"name": "Front"}, {"name": "Back"}],
    templates=[{"name": "Card", "qfmt": "{{Front}}", "afmt": "{{FrontSide}}<hr id=answer>{{Back}}"}],
)
MCQ = genanki.Model(
    1_794_660_002, "Study MCQ",
    fields=[{"name": "Question"}, {"name": "Answer"}],
    templates=[{"name": "Card", "qfmt": "{{Question}}", "afmt": "{{FrontSide}}<hr id=answer>{{Answer}}"}],
)


def stable_id(text):
    """Deterministic 31-bit id so rebuilds update decks instead of duplicating them."""
    return int(hashlib.sha1(text.encode()).hexdigest()[:8], 16) >> 1


def title_from(path):
    return path.stem.replace("_", " ").replace("mcq", "quiz").strip().capitalize()


def flashcard_notes(path):
    for line in path.read_text(encoding="utf-8").splitlines():
        term, definition = line.split("\t")
        yield genanki.Note(model=BASIC, fields=[html.escape(term), html.escape(definition)],
                           guid=genanki.guid_for(path.stem, term))


def quiz_notes(path):
    for item in json.loads(path.read_text(encoding="utf-8")):
        opts = "".join(f"<li>{html.escape(o)}</li>" for o in item["options"])
        correct = item["options"][item["answer"]]
        answer = f"<b>{'ABCDEF'[item['answer']]}. {html.escape(correct)}</b><br>{html.escape(item['explanation'])}"
        yield genanki.Note(model=MCQ, fields=[f"{html.escape(item['q'])}<ol type='A'>{opts}</ol>", answer],
                           guid=genanki.guid_for(path.stem, item["q"]))


def build_topic(topic, out_dir):
    decks = []
    sources = [(p, flashcard_notes) for p in sorted((ROOT / "flashcards" / topic).glob("*.tsv"))]
    sources += [(p, quiz_notes) for p in sorted((ROOT / "quizzes" / topic).glob("*.json"))]
    for path, notes in sources:
        name = f"{topic}::{title_from(path)}"
        deck = genanki.Deck(stable_id(name), name)
        for note in notes(path):
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
