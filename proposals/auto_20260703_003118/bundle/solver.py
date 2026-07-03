"""M1 max-cut solver: multi-start (1-opt + 2-opt-adjacent) + ILS.

Key insight: after 1-opt convergence, gain(u)+gain(v) <= 0 for non-adjacent pairs,
so 2-opt only needs to check the |E| edges — O(|E|) per pass, not O(n^2).
This makes full (1-opt + 2-opt) local search only ~3x slower than 1-opt alone,
but it finds strictly better local optima wherever adjacent nodes are "frustrated"
(neither alone benefits from flipping, but flipping both helps).
"""
from __future__ import annotations
import random
import math

_SEED = 7777


def solve(graph):
    n = graph["n"]
    edges = graph["edges"]

    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))

    def gain(mask, v):
        mv = mask[v]
        return sum(w if mv == mask[nb] else -w for nb, w in adj[v])

    def one_opt(mask):
        sc = sum(w for u, v, w in edges if mask[u] != mask[v])
        improved = True
        while improved:
            improved = False
            for v in range(n):
                d = gain(mask, v)
                if d > 0:
                    mask[v] ^= 1
                    sc += d
                    improved = True
        return sc

    def full_search(mask):
        """Alternate 1-opt and 2-opt-adjacent until no combined improvement."""
        sc = one_opt(mask)
        while True:
            improved = False
            for u, v, _ in edges:
                du = gain(mask, u)
                mask[u] ^= 1          # temporary flip
                dv = gain(mask, v)
                mask[u] ^= 1          # restore
                if du + dv > 0:
                    mask[u] ^= 1
                    mask[v] ^= 1
                    sc += du + dv
                    improved = True
            if not improved:
                break
            sc = one_opt(mask)
        return sc

    def run_sa(mask, T0, Tf, steps, rng):
        """Short SA pass to escape local optima; returns (best_mask, best_sc)."""
        sc = sum(w for u, v, w in edges if mask[u] != mask[v])
        best_mask = mask[:]
        best_sc = sc
        T = T0
        factor = (Tf / T0) ** (1.0 / max(steps - 1, 1))
        _exp = math.exp
        _rnd = rng.random
        _rndint = rng.randint
        for _ in range(steps):
            v = _rndint(0, n - 1)
            mv = mask[v]
            d = sum(w if mv == mask[nb] else -w for nb, w in adj[v])
            if d >= 0 or _rnd() < _exp(d / T):
                mask[v] ^= 1
                sc += d
                if sc > best_sc:
                    best_sc = sc
                    best_mask = mask[:]
            T *= factor
        return best_mask, best_sc

    rng = random.Random(_SEED)
    best_mask = [0] * n
    best_score = -1

    # Greedy starting point
    greedy = [0] * n
    for node in range(n):
        d_in = sum(w for nb, w in adj[node] if not greedy[nb])
        d_out = sum(w for nb, w in adj[node] if greedy[nb])
        greedy[node] = 1 if d_in >= d_out else 0
    sc = full_search(greedy)
    if sc > best_score:
        best_score = sc
        best_mask = greedy[:]

    # Multi-start phase (match champion coverage + 2-opt polish)
    for _ in range(700):
        mask = [rng.randint(0, 1) for _ in range(n)]
        sc = full_search(mask)
        if sc > best_score:
            best_score = sc
            best_mask = mask[:]

    # SA phase from best solution found — escape local optima
    for _ in range(5):
        m, s = run_sa(best_mask[:], T0=30.0, Tf=0.05, steps=20000, rng=rng)
        s2 = full_search(m)
        if s2 > best_score:
            best_score = s2
            best_mask = m[:]

    # ILS phase: perturb best and re-search
    for _ in range(300):
        perturbed = best_mask[:]
        for _ in range(5):
            perturbed[rng.randint(0, n - 1)] ^= 1
        sc = full_search(perturbed)
        if sc > best_score:
            best_score = sc
            best_mask = perturbed[:]

    return [i for i in range(n) if best_mask[i]]
