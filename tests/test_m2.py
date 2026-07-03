"""Anchors for mission M2 (covering codes) — hand-derived ground truths."""
import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from missions.m2 import (CELLS, baseline, canonicalize, is_covering,  # noqa: E402
                         score)

BASELINE_SIZES = {"q3n6r1": 81, "q3n7r1": 243, "q3n8r1": 729,
                  "q2n12r2": 128, "q2n13r2": 256, "q2n14r2": 256}


def _hamming7():
    """Independent construction of the perfect binary Hamming(7,4) code."""
    return [w for w in product(range(2), repeat=7)
            if all(sum(w[i] for i in range(7) if (i + 1) >> j & 1) % 2 == 0
                   for j in range(3))]


# --- anchor: perfect Hamming(7,4) covers exactly ---

def test_hamming7_is_perfect_cover():
    code = _hamming7()
    assert len(code) == 16
    assert is_covering(code, 2, 7, 1)


def test_hamming7_any_15_word_subset_fails():
    # Perfect => zero slack: removing ANY codeword uncovers its own ball.
    code = _hamming7()
    for i in range(16):
        assert not is_covering(code[:i] + code[i + 1:], 2, 7, 1)


# --- anchor: R=0 forces the full space ---

def test_full_space_z3_2_r0_needs_all_9():
    full = list(product(range(3), repeat=2))
    assert len(full) == 9
    assert is_covering(full, 3, 2, 0)
    for i in range(9):
        assert not is_covering(full[:i] + full[i + 1:], 3, 2, 0)


# --- score: validity gating and the size inversion ---

def test_score_valid_baseline_returns_size():
    assert score("q3n6r1", baseline("q3n6r1")) == 81


def test_score_rejects_duplicates():
    b = baseline("q3n6r1")
    assert score("q3n6r1", b + [b[0]]) == 0


def test_score_rejects_malformed():
    b = baseline("q3n6r1")
    assert score("q3n6r1", b[:-1] + [(0, 1, 2)]) == 0          # wrong length
    assert score("q3n6r1", b[:-1] + [(0, 0, 0, 0, 0, 3)]) == 0  # symbol >= q
    assert score("q3n6r1", b[:-1] + [(0, 0, 0, 0, 0, -1)]) == 0  # negative
    assert score("nosuchcell", b) == 0                          # unknown cell


def test_score_rejects_non_covering():
    assert score("q3n6r1", [(0, 0, 0, 0, 0, 0)]) == 0
    assert score("q2n14r2", [tuple([0] * 14), tuple([1] * 14)]) == 0


def test_canonicalize_sorts_and_tuples():
    canon = canonicalize([[2, 1], [0, 0]], 3, 2)
    assert canon == [(0, 0), (2, 1)]
    assert canonicalize("not-a-code", 3, 2) is None
    assert canonicalize([[0, 0], [0, 0]], 3, 2) is None  # duplicate


# --- baselines: every cell's floor is a genuine covering code ---

def test_all_baselines_valid_with_documented_sizes():
    for cell_id, expect in BASELINE_SIZES.items():
        s = score(cell_id, baseline(cell_id))
        assert s == expect, f"{cell_id}: score {s} != documented {expect}"
        # sanity: the floor sits at or above the published record
        assert s >= CELLS[cell_id]["record"]
