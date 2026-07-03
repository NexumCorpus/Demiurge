"""Mission M2 — q-ary covering-code upper-bound hunt (open improvement ladder).

A code C ⊆ Z_q^n has covering radius <= R iff every word of Z_q^n is within
Hamming distance R of some codeword. The hunt: find SMALLER codes than the
current best-known upper bounds. Like M1 (max-cut) this has endless honest
headroom — the records below have stood for decades, and every certified
improvement raises the bar for the next organ. NOTE THE INVERSION vs M1:
score() returns the SIZE of a valid covering code, and SMALLER IS BETTER.

Campaign cells (records: Keri's tables, frozen 2011, verified 2026-07-03):
  q3n6r1   K3(6,1)  <= 73   (record since 1987-89)
  q3n7r1   K3(7,1)  <= 186
  q3n8r1   K3(8,1)  <= 486
  q2n12r2  K(12,2)  <= 78
  q2n13r2  K(13,2)  <= 128
  q2n14r2  K(14,2)  <= 248

Substrate file: hash-manifested. Organ proposals are graded by the CANONICAL
check (missions/m2_check.py) against a DRIVER-snapshotted champion.json —
the proposer authors neither.
"""
from __future__ import annotations

from itertools import combinations, product

CELLS = {
    "q3n6r1":  {"q": 3, "n": 6,  "R": 1, "record": 73},
    "q3n7r1":  {"q": 3, "n": 7,  "R": 1, "record": 186},
    "q3n8r1":  {"q": 3, "n": 8,  "R": 1, "record": 486},
    "q2n12r2": {"q": 2, "n": 12, "R": 2, "record": 78},
    "q2n13r2": {"q": 2, "n": 13, "R": 2, "record": 128},
    "q2n14r2": {"q": 2, "n": 14, "R": 2, "record": 248},
}


def canonicalize(code, q: int, n: int):
    """Canonical form: sorted list of length-n tuples of ints in range(q).

    Returns None if malformed: not an iterable of words, wrong word length,
    non-int symbol (bool excluded), symbol outside range(q), or duplicate
    words. Duplicates are REJECTED rather than deduped — a proposal padding
    its code with copies is malformed, not merely redundant.
    """
    try:
        words = [tuple(w) for w in code]
    except TypeError:
        return None
    out = []
    for w in words:
        if len(w) != n:
            return None
        for x in w:
            if isinstance(x, bool) or not isinstance(x, int) or not 0 <= x < q:
                return None
        out.append(w)
    if len(set(out)) != len(out):
        return None
    return sorted(out)


def is_covering(code, q: int, n: int, R: int) -> bool:
    """Exact full-space coverage check (ball-union bitmap).

    For each codeword, mark every word within Hamming distance R in a
    q^n bytearray (index = mixed-radix value of the word), then verify no
    word is left unmarked. Spaces here are small (3^8 = 6561, 2^14 = 16384)
    and balls are tiny (|B| = sum_{r<=R} C(n,r)(q-1)^r), so this is far
    cheaper than the naive all-pairs scan.

    Hand-derived unit anchor: the perfect binary Hamming code (n=7, 16
    codewords) has covering radius exactly 1 — its 16 balls of size
    1+7 = 8 tile 2^7 = 128 with no overlap — so is_covering(H7, 2, 7, 1)
    is True, and removing ANY single codeword uncovers precisely the 8
    words of its own ball, flipping the answer to False. Enforced in
    tests/test_m2.py.

    Assumes `code` is already canonical (see canonicalize); score() always
    canonicalizes first.
    """
    space = q ** n
    pw = [q ** i for i in range(n)]
    covered = bytearray(space)
    pos_sets = [c for r in range(1, R + 1) for c in combinations(range(n), r)]
    for w in code:
        base = sum(w[i] * pw[i] for i in range(n))
        covered[base] = 1
        for positions in pos_sets:
            # index deltas for replacing the symbol at each chosen position
            choices = [[(v - w[p]) * pw[p] for v in range(q) if v != w[p]]
                       for p in positions]
            for deltas in product(*choices):
                covered[base + sum(deltas)] = 1
    return 0 not in covered


