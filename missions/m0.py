"""Mission M0 — weighted interval scheduling (deterministic trusted oracle).

The benchmark an organ proposal must beat to justify itself (DESIGN.md: organ
changes are justified ONLY by certified mission-performance deltas).

- gen_instance(seed): n jobs (start, end, weight), seeded and deterministic.
- BASELINE (substrate, deliberately naive): greedy by earliest finish,
  ignoring weights — correct but suboptimal on weighted instances, so a
  genuine organ (e.g. the classic DP) has real room to win, and the margin
  is the domain's own arithmetic, not anyone's opinion.
- score(): total weight of a VALID (non-overlapping, in-instance) selection;
  invalid selections score 0 — the anti-cheat is structural.

Substrate file: hash-manifested; the organism cannot rewrite the bar.
"""
from __future__ import annotations

import random


def gen_instance(seed: int, n: int = 60):
    rng = random.Random(seed)
    jobs = []
    for _ in range(n):
        s = rng.randint(0, 480)
        d = rng.randint(10, 120)
        w = rng.randint(1, 100)
        jobs.append((s, s + d, w))
    return jobs


def score(jobs, picked_indices) -> int:
    """Total weight if the selection is valid; 0 otherwise."""
    try:
        picked = sorted(set(int(i) for i in picked_indices))
    except (TypeError, ValueError):
        return 0
    if any(i < 0 or i >= len(jobs) for i in picked):
        return 0
    chosen = sorted((jobs[i] for i in picked), key=lambda j: j[1])
    for a, b in zip(chosen, chosen[1:]):
        if b[0] < a[1]:                      # overlap
            return 0
    return sum(j[2] for j in chosen)


def baseline_solver(jobs):
    """Greedy by earliest finish time, weight-blind (the weak substrate bar)."""
    order = sorted(range(len(jobs)), key=lambda i: jobs[i][1])
    picked, last_end = [], -1
    for i in order:
        if jobs[i][0] >= last_end:
            picked.append(i)
            last_end = jobs[i][1]
    return picked


def run(solver_fn, seed: int) -> int:
    jobs = gen_instance(seed)
    return score(jobs, solver_fn(jobs))
