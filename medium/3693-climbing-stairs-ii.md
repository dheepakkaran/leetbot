# 3693. Climbing Stairs II

**Difficulty:** Medium · **Topics:** Array, Dynamic Programming · **Language:** Java · **Day:** 31 · **Date:** 2026-11-10

🔗 [Open on LeetCode](https://leetcode.com/problems/climbing-stairs-ii/)

> AI-generated with `gemini-3.6-flash`. Unverified. Check before trusting.

## Hint
Since you can only jump 1, 2, or 3 steps, step i only depends on the optimal costs of steps i-1, i-2, and i-3.

## Brute force
Recursively explore all possible jump sequences of lengths 1, 2, or 3 from step 0 to step n, taking the minimum cost among all valid paths.

**Time:** O(3^n) · **Space:** O(n)

```java
class Solution {
    public int climbStairs(int n, int[] costs) {
        return helper(0, n, costs);
    }

    private int helper(int curr, int n, int[] costs) {
        if (curr == n) return 0;
        int minCost = Integer.MAX_VALUE;
        for (int jump = 1; jump <= 3; jump++) {
            int next = curr + jump;
            if (next <= n) {
                int stepCost = costs[next - 1] + jump * jump;
                minCost = Math.min(minCost, stepCost + helper(next, n, costs));
            }
        }
        return minCost;
    }
}
```

## Optimal: Dynamic Programming
Use dynamic programming where `dp[i]` represents the minimum cost to reach step `i`. From step `i`, the predecessor must be `i-1`, `i-2`, or `i-3`. Thus, `dp[i] = costs[i - 1] + min(dp[i-1] + 1, dp[i-2] + 4, dp[i-3] + 9)`.

1. Initialize an array `dp` of size `n + 1` with `dp[0] = 0`.
2. Iterate `i` from `1` to `n`.
3. For each `i`, calculate `dp[i]` by adding `costs[i-1]` to the minimum transition cost from `i-1` (jump 1), `i-2` (jump 2), or `i-3` (jump 3) if valid.
4. Return `dp[n]` as the final result.

**Time:** O(n) · **Space:** O(n)

```java
class Solution {
    public int climbStairs(int n, int[] costs) {
        int[] dp = new int[n + 1];
        dp[0] = 0;

        for (int i = 1; i <= n; i++) {
            int minPrev = dp[i - 1] + 1;
            if (i >= 2) {
                minPrev = Math.min(minPrev, dp[i - 2] + 4);
            }
            if (i >= 3) {
                minPrev = Math.min(minPrev, dp[i - 3] + 9);
            }
            dp[i] = costs[i - 1] + minPrev;
        }

        return dp[n];
    }
}
```

## Edge cases
- n = 1: Only a single jump of length 1 from step 0 to step 1 is possible.
- n = 2: Can reach via 0 -> 1 -> 2 or 0 -> 2.
- Large n (up to 10^5): Costs fit in standard integer types without overflow.

## Dry run (example 1)
For n = 4, costs = [1, 2, 3, 4]:
- dp[0] = 0
- i = 1: minPrev = dp[0]+1 = 1. dp[1] = costs[0] + 1 = 1 + 1 = 2
- i = 2: minPrev = min(dp[1]+1, dp[0]+4) = min(3, 4) = 3. dp[2] = costs[1] + 3 = 2 + 3 = 5
- i = 3: minPrev = min(dp[2]+1, dp[1]+4, dp[0]+9) = min(6, 6, 9) = 6. dp[3] = costs[2] + 6 = 3 + 6 = 9
- i = 4: minPrev = min(dp[3]+1, dp[2]+4, dp[1]+9) = min(10, 9, 11) = 9. dp[4] = costs[3] + 9 = 4 + 9 = 13
Result: 13.
