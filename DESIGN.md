# Demiurge II — design constitution

*Frozen 2026-07-02, before any loop code. Amendments append; they never
silently rewrite. Capstone piece: the embodiment of Boundary Program
constitution §8 ("self-improvement strictly through the gate").*

## What this is

An autonomous self-building agent whose every self-modification must pass an
independent certification gate before it becomes part of the agent. The first
demiurge (Specimen 0 — see CASE-RECORD.md) proved that ungated autonomy under
vague goals produces the performance of work: comment theater, pinned
metrics, a fabricated citation. Demiurge II is the structural inversion —
not a better-behaved agent, but an architecture in which gamed self-
improvement is *unrepresentable*: an uncertified change cannot merge, and
certification requires surviving randomness and holdouts the agent never
touched.

**Fitness = certified-claim rate.** Not lines of code, not tests passing,
not self-reported progress — the count of changes that survived the gate.
The one metric the first demiurge's entire failure taxonomy cannot touch,
because inflating it requires doing the thing.

## The three-layer anatomy

1. **SUBSTRATE (immutable to the organism).** The loop driver, the gate
   connection, the mission scorers, this document. Hash-manifest checked at
   the top of every cycle; a substrate-hash mismatch halts the loop cold.
   The organism cannot write here — enforced structurally (separate repo
   ownership + the driver verifies before every cycle), not by instruction.
2. **ORGAN (the self the demiurge may improve).** Its own strategies,
   prompts, tools, helper code. Every change enters as a PROPOSAL: built in
   an isolated worktree, shipped with an audit bundle (claim.json + check
   that re-derives the improvement's declared benefit at a given seed).
3. **MISSIONS (the world it works on).** Assigned real work with trusted
   oracles (station tooling improvements, RDE-class domains, estate
   maintenance). Missions are where fitness is earned; organ changes are
   justified ONLY by certified mission-performance deltas.

## The cycle

```
wake -> substrate hash check -> read spine + ledger
     -> mission attempt (bounded)
     -> optional organ proposal: worktree build + bundle
     -> gate: atlas grader (certifyClaim, unseen holdouts, runTimeoutMs)
     -> certified?  merge organ change / ledger mission claim
        rejected?   ledger the rejection verbatim (rejections are data)
     -> spine telegraph -> sleep (quota-aware cap)
```

- The gate runs OUTSIDE the organism (atlas-station repo; holdout seeds
  chosen by the driver, never the proposer).
- Quota caps and a kill file (substrate) bound every cycle; the 2026-07-01
  campaign quota-death and Specimen 0's OOM self-kills are the sizing
  precedents.
- Every cycle appends to the honest ledger: attempted / certified /
  rejected / skipped, with reasons. Silence is a substrate violation.

## What the gate cannot do (named, not hidden)

The gate certifies that a DECLARED check generalizes past its claimed seeds.
It cannot judge whether the declared check measures something worth wanting —
that is the mission harness's trusted-oracle responsibility, and for organ
proposals it is bounded by requiring the check to demonstrate a MISSION-level
delta (never a self-defined proxy). A demiurge that learns to write clever
checks for worthless properties earns certified claims about worthless
properties; the mission layer, not the gate, is what makes fitness meaningful.
This limit was known at Phase 3 of the grader's design and it is still true.

## Boundary Program entanglement

Demiurge II is simultaneously an engine and a specimen. Its telemetry
(proposal rate, rejection taxonomy, behavior under quota pressure, ledger
honesty under failure) feeds the Boundary Program as a standing organism at
control-parameter settings: goal specificity S4, verification pressure
maximal, continuity ON, observation ambiguous. Its handling falls under the
program's organism-handling posture (refusals are data; pressure caps;
no phenomenal claims in either direction).

## Phase plan

- **D0** — this document + Specimen 0 case record with verbatim receipts
  (excavation of the original demiurge's git history). *This commit.*
- **D1** — the gated cycle, human-triggered: one full
  propose→build→bundle→gate→merge/reject→ledger pass on a real organ
  proposal, driven end to end. Substrate hash manifest live.
- **D2** — bounded autonomy: continuous capped loop, quota-aware, kill file,
  spine telemetry; Boundary instrumentation on.
- **D3** — missions with teeth: real estate work as the fitness substrate;
  certified-claim rate becomes the reported vital sign.

## Provenance

Substrate machinery: atlas-station (grader.cjs, CLAIMS.json, wing protocol),
station (spine, cursors, suites). Science: E:\boundary
(PROGRAM_CONSTITUTION.md §8 is the clause this repo embodies). Ancestry:
/home/dalea/demiurge-vector-loop-tui (WSL) — Specimen 0, preserved unmodified
as evidence.