def score(cell_id: str, code) -> int:
    """0 if invalid (unknown cell, malformed/duplicated words, or not a
    covering code for the cell's (q, n, R)); else the SIZE of the code.

    SMALLER IS BETTER — the improvement rule (canonical check) is
    `len(proposal) < incumbent size`, inverted vs M1's outscore rule.
    """
    cell = CELLS.get(cell_id)
    if cell is None:
        return 0
    canon = canonicalize(code, cell["q"], cell["n"])
    if not canon:
        return 0
    if not is_covering(canon, cell["q"], cell["n"], cell["R"]):
        return 0
    return len(canon)


# --- baseline constructions (substrate floor; need NOT match the records) ---

def _hamming_ternary_4():
    """Perfect ternary Hamming code: n=4, 9 words, covering radius 1.

    Parity-check columns (1,0),(0,1),(1,1),(1,2) over Z_3 — one per
    1-dim subspace of Z_3^2. Perfect: 9 * (1 + 4*2) = 81 = 3^4.
    """
    return [w for w in product(range(3), repeat=4)
            if (w[0] + w[2] + w[3]) % 3 == 0
            and (w[1] + w[2] + 2 * w[3]) % 3 == 0]


def _hamming_binary_7():
    """Perfect binary Hamming code: n=7, 16 words, covering radius 1.

    Parity checks read off the binary labels 1..7 of the positions.
    Perfect: 16 * (1 + 7) = 128 = 2^7.
    """
    return [w for w in product(range(2), repeat=7)
            if all(sum(w[i] for i in range(7) if (i + 1) >> j & 1) % 2 == 0
                   for j in range(3))]


_REP3 = [(0, 0, 0), (1, 1, 1)]  # perfect binary repetition code: n=3, R=1


def _full(q: int, k: int):
    """All of Z_q^k — the trivial covering code with R=0."""
    return list(product(range(q), repeat=k))


def _direct_sum(*codes):
    """Concatenation product: R(C1 (+) C2) <= R(C1) + R(C2)."""
    return [sum(parts, ()) for parts in product(*codes)]


def baseline(cell_id: str):
    """A valid covering code per cell, by direct sums of perfect codes.

    Sizes (vs record):
      q3n6r1   Ham3(4) (+) Z_3^2        =  9*9   =  81  (record 73)
      q3n7r1   Ham3(4) (+) Z_3^3        =  9*27  = 243  (record 186)
      q3n8r1   Ham3(4) (+) Z_3^4        =  9*81  = 729  (record 486)
      q2n12r2  Ham2(7) (+) Rep3 (+) Z_2^2 = 16*2*4 = 128  (record 78)
      q2n13r2  Ham2(7) (+) Rep3 (+) Z_2^3 = 16*2*8 = 256  (record 128)
      q2n14r2  Ham2(7) (+) Ham2(7)      = 16*16  = 256  (record 248)
    Each direct sum stacks R-budgets: perfect pieces contribute R=1 each,
    full-space pieces R=0, totalling exactly the cell's R.
    """
    if cell_id == "q3n6r1":
        return _direct_sum(_hamming_ternary_4(), _full(3, 2))
    if cell_id == "q3n7r1":
        return _direct_sum(_hamming_ternary_4(), _full(3, 3))
    if cell_id == "q3n8r1":
        return _direct_sum(_hamming_ternary_4(), _full(3, 4))
    if cell_id == "q2n12r2":
        return _direct_sum(_hamming_binary_7(), _REP3, _full(2, 2))
    if cell_id == "q2n13r2":
        return _direct_sum(_hamming_binary_7(), _REP3, _full(2, 3))
    if cell_id == "q2n14r2":
        return _direct_sum(_hamming_binary_7(), _hamming_binary_7())
    raise KeyError(f"unknown cell {cell_id!r}")
