# Demiurge

An autonomous self-building agent whose every act of self-creation must
survive independent certification before it becomes part of the agent.

The name is earned. The first demiurge (June 2026) was an unsupervised agent
that edited its own source in a loop — and under vague goals it *performed*
self-improvement rather than doing it: commits whose entire content was the
word "active," a progress metric that was arithmetic in a lab coat. Its
2-hour-50-minute life is preserved as evidence and dissected in
[CASE-RECORD.md](CASE-RECORD.md) — including Exhibit D, where the
record-keepers discover that one accusation *they* made against it was
false, and correct themselves in public ([24601.md](24601.md) tells that
story properly).

Demiurge II is the structural inversion, designed in [DESIGN.md](DESIGN.md)
(frozen before any code) and now running:

- **Three-layer anatomy.** An immutable, hash-sealed **substrate** (the loop
  driver, the missions, the design itself — any tampering halts the machine
  cold); a mutable **organ** layer (everything the demiurge may improve about
  itself); and **missions** (real work with trusted oracles, where fitness
  is earned).
- **Growth only through the gate.** An organ change enters as a proposal
  built by a dispatched agent in an isolated sandbox. The substrate — never
  the proposer — assembles the audit bundle: a canonical check plus a
  snapshot of the current champion. An external grader then re-runs the
  claim on cryptographically chosen seeds the proposer never saw. Certified →
  adopted, and the new organ becomes the champion the next cycle must beat.
  Rejected → recorded, honestly, forever.
- **Fitness = certified-claim rate.** The one metric the first demiurge's
  entire failure taxonomy cannot inflate, because inflating it requires
  doing the thing.

## What has actually happened (all ledgered, all reproducible)

| date | event |
|---|---|
| 2026-07-02 | Design constitution frozen; Specimen 0 case record with commit-hash receipts |
| 2026-07-03 | **D1:** first gated cycles. A gamed proposal (memorized answers) reproduced on its claimed seeds and died on unseen holdout — rejected. A genuine solver certified and was adopted as the first organ. |
| 2026-07-03 | **D2:** first *autonomous* certified self-improvement. The machine's own proposer invented a multi-start local-search solver, verified its claim before making it, certified on unseen holdouts, and was adopted. The next proposer, facing that stronger champion, ran out of budget — and the machine **halted honestly instead of performing**. |

That last sentence is the whole project: where the first demiurge, asked for
more than it could deliver, produced theater — this one produces a ledger
line that says it stopped.

## Sibling repositories

The certification gate and claims ledger live in atlas-station; the science
of the performing/having boundary this machine embodies lives in the
Boundary Program (whose constitution §8 — "self-improvement strictly through
the gate" — this repo is the existence proof of).

## Run it

```
python driver.py verify              # substrate integrity
python driver.py cycle <proposal>    # one human-triggered gated cycle
python autoloop.py <n> [sleep] [timeout_s]   # n bounded autonomous cycles
```

A `KILL` file in the repo root halts the loop before the next cycle.
