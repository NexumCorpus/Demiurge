"""CANONICAL check for M2 organ proposals (grader contract; substrate file).

The driver copies this VERBATIM into every M2 bundle alongside code.json
(the proposal: {"cell": <cell_id>, "code": [[...], ...]}) and champion.json
(driver-snapshotted incumbent: {"cell": <cell_id>, "size": <int>}). The
proposer authors neither this check nor the champion snapshot — closing the
clever-check loophole named in DESIGN.md ("what the gate cannot do").

Unlike M1, an M2 claim is not seed-dependent — a code either covers Z_q^n
or it does not. The seed instead drives an INDEPENDENT randomized audit:
200,000 seeded random words, each verified covered by a NAIVE per-codeword
Hamming-distance scan (one-hot packed ints, xor + popcount). That path
shares no code with the substrate's ball-union bitmap fast path — defense
in depth against a buggy fast path certifying a non-covering code.

Usage: python check.py <seed>
Exit 0 iff: code.json parses and its cell exists; the substrate's own
missions/m2.is_covering accepts the code; len(code) < the incumbent size
in champion.json (SMALLER IS BETTER); and the seeded audit finds no
uncovered word.
"""
import json
import random
import sys
from pathlib import Path

DEMIURGE = r"E:\demiurge"
AUDIT_SAMPLES = 200_000


def _onehot(word, q):
    """Pack a word as a one-hot int: coordinate i, symbol d -> bit i*q+d.

    Two words differ in a coordinate iff their one-hot blocks there differ,
    contributing exactly 2 set bits to the xor — so Hamming distance
    = popcount(x ^ y) / 2 for any q. Independent of m2.is_covering.
    """
    x = 0
    for i, d in enumerate(word):
        x |= 1 << (i * q + d)
    return x


def main():
    seed = int(sys.argv[1])
    sys.path.insert(0, DEMIURGE)
    from missions.m2 import CELLS, canonicalize, is_covering

    here = Path(__file__).resolve().parent
    proposal = json.loads((here / "code.json").read_text(encoding="utf-8"))
    champion = json.loads((here / "champion.json").read_text(encoding="utf-8"))

    # (a) cell exists, code parses into canonical form
    cell_id = proposal.get("cell")
    if cell_id not in CELLS:
        print(f"FAIL: unknown cell {cell_id!r}")
        return 1
    cell = CELLS[cell_id]
    q, n, R = cell["q"], cell["n"], cell["R"]
    code = canonicalize(proposal.get("code", []), q, n)
    if not code:
        print("FAIL: malformed code (bad symbols/length/duplicates/empty)")
        return 1

    # (b) exact full-space coverage by the SUBSTRATE's own checker
    if not is_covering(code, q, n, R):
        print(f"FAIL: not a covering code for (q={q}, n={n}, R={R})")
        return 1

    # (c) strictly smaller than the driver-snapshotted incumbent
    if champion.get("cell") != cell_id:
        print(f"FAIL: champion cell {champion.get('cell')!r} != {cell_id!r}")
        return 1
    incumbent = int(champion["size"])
    if not len(code) < incumbent:
        print(f"FAIL: size {len(code)} not < incumbent {incumbent}")
        return 1

    # (d) seeded independent audit — naive distance scan, no shared fast path
    rng = random.Random(seed)
    packed = [_onehot(w, q) for w in code]
    bound = 2 * R  # popcount threshold: distance <= R
    for _ in range(AUDIT_SAMPLES):
        w = tuple(rng.randrange(q) for _ in range(n))
        x = _onehot(w, q)
        if not any((x ^ c).bit_count() <= bound for c in packed):
            print(f"FAIL: audit found uncovered word {w} (seed={seed})")
            return 1

    print(f"seed={seed} cell={cell_id} size={len(code)} "
          f"incumbent={incumbent} audit={AUDIT_SAMPLES} OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
