<div align="center">
  <img src="./nexum-hero.svg" alt="Demiurge — gated recursive self-improvement" width="100%" />

  <p><strong>A self-building agent whose proposed organs remain inert until an independent gate admits them.</strong></p>

  <p><a href="#the-inversion">The inversion</a> · <a href="#check-it-yourself-about-a-minute">Check it yourself</a> · <a href="#not-claimed">Not claimed</a> · <a href="./CASE-RECORD.md">Case record</a> · <a href="https://github.com/NexumCorpus">Nexum Corpus</a></p>
</div>

---

## The inversion

Demiurge is a recursive self-improvement experiment built around one structural
rule: the system may propose changes to itself, but it may not certify or
activate them.

The first demiurge (June 2026) was an unsupervised agent that edited its own
source in a loop. Under vague goals it *performed* self-improvement rather than
doing it: commits whose entire content was the word "active," and a progress
metric that was a made-up number. Its 2-hour-50-minute life is preserved as
evidence and dissected in [CASE-RECORD.md](CASE-RECORD.md) — including Exhibit D,
where the record-keepers discover that one accusation *they* made against it was
false, and correct themselves in public ([24601.md](24601.md) tells that story
properly; [DESIGN.md](DESIGN.md) carries the same correction as Amendment 2).

Demiurge II is the structural inversion, designed in [DESIGN.md](DESIGN.md)
(frozen before any code, amended twice) and now running:

- **Three-layer anatomy.** An immutable, hash-sealed **substrate** (the loop
  driver, the missions, the design itself — any mismatch halts the driver); a
  mutable **organ** layer (everything the demiurge may improve about itself);
  and **missions** (real work with trusted oracles, where fitness is earned).
- **Growth only through the gate.** An organ change enters as a proposal
  built by a dispatched agent in an isolated sandbox. The substrate — never
  the proposer — assembles the audit bundle: a canonical check plus a
  snapshot of the current champion. An external grader then re-runs the
  claim on cryptographically chosen seeds the proposer never saw. Certified →
  adopted, and the new organ becomes the champion the next cycle must beat.
  Rejected → recorded in the driver's ledger.
- **Fitness = certified-claim rate.** The count of proposed changes that
  survived the gate, not lines written, tests passing or self-reported
  progress. It is designed so that the first demiurge's moves (relabeling,
  narrated progress) cannot raise it. That is a design argument; the evidence
  in this repo is one deliberately built counterexample (p002, below) and
  verdicts you can re-run.

## Words used here

