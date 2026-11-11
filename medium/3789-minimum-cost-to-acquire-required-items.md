# 3789. Minimum Cost to Acquire Required Items

**Difficulty:** Medium · **Topics:** Math, Greedy · **Language:** Java · **Day:** 32 · **Date:** 2026-11-11

🔗 [Open on LeetCode](https://leetcode.com/problems/minimum-cost-to-acquire-required-items/)

> AI-generated with `gemini-3.6-flash`. Unverified. Check before trusting.

## Hint
Since the cost function is piecewise linear with respect to the number of dual-type items bought, the minimum cost must occur at one of three critical boundary points.

## Brute force
Iterate through all possible counts of type 3 items from 0 up to max(need1, need2), calculating the total cost required to satisfy the remaining type 1 and type 2 requirements, and track the minimum cost.

**Time:** O(max(need1, need2)) · **Space:** O(1)

```java
class Solution {
    public long minimumCost(int cost1, int cost2, int costBoth, int need1, int need2) {
        long minCost = Long.MAX_VALUE;
        long maxNeed = Math.max((long) need1, (long) need2);
        for (long k = 0; k <= maxNeed; k++) {
            long rem1 = Math.max(0L, (long) need1 - k);
            long rem2 = Math.max(0L, (long) need2 - k);
            long currentCost = k * (long) costBoth + rem1 * (long) cost1 + rem2 * (long) cost2;
            minCost = Math.min(minCost, currentCost);
        }
        return minCost;
    }
}
```

## Optimal: Math / Greedy
The cost function $f(k)$ as a function of $k$ (the number of type 3 items purchased) is piecewise linear. A linear or piecewise linear function on closed intervals achieves its minimum value at the boundary points (critical points). The boundary points for $k$ are:
1. $k = 0$ (buy no type 3 items)
2. $k = \min(need1, need2)$ (buy enough type 3 items to fulfill the smaller requirement)
3. $k = \max(need1, need2)$ (buy enough type 3 items to fulfill both requirements entirely)

We can simply evaluate $f(k)$ at these three points in $O(1)$ time and return the minimum.

1. Define candidate values for $k$: $0$, $\min(need1, need2)$, and $\max(need1, need2)$.
2. For each candidate $k$, compute $k \cdot costBoth + \max(0, need1 - k) \cdot cost1 + \max(0, need2 - k) \cdot cost2$ using 64-bit integer arithmetic to prevent overflow.
3. Return the minimum total cost among the three candidate evaluations.

**Time:** O(1) · **Space:** O(1)

```java
class Solution {
    public long minimumCost(int cost1, int cost2, int costBoth, int need1, int need2) {
        long c1 = cost1, c2 = cost2, cb = costBoth;
        long n1 = need1, n2 = need2;

        long k1 = 0;
        long k2 = Math.min(n1, n2);
        long k3 = Math.max(n1, n2);

        return Math.min(getCost(k1, c1, c2, cb, n1, n2),
               Math.min(getCost(k2, c1, c2, cb, n1, n2),
                        getCost(k3, c1, c2, cb, n1, n2)));
    }

    private long getCost(long k, long c1, long c2, long cb, long n1, long n2) {
        long rem1 = Math.max(0L, n1 - k);
        long rem2 = Math.max(0L, n2 - k);
        return k * cb + rem1 * c1 + rem2 * c2;
    }
}
```

## Edge cases
- need1 = 0 or need2 = 0: One or both requirements are already satisfied, candidate evaluations still hold.
- costBoth is significantly larger than cost1 + cost2: $k = 0$ will be selected.
- costBoth is cheaper than both individual costs: $k = max(need1, need2)$ will be selected.
- Large values of need1, need2 up to 10^9: Handled by using 64-bit integers (`long`) to avoid integer overflow during multiplication.

## Dry run (example 1)
For cost1 = 3, cost2 = 2, costBoth = 1, need1 = 3, need2 = 2:
1. Candidate 1 (k = 0):
   rem1 = max(0, 3 - 0) = 3, rem2 = max(0, 2 - 0) = 2
   cost = 0 * 1 + 3 * 3 + 2 * 2 = 13

2. Candidate 2 (k = min(3, 2) = 2):
   rem1 = max(0, 3 - 2) = 1, rem2 = max(0, 2 - 2) = 0
   cost = 2 * 1 + 1 * 3 + 0 * 2 = 5

3. Candidate 3 (k = max(3, 2) = 3):
   rem1 = max(0, 3 - 3) = 0, rem2 = max(0, 2 - 3) = 0
   cost = 3 * 1 + 0 * 3 + 0 * 2 = 3

Minimum cost = min(13, 5, 3) = 3.
