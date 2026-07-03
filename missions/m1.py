"""Mission M1 — seeded weighted max-cut (open improvement ladder).

Unlike M0 (solved exactly by one DP organ), max-cut is NP-hard: no organ is
ever final, so the autonomous loop always has honest headroom — local search
beats greedy, annealing beats local search, and so on. Fitness stays real
forever.

- gen_graph(seed): 60 nodes, ~15% weighted edges, deterministic.
- solve(graph) -> iterable of node ids (one side of the cut).
- score(): total weight of edges crossing the cut. Unknown nodes are
  ignored (structural anti-cheat: you cannot invent vertices).
- BASELINE (substrate, deliberately modest): single greedy pass.

Substrate file: hash-manifested. Organ proposals are graded by the CANONICAL
check (missions/m1_check.py) against a DRIVER-snapshotted champion — the
proposer authors neither.
"""
from __future__ import annotations

import random

N_NODES = 60
EDGE_P = 0.15


def gen_graph(seed: int):
    rng = random.Random(seed)
    edges = []
    for u in range(N_NODES):
        for v in range(u + 1, N_NODES):
            if rng.random() < EDGE_P:
                edges.append((u, v, rng.randint(1, 20)))
    return {"n": N_NODES, "edges": edges}


def score(graph, side) -> int:
    try:
        s = {int(x) for x in side if 0 <= int(x) < graph["n"]}
    except (TypeError, ValueError):
        return 0
    return sum(w for u, v, w in graph["edges"] if (u in s) != (v in s))


def baseline_solver(graph):
    """One greedy pass: place each node on the side that currently cuts more."""
    side = set()
    for node in range(graph["n"]):
        gain_in = sum(w for u, v, w in graph["edges"]
                      if (u == node and v not in side)
                      or (v == node and u not in side))
        gain_out = sum(w for u, v, w in graph["edges"]
                       if (u == node and v in side)
                       or (v == node and u in side))
        if gain_in >= gain_out:
            side.add(node)
    return side


def run(solver_fn, seed: int) -> int:
    graph = gen_graph(seed)
    return score(graph, solver_fn(graph))
