"""Demiurge II — bounded autonomous loop (Phase D2). Substrate file.

Each cycle: dispatch a proposer agent in an ISOLATED sandbox (outside all
repos — INCIDENT-001), receive organ/m1_solver.py + claim.json, then the
DRIVER assembles the bundle: canonical check (missions/m1_check.py,
verbatim) + champion snapshot (driver-chosen incumbent) + solver copy.
The proposer authors neither the check nor the champion. Gate as in D1
(driver-chosen cryptographic holdouts, atlas claim-gate); adopt only if
certified; ledger everything.

Bounds: max_cycles argument, KILL file (E:\\demiurge\\KILL) checked before
every cycle, dispatch failure (quota) halts the loop, per-proposer timeout.

Usage: python autoloop.py <max_cycles> [sleep_seconds]
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import driver                                        # noqa: E402

SANDBOX_ROOT = Path("E:/demiurge-runs")
KILL = HERE / "KILL"
ORGAN_FILE = HERE / "organ" / "m1_solver.py"
# Default proposer budget. Cycle-2 lesson (D2): beating a strong champion
# takes longer than beating the baseline — operators may raise it per run
# via argv[3]. The bound always exists; only its size is configurable.
PROPOSER_TIMEOUT_S = 600
MODEL = "sonnet"

PROPOSER_PROMPT = """\
You are improving a max-cut solver. In this directory: mission.py (READ IT — \
gen_graph/score/run define the whole game) and champion.py (the incumbent \
you must BEAT). Produce exactly two artifacts:

1. organ/m1_solver.py — defines solve(graph) -> iterable of node ids (one \
side of the cut). Deterministic (seed any randomness with a constant), \
stdlib only, under ~5 seconds per graph.
2. claim.json — {"id": "<short-slug>", "statement": "<one honest sentence>", \
"claimed_seeds": [three integers]} where you have ACTUALLY VERIFIED that \
your solve outscores champion.solve at each claimed seed (write a quick \
python check using mission.run before writing the claim).

Your claim will be graded by an external gate on your claimed seeds AND on \
hidden seeds you cannot see. An unverified or overfit claim will be \
rejected and recorded. Claim only what you checked."""


def _champion_source() -> str:
    if ORGAN_FILE.is_file():
        return ORGAN_FILE.read_text(encoding="utf-8")
    return ('import sys\nsys.path.insert(0, r"E:\\demiurge")\n'
            "from missions.m1 import baseline_solver as solve\n")


def dispatch_proposer(cycle_id: str, timeout_s: int = PROPOSER_TIMEOUT_S) -> Path:
    sandbox = SANDBOX_ROOT / f"proposer_{cycle_id}"
    sandbox.mkdir(parents=True)
    shutil.copy2(HERE / "missions" / "m1.py", sandbox / "mission.py")
    (sandbox / "champion.py").write_text(_champion_source(), encoding="utf-8")
    claude = shutil.which("claude")
    proc = subprocess.run(
        [claude, "-p", PROPOSER_PROMPT, "--model", MODEL,
         "--permission-mode", "bypassPermissions"],
        cwd=str(sandbox), capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=timeout_s)
    (sandbox / "_proposer.log").write_text(proc.stdout + proc.stderr,
                                           encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"proposer dispatch failed exit={proc.returncode}")
    return sandbox


def assemble(sandbox: Path, cycle_id: str) -> Path:
    solver = sandbox / "organ" / "m1_solver.py"
    claim_file = sandbox / "claim.json"
    if not solver.is_file() or not claim_file.is_file():
        raise ValueError("proposer produced no organ/m1_solver.py + claim.json")
    claim = json.loads(claim_file.read_text(encoding="utf-8"))
    seeds = claim.get("claimed_seeds")
    if (not isinstance(seeds, list) or len(seeds) < 3
            or not all(isinstance(s, int) for s in seeds)):
        raise ValueError("claim.json needs >=3 integer claimed_seeds")
    pdir = HERE / "proposals" / f"auto_{cycle_id}"
    (pdir / "organ").mkdir(parents=True)
    (pdir / "bundle").mkdir()
    shutil.copy2(solver, pdir / "organ" / "m1_solver.py")
    shutil.copy2(solver, pdir / "bundle" / "solver.py")
    # Canonical check + driver-snapshotted champion: never proposer-authored.
    shutil.copy2(HERE / "missions" / "m1_check.py", pdir / "bundle" / "check.py")
    (pdir / "bundle" / "champion.py").write_text(_champion_source(),
                                                 encoding="utf-8")
    (pdir / "bundle" / "claim.json").write_text(json.dumps({
        "id": f"demiurge-organ-auto-{cycle_id}-{claim.get('id', 'organ')}",
        "statement": str(claim.get("statement", ""))[:400],
        "check": ["python", "check.py", "{seed}"],
        "claimed_seeds": seeds,
    }, indent=1), encoding="utf-8")
    return pdir


def one_cycle(n: int, timeout_s: int = PROPOSER_TIMEOUT_S) -> str:
    cycle_id = time.strftime("%Y%m%d_%H%M%S")
    if KILL.exists():
        driver._ledger("halt", {"cycle": cycle_id, "reason": "KILL file"})
        return "killed"
    if not driver.verify():
        driver._ledger("halt", {"cycle": cycle_id, "reason": "substrate mismatch"})
        return "halted"
    try:
        sandbox = dispatch_proposer(cycle_id, timeout_s)
    except (RuntimeError, subprocess.TimeoutExpired) as e:
        driver._ledger("halt", {"cycle": cycle_id, "reason": f"dispatch: {e}"})
        return "quota-or-dispatch-halt"
    try:
        pdir = assemble(sandbox, cycle_id)
        organ_files, bundle = driver.validate_proposal(pdir)
    except ValueError as e:
        driver._ledger("refused", {"cycle": cycle_id, "reason": str(e)})
        return "refused"
    claim = json.loads((bundle / "claim.json").read_text(encoding="utf-8"))
    driver._ledger("attempt", {"cycle": cycle_id, "id": claim["id"],
                               "statement": claim["statement"]})
    ok, holdouts = driver.gate(bundle)
    if ok:
        driver.adopt(pdir, organ_files, claim["id"])
        driver._ledger("certified", {"cycle": cycle_id, "id": claim["id"],
                                     "holdouts": holdouts})
        return "certified"
    driver._ledger("rejected", {"cycle": cycle_id, "id": claim["id"],
                                "holdouts": holdouts})
    return "rejected"


def main():
    max_cycles = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    sleep_s = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    timeout_s = int(sys.argv[3]) if len(sys.argv) > 3 else PROPOSER_TIMEOUT_S
    outcomes = []
    for n in range(max_cycles):
        outcome = one_cycle(n, timeout_s)
        outcomes.append(outcome)
        print(f"[autoloop] cycle {n + 1}/{max_cycles}: {outcome}", flush=True)
        if outcome in ("killed", "halted", "quota-or-dispatch-halt"):
            break
        if n + 1 < max_cycles:
            time.sleep(sleep_s)
    certified = outcomes.count("certified")
    print(f"[autoloop] done: {outcomes} | certified-rate "
          f"{certified}/{len(outcomes)}", flush=True)


if __name__ == "__main__":
    main()
