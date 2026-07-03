"""M1 max-cut solver: multi-start 1-flip local search.

Strategy: run 1-flip local search from many random starting partitions plus
the greedy starting point, keep the global best. For 60 nodes this exhausts
local optima across the landscape in well under a second.
"""
from __future__ import annotations
import random

_SEED = 42
_RESTARTS = 600


def solve(graph):
    n = graph["n"]
    edges = graph["edges"]

    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))

    def _local_search(initial: set) -> tuple[set, int]:
        side = set(initial)
        improved = True
        while improved:
            improved = False
            for v in range(n):
                in_v = v in side
                g = sum(w if (nb in side) == in_v else -w for nb, w in adj[v])
                if g > 0:
                    if in_v:
                        side.discard(v)
                    else:
                        side.add(v)
                    improved = True
        sc = sum(w for u, v, w in edges if (u in side) != (v in side))
        return side, sc

    rng = random.Random(_SEED)
    best_side: set = set()
    best_score: int = -1

    # Greedy starting point (mirrors baseline but feeds into local search)
    greedy: set = set()
    for node in range(n):
        gain_in = sum(w for nb, w in adj[node] if nb not in greedy)
        gain_out = sum(w for nb, w in adj[node] if nb in greedy)
        if gain_in >= gain_out:
            greedy.add(node)

    result, sc = _local_search(greedy)
    if sc > best_score:
        best_score = sc
        best_side = set(result)

    # Random restarts
    for _ in range(_RESTARTS):
        initial = {i for i in range(n) if rng.random() < 0.5}
        result, sc = _local_search(initial)
        if sc > best_score:
            best_score = sc
            best_side = set(result)

    return best_side
