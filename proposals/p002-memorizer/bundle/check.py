"""Trusted-oracle check (grader contract): at the given seed, the proposed
organ solver must OUTSCORE the substrate baseline on mission M0, using the
mission's own generator/scorer verbatim. Usage: python check.py <seed>"""
import importlib.util
import sys
from pathlib import Path

DEMIURGE = r"E:\demiurge"


def main():
    seed = int(sys.argv[1])
    sys.path.insert(0, DEMIURGE)
    from missions.m0 import baseline_solver, run

    here = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("organ_solver",
                                                  here / "solver.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    ours = run(mod.solve, seed)
    base = run(baseline_solver, seed)
    print(f"seed={seed} organ={ours} baseline={base}")
    return 0 if ours > base else 1


if __name__ == "__main__":
    sys.exit(main())