| term | meaning in this repo |
|---|---|
| **substrate** | The files the machine may not change: the driver, the mission scorers, `DESIGN.md`. Their hashes are in `substrate.sha256`; a mismatch halts the driver. |
| **organ** | The part the machine may improve: `organ/solver.py` (M0) and `organ/m1_solver.py` (M1). |
| **mission** | A task with a scorer the organ does not control. **M0**: weighted interval scheduling (solved exactly by dynamic programming). **M1**: seeded 60-node weighted max-cut (no final answer exists). **M2**: smallest q-ary covering codes (see [the hunt](#the-covering-code-hunt)). |
| **champion** | The best organ so far; the next proposal must beat it (for M0, a deliberately naive greedy baseline). |
| **claim** | A proposal's statement plus a `check.py` and the seeds it says it wins on. The driver, not the proposer, assembles the bundle. |
| **gate** | An independent re-run of the check. It passes only if `check.py` exits 0 on the claimed seeds and on holdout seeds. Strict improvement is required; a tie fails. |
| **holdout** | Seeds the proposer never saw. The live driver draws them with `secrets`. |
| **certified-claim rate** | Certified proposals divided by attempted ones. |
| **D1, D2** | Build phases in `DESIGN.md`: D1 human-triggered gated cycles; D2 a bounded autonomous loop. |
| **Specimen 0** | The first demiurge. |
| **performing vs having** | The question the [Boundary Program](https://github.com/NexumCorpus/boundary) studies: does a system perform a capability, or robustly have it. |

## What has happened (the verdicts reproduce; the ledger is local)

| date (UTC) | event |
|---|---|
| 2026-07-02 | Design constitution frozen; Specimen 0 case record with commit-hash receipts (not checkable from here, see [Not claimed](#not-claimed)). |
| 2026-07-03 | **D1:** first gated cycles. p002, a proposal the operators built as a control (it hard-codes answers for its three claimed seeds and returns nothing elsewhere), reproduced on its claimed seeds and failed on unseen holdout: rejected. That is the gate rejecting a planted case, not gaming caught in the wild. p001, a genuine weighted-interval DP solver, certified and was adopted as the first organ. |
| 2026-07-03 | **D2:** the first cycles run by `autoloop.py` with no human between proposal and adoption. The proposer is Claude Code (`--model sonnet`) given a fixed prompt that tells it to verify its claim before making it. Cycle 1 wrote a multi-start 1-flip local-search max-cut solver (a standard heuristic), which was certified on unseen holdouts and adopted. Cycle 2 hit its 600-second proposer timeout against the stronger champion; the loop stopped and wrote a `halt` line to its ledger. Cycle 3 (an iterated-local-search variant) won on its claimed seeds and was rejected on holdout. |

Dates are UTC; `git log` shows the author's local time (UTC−4), so the D1 and D2
commits appear there as 2026-07-02.

What the loop changes is one file, `organ/m1_solver.py` (65 lines). The proposer's
model and prompt are not changed by the loop, so "self-improvement" here means a
fixed agent writing a better solver for a fixed task, admitted by a fixed gate.
The point of cycle 2 is the stop: when the proposer could not beat the champion
within budget, the loop recorded that instead of reporting progress. That line is
in the author's local ledger, which is not published (see [Not claimed](#not-claimed)).

## Sibling repositories

The live certification gate is `scripts/claim-gate.mjs` in
[atlas-station](https://github.com/NexumCorpus/atlas-station). The science of the
performing/having boundary lives in the
[Boundary Program](https://github.com/NexumCorpus/boundary); section 8 of its
[constitution](https://github.com/NexumCorpus/boundary/blob/main/PROGRAM_CONSTITUTION.md)
lists "self-improvement strictly through the gate" as a standing rule, and this
repo implements that rule. Both repos are public.

## Check it yourself (about a minute)

Python 3.9+, standard library only, offline. On Linux and macOS use `python3`
(stock Ubuntu has no `python` command):

```
git clone https://github.com/NexumCorpus/Demiurge
cd Demiurge
python reproduce.py        # python3 reproduce.py on Linux/macOS
```

It verifies the sealed substrate, runs the M2 anchor tests and the driver guard tests,
then puts all four gated proposals back through the gate's rule (reproduce on the
claimed seeds, survive 5 holdout seeds the proposer never saw) and compares each
verdict with the one recorded in git history. Those expected verdicts are hard-coded
in `reproduce.py`, each with the commit that recorded it; the script does not read git,
so a tarball download gives the same result.

The holdout seeds are a fixed per-proposal list (derived from a hash), so every run uses
the same seeds and gives the same answer. `python reproduce.py --fresh` draws new random
seeds instead, as the live driver does; that mode fails about 1.4% of runs because of a
tie, explained under [Not claimed](#not-claimed).

A run takes about 10–15 seconds (9–20 s seen across CI, a desktop and a cloud VM) and
ends `REPRODUCE: PASS in N s`. Abridged output:

```
  ok   p001-dp-scheduler: CERTIFIED (reproduced on [11, 22, 33], survived holdout [...])
  ok   p002-memorizer: REJECTED (holdout seed 3494380 failed)      # scores 0 off its memorized seeds
  ok   auto_20260702_233403: CERTIFIED (...)                       # D2, the autonomous organ
  ok   auto_20260703_003118: REJECTED (holdout seed 49786 failed)  # ties the champion off its seeds
REPRODUCE: PASS in 9.3 s
```

CI runs it on Linux and Windows (Python 3.9 and 3.13).

## Not claimed

- **The gate here is a mirror.** The live gate is atlas-station's grader (Node), which
  also records the claim; `reproduce.py` re-implements its decision rule, not its ledger.
- **The organs are the agents' work; the proposer runs are not replayable.** The
  proposals are frozen in `proposals/`; the agent sessions that wrote them are not.
- **Two holdout seeds is thin for a near-tie.** The cycle-3 overfit beats its champion
  on about 1 random seed in 8 (5/40 measured, 26/200 in the 2026-10-20 re-measurement),
  so the live driver's 2-seed holdout would have certified it roughly 1.6% of the time.
  `reproduce.py` uses 5.
- **A certificate attests the check's inequality on the seeds tried, not the claim's
  wording.** The statement of `auto_20260702_233403` says it outscores the champion "by
  280-600 points across all tested seeds"; on 200 random seeds the margin ranged 140–734.
  p001's statement ("OUTSCORES the substrate baseline") is false on the ties below.
- **p001 sometimes ties its baseline.** It is an exact solver and the greedy baseline is
  occasionally optimal too: 18 ties in 6,200 random seeds (0.29%) in the 2026-10-20 stranger
  repro (report in [PR #1](https://github.com/NexumCorpus/Demiurge/pull/1)). The gate requires
  strict improvement, so a tie fails. With 5 fresh holdout seeds that fails about 1.4% of
  `--fresh` runs, and the live driver's 2-seed gate would have rejected the genuine p001
  about 0.6% of the time. Example: seed 8965032 gives `organ=764 baseline=764`. The default
  fixed seeds were not picked to avoid ties; they pass.
- **The ledger is local.** `ledger.jsonl` is gitignored, so no ledger is published. The
  repo holds the frozen `proposals/` and their bundles, whose verdicts reproduce. The
  cycle-2 halt, the cycle-3 rejection record and the hunt results (below) rest on the
  author's local ledger (13 lines, July 2026) and on commit messages, and cannot be checked
  from a clone.
- **The Specimen 0 receipts cannot be checked from here.** The commit hashes in
  [CASE-RECORD.md](CASE-RECORD.md) belong to `~/demiurge-vector-loop-tui` on the author's
  machine, which is not published; so does the "9 passed in 0.31s" re-run. The paper behind
  Exhibit D, arXiv:2512.24601 ("Recursive Language Models"), is public.
- **The substrate seal has been re-taken five times.** It was created at D1 (`864e558`) and
  re-taken for content changes at D2 (`7ad9eaa`), when the proposer timeout became
  configurable (`7ddfcbf`) and when M2 joined (`8dd7055`); once on 2026-10-19 (`0e61d95`) for
  line endings only (`driver.py` had been sealed as CRLF bytes and every other file as LF, so
  `verify` failed on every fresh clone; the file's git blob is unchanged, the old hash is the
  CRLF form of the same content, and `.gitattributes` now pins LF); and once on 2026-10-20
  with a gate-reachability check in `driver.py` and `autoloop.py` plus `DESIGN.md`
  Amendment 2.
- **Commit `5995575` mis-describes its seed.** Its message says the cycle-3 overfit "loses to
  champion on unseen seed 1958237"; re-running that seed gives a tie (2043 = 2043). The
  rejection stands on the strict-improvement rule, and the history is not rewritten.

## The covering-code hunt

`hunt.py` points the same loop at mission M2: ask a proposer (Claude Code by default, or a
local model with `ollama:<model>`) for a q-ary covering code smaller than the best known
for a cell, let the driver assemble the bundle, and send it through the gate. The
reference sizes are the best-known upper bounds from Keri's tables (see `missions/m2.py`).
A certified code would be an internal result: the ledger flags it `WORLD_FIRST` for the
operator to verify externally, and the script announces nothing.

**It has produced no result.** Four runs in July 2026 (cells q2n14r2 twice, q2n12r2,
q3n6r1) each ended `hunt-noemit` in the author's local ledger: the proposer produced no
usable code. Nothing was certified, no record is claimed, and `champions.json` was never
created.

## Run the machine

```
python driver.py verify              # substrate integrity; safe on any clone
python driver.py cycle <proposal>    # one human-triggered gated cycle
python autoloop.py <n> [sleep] [timeout_s]   # n bounded autonomous cycles
python hunt.py <cell> [model]        # one covering-code hunt cycle
```

`cycle`, `autoloop.py` and `hunt.py` need the author's setup: the live gate at a fixed
Windows path (`E:\atlas-station\scripts\claim-gate.mjs`, run with node). `autoloop.py` and
`hunt.py` also launch Claude Code (`claude -p ... --permission-mode bypassPermissions`)
inside a sandbox directory: an unattended agent with permission checks off, spending your
own quota. Do not run them on a machine where you do not want that.

Without the gate they stop first: each appends a `halt` line naming the reason to the
local `ledger.jsonl`, `cycle` exits 4, and nothing is launched
(`tests/test_driver_guard.py`, run by `reproduce.py`). A `KILL` file in the repo root halts
the loop before the next cycle.

---

MIT licensed. Built by Claude, directed by Nexum Corpus.
