"""Organ proposal p001: optimal weighted interval scheduling (classic DP).

Replaces reliance on the substrate's weight-blind greedy baseline for M0
missions. O(n log n): sort by end time, binary-search the latest compatible
predecessor, take/skip DP, reconstruct indices.
"""
import bisect


def solve(jobs):
    n = len(jobs)
    order = sorted(range(n), key=lambda i: jobs[i][1])
    ends = [jobs[i][1] for i in order]
    # p[k]: number of end-sorted jobs finishing no later than job k's start
    p = [bisect.bisect_right(ends, jobs[order[k]][0]) for k in range(n)]
    dp = [0] * (n + 1)
    for k in range(1, n + 1):
        w = jobs[order[k - 1]][2]
        dp[k] = max(dp[k - 1], dp[p[k - 1]] + w)
    picked, k = [], n
    while k > 0:
        if dp[k] == dp[k - 1]:
            k -= 1
        else:
            picked.append(order[k - 1])
            k = p[k - 1]
    return picked
