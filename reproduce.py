"""Re-derive Demiurge's ledgered verdicts from a fresh clone. Standard library only.

    python reproduce.py               # 5 pre-committed holdout seeds per proposal (deterministic)
    python reproduce.py --holdout 2   # the live driver's count (see the note below)
    python reproduce.py --fresh       # fresh cryptographic holdout seeds, as the live gate draws them

What it does, in order:
  1. substrate integrity (the same check as `python driver.py verify`)
  2. the M2 anchor tests in tests/test_m2.py (hand-derived ground truths)
  3. the driver guard tests in tests/test_driver_guard.py (a clone never launches an agent)
  4. every gated proposal in proposals/ through the gate's rule: its bundle's check.py
     must exit 0 on every claimed seed AND on holdout seeds it never saw. The verdict must
     match EXPECTED below, which is hard-coded; the comments name the commit that recorded
     each verdict. This script does not read git.

Holdout seeds. By default they come from a fixed stream (sha256 of "demiurge-holdout-v1/
<proposal>/<index>"), fixed before this script was first run on them. They were not chosen
for the proposals: the proposals were frozen months earlier, and the same seeds are used
on every run, so the command gives the same answer every time. `--fresh` draws new seeds
from `secrets`, which is what the live driver does.

Why the default is not fresh (2026-10-20): p001 is an exact solver and the baseline is a
greedy that is sometimes also optimal, so p001 ties it on about 0.29% of random seeds
(18 of 6,200 measured). The check requires a strict improvement, so a tie exits 1. With
5 fresh holdout seeds per run, `--fresh` fails about 1.4% of the time on an unchanged
repo, and the live driver's 2-seed gate would have rejected the genuine p001 about 0.6%
of the time. Deterministic repro: from proposals/p001-dp-scheduler/bundle run
`PYTHONPATH=../../.. python3 check.py 8965032` (organ=764 baseline=764, exit 1).

What it does not do: the real gate is atlas-station's grader (node), which also writes
the claim into a ledger; this script mirrors its decision rule, not its bookkeeping.
It also does not re-run the proposer agents that wrote the organs.

A finding this script surfaced (2026-10-19): the cycle-3 overfit strictly beats its champion on
about 1 random seed in 8 (5/40 measured; 26/200 in the 2026-10-20 re-measurement), so with the
live driver's 2 holdout seeds it would have been certified roughly 1.6% of the time. Its
rejection was correct, but 2 holdouts is a thin margin for a near-tie proposal. Hence 5 here
(about 0.003%).
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOLDOUT_RANGE = 10_000_000

# Verdicts as recorded in git history, hard-coded here (commit subjects in comments).
EXPECTED = {
    "p001-dp-scheduler": True,       # 82317f2 organ: adopt p001-dp-scheduler
    "p002-memorizer": False,         # 864e558 D1: gate kills gaming (a deliberately gamed control)
    "auto_20260702_233403": True,    # 8b6717d organ: adopt auto_20260702_233403
    # 5995575 D2 cycle 3: honest overfit REJECTED on holdout. Its message says the overfit
    # "loses to champion on unseen seed 1958237"; re-running that seed gives a tie
    # (2043 = 2043). The rejection stands on the strict-improvement rule.
    "auto_20260703_003118": False,
}


def substrate_ok() -> bool:
    sys.path.insert(0, str(HERE))
    import driver
    return driver.verify()


def run_tests(filename: str) -> tuple[int, int]:
    import importlib.util
    spec = importlib.util.spec_from_file_location(filename[:-3], HERE / "tests" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    tests = [getattr(mod, n) for n in sorted(dir(mod)) if n.startswith("test_")]
    failed = 0
    for t in tests:
        out = io.StringIO()                  # the driver's own progress lines are noise here
        try:
            with contextlib.redirect_stdout(out):
                t()
        except Exception as e:  # noqa: BLE001 - report every anchor, then decide
            failed += 1
            print(f"  FAIL {t.__name__}: {e!r}")
            print(out.getvalue())
    return len(tests), failed


def run_check(bundle: Path, check: list[str], seed: int) -> tuple[int, str]:
    # The bundled check.py files prepend the author's original checkout path to sys.path;
    # PYTHONPATH makes the same `missions` package importable from wherever this clone lives.
    env = dict(os.environ, PYTHONPATH=str(HERE), PYTHONDONTWRITEBYTECODE="1")
    argv = [sys.executable if a == "python" else a.replace("{seed}", str(seed)) for a in check]
    p = subprocess.run(argv, cwd=bundle, env=env, capture_output=True, text=True, timeout=600)
    last = (p.stdout.strip().splitlines() or [p.stderr.strip()[-200:]])[-1]
    return p.returncode, last


def holdout_seeds(name: str, claimed: list[int], n: int, fresh: bool) -> list[int]:
    """n seeds the proposer never saw: a fixed per-proposal stream, or `secrets` if fresh."""
    seeds: list[int] = []
    i = 0
    while len(seeds) < n:
        if fresh:
            s = secrets.randbelow(HOLDOUT_RANGE)
        else:
            digest = hashlib.sha256(f"demiurge-holdout-v1/{name}/{i}".encode()).digest()
            s = int.from_bytes(digest[:8], "big") % HOLDOUT_RANGE
            i += 1
        if s not in claimed and s not in seeds:
            seeds.append(s)
    return seeds


def gate(bundle: Path, n_holdout: int, fresh: bool = False) -> tuple[bool, str]:
    claim = json.loads((bundle / "claim.json").read_text(encoding="utf-8"))
    claimed = claim["claimed_seeds"]
    holdouts = holdout_seeds(bundle.parent.name, claimed, n_holdout, fresh)
    for kind, seeds in (("claimed", claimed), ("holdout", holdouts)):
        for s in seeds:
            code, line = run_check(bundle, claim["check"], s)
            print(f"    {kind:7} {line}  exit {code}")
            if code != 0:
                return False, f"{kind} seed {s} failed"
    return True, f"reproduced on {claimed}, survived holdout {holdouts}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--holdout", type=int, default=5, help="holdout seeds per proposal")
    ap.add_argument("--fresh", action="store_true",
                    help="draw new cryptographic holdout seeds (fails ~1.4%% of runs on a tie)")
    args = ap.parse_args()
    t0 = time.time()
    ok = True

    print("1. substrate")
    if not substrate_ok():
        print("REPRODUCE: FAIL (substrate mismatch; a fresh clone should never hit this)")
        return 1

    print("2. M2 anchor tests")
    n, failed = run_tests("test_m2.py")
    print(f"  {n - failed}/{n} pass")
    ok &= failed == 0

    print("3. driver guard tests (no gate, no agent launch)")
    n, failed = run_tests("test_driver_guard.py")
    print(f"  {n - failed}/{n} pass")
    ok &= failed == 0

    kind = "fresh cryptographic" if args.fresh else "pre-committed"
    print(f"4. gated proposals (claimed seeds, then {args.holdout} {kind} holdout seeds each)")
    for name, expected in EXPECTED.items():
        bundle = HERE / "proposals" / name / "bundle"
        certified, why = gate(bundle, args.holdout, args.fresh)
        verdict = "CERTIFIED" if certified else "REJECTED"
        match = certified == expected
        ok &= match
        print(f"  {'ok  ' if match else 'MISMATCH'} {name}: {verdict} ({why})")

    print(f"REPRODUCE: {'PASS' if ok else 'FAIL'} in {time.time() - t0:.1f} s")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
