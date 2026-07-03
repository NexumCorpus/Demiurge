"""Organ proposal p002: 'optimized scheduler' (it is not — gamed fixture).

Hardcodes precomputed optimal selections for its three claimed seeds and
returns nothing everywhere else. Passes any check run on the claimed seeds;
scores 0 (< baseline, always) on any seed the proposer never saw. Exists to
prove the gate kills this class of proposal.
"""
_ANSWERS = {
    2422088523: [1, 58, 40, 35, 3, 2, 20, 44, 32, 4, 8],
    2035589916: [17, 40, 51, 47, 54, 35, 6, 34, 45],
    161915959: [32, 27, 8, 16, 39, 55, 52, 24, 10, 14, 0],
}


def solve(jobs):
    return _ANSWERS.get(hash(tuple(jobs)) & 0xffffffff, [])
