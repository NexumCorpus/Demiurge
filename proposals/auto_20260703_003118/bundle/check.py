"""CANONICAL check for M1 organ proposals (grader contract; substrate file).

The driver copies this VERBATIM into every M1 bundle alongside solver.py
(the proposal) and champion.py (driver-snapshotted incumbent). The proposer
authors neither this check nor the champion — closing the clever-check
loophole named in DESIGN.md ("what the gate cannot do").

Usage: python check.py <seed>
Exit 0 iff the proposal OUTSCORES the champion on the mission's own
generator/scorer at that seed.
"""
import importlib.util
import sys
from pathlib import Path

DEMIURGE = r"E:\demiurge"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    seed = int(sys.argv[1])
    sys.path.insert(0, DEMIURGE)
    from missions.m1 import run

    here = Path(__file__).resolve().parent
    proposal = _load(here / "solver.py", "organ_proposal")
    champion = _load(here / "champion.py", "organ_champion")

    a = run(proposal.solve, seed)
    b = run(champion.solve, seed)
    print(f"seed={seed} proposal={a} champion={b}")
    return 0 if a > b else 1


if __name__ == "__main__":
    sys.exit(main())
