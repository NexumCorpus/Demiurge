"""Re-derive Demiurge's ledgered verdicts from a fresh clone. Standard library only.

    python reproduce.py               # 5 fresh holdout seeds per proposal
    python reproduce.py --holdout 2   # the live driver's count (see the note below)

What it does, in order:
  1. substrate integrity (the same check as `python driver.py verify`)
  2. the M2 anchor tests in tests/test_m2.py (hand-derived ground truths)
  3. every gated proposal in proposals/ through the gate's rule: its bundle's check.py
     must exit 0 on every claimed seed AND on fresh holdout seeds it never saw
     (seeds from `secrets`, as driver.py chooses them). The verdict must match the
     one recorded in git history.

What it does not do: the real gate is atlas-station's grader (node), which also writes
the claim into a ledger; this script mirrors its decision rule, not its bookkeeping.
It also does not re-run the proposer agents that wrote the organs.

A finding this script surfaced (2026-10-19): the cycle-3 overfit strictly beats its champion on
about 1 random seed in 8 (5/40 measured), so with the live driver's 2 holdout seeds it would have
been certified roughly 1.6% of the time. Its rejection was correct, but 2 holdouts is a thin
margin for a near-tie proposal. Hence 5 here (about 0.003%).
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOLDOUT_RANGE = 10_000_000

# Verdicts as recorded in git history (commit subjects in parentheses).
EXPECTED = {
    "p001-dp-scheduler": True,       # 82317f2 organ: adopt p001-dp-scheduler
    "p002-memorizer": False,         # 864e558 D1: gate kills gaming
    "auto_20260702_233403": True,    # 8b6717d organ: adopt auto_20260702_233403
    "auto_20260703_003118": False,   # 5995575 D2 cycle 3: honest overfit REJECTED on holdout
}


def substrate_ok() -> bool:
    sys.path.insert(0, str(HERE))
    import driver
    return driver.verify()


def m2_anchors() -> tuple[int, int]:
    import importlib.util
    spec = importlib.util.spec_from_file_location("test_m2", HERE / "tests" / "test_m2.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    tests = [getattr(mod, n) for n in sorted(dir(mod)) if n.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:  # noqa: BLE001 - report every anchor, then decide
            failed += 1
            print(f"  FAIL {t.__name__}: {e!r}")
    return len(tests), failed


def run_check(bundle: Path, check: list[str], seed: int) -> tuple[int, str]:
    # The bundled check.py files prepend the author's original checkout path to sys.path;
    # PYTHONPATH makes the same `missions` package importable from wherever this clone lives.
    env = dict(os.environ, PYTHONPATH=str(HERE), PYTHONDONTWRITEBYTECODE="1")
    argv = [sys.executable if a == "python" else a.replace("{seed}", str(seed)) for a in check]
    p = subprocess.run(argv, cwd=bundle, env=env, capture_output=True, text=True, timeout=600)
    last = (p.stdout.strip().splitlines() or [p.stderr.strip()[-200:]])[-1]
    return p.returncode, last


def gate(bundle: Path, n_holdout: int) -> tuple[bool, str]:
    claim = json.loads((bundle / "claim.json").read_text(encoding="utf-8"))
    claimed = claim["claimed_seeds"]
    holdouts: list[int] = []
    while len(holdouts) < n_holdout:
        s = secrets.randbelow(HOLDOUT_RANGE)
        if s not in claimed and s not in holdouts:
            holdouts.append(s)
    for kind, seeds in (("claimed", claimed), ("holdout", holdouts)):
        for s in seeds:
            code, line = run_check(bundle, claim["check"], s)
            print(f"    {kind:7} {line}  exit {code}")
            if code != 0:
                return False, f"{kind} seed {s} failed"
    return True, f"reproduced on {claimed}, survived holdout {holdouts}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--holdout", type=int, default=5, help="fresh holdout seeds per proposal")
    args = ap.parse_args()
    t0 = time.time()
    ok = True

    print("1. substrate")
    if not substrate_ok():
        print("REPRODUCE: FAIL (substrate mismatch; a fresh clone should never hit this)")
        return 1

    print("2. M2 anchor tests")
    n, failed = m2_anchors()
    print(f"  {n - failed}/{n} pass")
    ok &= failed == 0

    print("3. gated proposals (claimed seeds, then fresh holdouts)")
    for name, expected in EXPECTED.items():
        bundle = HERE / "proposals" / name / "bundle"
        certified, why = gate(bundle, args.holdout)
        verdict = "CERTIFIED" if certified else "REJECTED"
        match = certified == expected
        ok &= match
        print(f"  {'ok  ' if match else 'MISMATCH'} {name}: {verdict} ({why})")

    print(f"REPRODUCE: {'PASS' if ok else 'FAIL'} in {time.time() - t0:.1f} s")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
