# The Claw AI Agent Ecosystem: study guide

Flashcards and quizzes for
[*The Claw AI Agent Ecosystem: Designing, Operating, and Securing Self-Hosted AI Agents*](https://www.amazon.com/dp/B0GT7NBZV3)
by Ava S. Barron.

Use them to review the book chapter by chapter, prepare a team reading
group, or check what you know about running self-hosted AI agents. Every
card and question cites the book section it covers.

## Contents

| Path | What it holds |
|---|---|
| `flashcards/` | 14 decks, one term and definition per line, tab-separated. |
| `quizzes/` | 15 multiple-choice quizzes in JSON, with answers, explanations, and section numbers. |
| `deck_metadata.json` | Title, description, and tags for each deck. |

### Decks

- One flashcard deck and one quiz for each of Chapters 1–11.
- Themed sets:
  - Agentic memory vs. stateless chatbots (flashcards and quiz)
  - AI agent security threat-modeling scenarios (quiz)
  - Cost and operations decisions (quiz)
  - Comparing Claw agent frameworks (quiz)
  - Glossary (flashcards)

## Use the flashcards

The `.tsv` files import into most flashcard apps:

- **Anki**: **File > Import**, then pick a file. Set the field separator to
  **Tab**.
- **Quizlet**: **Create > Flashcard set > Import**, paste the file
  contents, then set the separator to **Tab**.
- **Brainscape**: **Create deck > Import**, paste, and use **Tab**.

A ready-made Anki package with every deck is shared on AnkiWeb.

## Use the quizzes

Each quiz file is a JSON array. Each item looks like this:

```json
{
  "q": "Question text",
  "options": ["A", "B", "C", "D"],
  "answer": 3,
  "explanation": "Why the answer is right.",
  "section": "§1.3.1"
}
```

`answer` is the zero-based index of the correct option.

## About the book

*The Claw AI Agent Ecosystem* treats self-hosted AI agent runtimes like
production distributed systems: architecture, identity and memory files,
the runtime loop, deployment, cost control, safe autonomy, security, and
the wider Claw ecosystem.

| Edition | Identifier |
|---|---|
| Paperback | ISBN 979-8-2526-0474-9 |
| Kindle | ASIN [B0GT7NBZV3](https://www.amazon.com/dp/B0GT7NBZV3) |

## License

Study materials © 2026 Ava S. Barron, licensed under
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). Share and
adapt them for non-commercial use with credit to the author and the book.
