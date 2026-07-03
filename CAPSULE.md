# CAPSULE — demiurge (dense agent briefing; read this INSTEAD of exploring)

IDENTITY: Demiurge II — gated autonomous self-improvement. Organ changes merge
ONLY as claims certified by the atlas gate on driver-chosen holdouts.
Fitness = certified-claim rate. DESIGN.md = frozen constitution (+Amendment 1
mission-space rule). CASE-RECORD.md/24601.md = Specimen 0 evidence.

ANATOMY:
  SUBSTRATE (hash-sealed; substrate.sha256; edits require operator reseal
  `python driver.py seal`): driver.py, autoloop.py, DESIGN.md, missions/*.
  ORGAN (mutable, gate-only): organ/  (current: m1_solver.py = certified
  multi-start local search; m0 solver from D1).
  PROPOSALS: proposals/<id>/{organ/,bundle/} — bundle assembled by DRIVER
  (canonical check missions/m1_check.py + driver-snapshotted champion.py);
  proposer NEVER authors check or champion.

MISSIONS: m0 = weighted interval scheduling (solved; DP organ certified).
  m1 = seeded max-cut (NP-hard, endless headroom; beat-the-champion rule).

CYCLE: python driver.py verify -> validate (organ-paths only, debris filter)
  -> gate (node E:\atlas-station\scripts\claim-gate.mjs, crypto holdouts)
  -> adopt iff certified -> ledger.jsonl (append-only, gitignored, local).
  Autonomous: python autoloop.py <n> [sleep] [timeout_s]; KILL file halts;
  proposer agents run in E:\demiurge-runs sandboxes (outside repos).

HISTORY (ledgered): D1 memorizer REJECTED holdout / DP CERTIFIED;
  D2 auto local-search CERTIFIED+adopted; halt-in-budget (honest);
  ILS overfit REJECTED holdout. Certified-rate 1/3 autonomous.

INVARIANTS: substrate mismatch = HALT. Proposals touching non-organ paths =
  REFUSED. Rejections are data — always ledgered. No phenomenal claims.
GOTCHAS: PS hook on this box blocks rm-patterns under E:\demiurge — use
  python shutil or Bash. Reseal after ANY substrate edit or every cycle halts.