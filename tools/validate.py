"""Validate every flashcard and quiz file in the repo.

Usage: python3 tools/validate.py
Exits non-zero and lists problems if any file is invalid.
"""
import json
import pathlib
import sys

from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schema" / "quiz.schema.json").read_text(encoding="utf-8"))


def check_flashcards(path):
    problems = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        parts = line.split("\t")
        if len(parts) != 2 or not all(p.strip() for p in parts):
            problems.append(f"{path}:{n}: expected 'term<TAB>definition'")
    return problems


def check_quiz(path, validator):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        return [f"{path}: invalid JSON: {err}"]
    problems = [f"{path}: {e.json_path}: {e.message}" for e in validator.iter_errors(data)]
    for i, item in enumerate(data if isinstance(data, list) else []):
        if isinstance(item, dict) and item.get("answer", 0) >= len(item.get("options", [])):
            problems.append(f"{path}: $[{i}].answer: index out of range")
    return problems


def main():
    validator = Draft202012Validator(SCHEMA)
    problems = []
    for path in sorted((ROOT / "flashcards").rglob("*.tsv")):
        problems += check_flashcards(path)
    for path in sorted((ROOT / "quizzes").rglob("*.json")):
        problems += check_quiz(path, validator)
    print("\n".join(problems) or "All files valid.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
