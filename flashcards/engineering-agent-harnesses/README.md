# Engineering Agent Harnesses

Study materials for *Engineering Agent Harnesses*, a course by Ava S. Barron on
designing, building and operating the software around an LLM agent: the model
boundary, the executor and its gates, the ledger, and the evidence that the
harness did what it claims.

| Deck | Covers |
|---|---|
| Orientation | shadow, live and replay runs; what a verified ledger does and doesn't prove; the harness card |
| Architecture | frozen contracts, the pure strategy, the loop grammar as an automaton, the run contract |
| Tokens and sampling | BPE, logits, temperature, top-k and nucleus sampling, nondeterminism, record and replay |
| Policy as code | the gate table as a reference monitor, deny wins, fail closed, the budget day, the Ask tier |
| Glossary | the course's named concepts |

Each card is a question tagged Foundation, Core or Advanced, then a model answer:
a direct answer with **bold** key terms, an optional bulleted plan, and a closing
line on what a strong answer names or where the trap is. A few questions ask you
to implement a function from the course's labs.

In the TSV files a literal `\n` separates lines of an answer, `- ` starts a bullet,
and ``` fences hold code; `tools/build_anki.py` renders them, and tags each Anki
note with its level.

Source references name the course page, or the Spec page and clause, that each
card comes from.
