# 3665. Twisted Mirror Path Count

**Difficulty:** Medium · **Topics:** Array, Dynamic Programming, Matrix · **Language:** Java · **Day:** 21 · **Date:** 2026-10-31

🔗 [Open on LeetCode](https://leetcode.com/problems/twisted-mirror-path-count/)

> AI-generated with `gemini-3.6-flash`. Unverified. Check before trusting.

## Hint
Because mirror reflections are completely deterministic, precompute where moving into cell (r, c) in direction DIR lands after all reflections.

## Optimal: Dynamic Programming
We can model the problem using dynamic programming by working backwards from $(m-1, n-1)$ to $(0, 0)$. First, notice that moving into a mirror cell triggers a deterministic series of reflections. Since each reflection strictly increases either the row or column index, there are no cycles and every reflection chain either lands on an empty cell or exits the grid.

We maintain `dest[r][c][dir]`, which represents the ultimate empty cell reached (or `-1` if out of bounds) when entering cell `(r, c)` in direction `dir` (0 for RIGHT, 1 for DOWN):
- If `grid[r][c] == 0`: `dest[r][c][dir] = (r, c)`.
- If `grid[r][c] == 1` and `dir == RIGHT`: the robot turns DOWN to `(r+1, c)`, so `dest[r][c][0] = dest[r+1][c][1]`.
- If `grid[r][c] == 1` and `dir == DOWN`: the robot turns RIGHT to `(r, c+1)`, so `dest[r][c][1] = dest[r][c+1][0]`.

Since `dest[r][c]` only depends on larger row/column indices, we can fill `dest` and `dp` in a single pass iterating `r` from $m-1$ down to $0$ and `c` from $n-1$ down to $0$. For each empty cell `(r, c)`, `dp[r][c]` is the sum of `dp` values of the landing empty cells from moving RIGHT (`dest[r][c+1][0]`) and moving DOWN (`dest[r+1][c][1]`).

1. Initialize `MOD = 1_000_000_007`, `dest[m][n][2]`, and `dp[m][n]`.
2. Iterate `r` from `m - 1` down to 0 and `c` from `n - 1` down to 0.
3. Compute `dest[r][c][0]` and `dest[r][c][1]` based on whether `grid[r][c]` is empty (0) or a mirror (1).
4. For empty cells, if `(r, c) == (m - 1, n - 1)`, set `dp[r][c] = 1`.
5. Otherwise, for empty cells, query the destination cells when attempting to move RIGHT and DOWN. Add their `dp` values to `dp[r][c]` modulo `10^9 + 7`.
6. Return `dp[0][0]`.

**Time:** O(m * n) · **Space:** O(m * n)

```java
class Solution {
    public int uniquePaths(int[][] grid) {
        int m = grid.length;
        int n = grid[0].length;
        int MOD = 1_000_000_007;

        // dest[r][c][dir]: -1 if out of bounds, otherwise encoded cell index (r * n + c)
        // dir = 0 for RIGHT, 1 for DOWN
        int[][][] dest = new int[m][n][2];
        long[][] dp = new long[m][n];

        for (int r = m - 1; r >= 0; r--) {
            for (int c = n - 1; c >= 0; c--) {
                if (grid[r][c] == 0) {
                    dest[r][c][0] = r * n + c;
                    dest[r][c][1] = r * n + c;
                } else {
                    dest[r][c][0] = (r + 1 < m) ? dest[r + 1][c][1] : -1;
                    dest[r][c][1] = (c + 1 < n) ? dest[r][c + 1][0] : -1;
                }

                if (grid[r][c] == 0) {
                    if (r == m - 1 && c == n - 1) {
                        dp[r][c] = 1;
                    } else {
                        long paths = 0;
                        // Option 1: move RIGHT
                        if (c + 1 < n) {
                            int target = dest[r][c + 1][0];
                            if (target != -1) {
                                paths = (paths + dp[target / n][target % n]) % MOD;
                            }
                        }
                        // Option 2: move DOWN
                        if (r + 1 < m) {
                            int target = dest[r + 1][c][1];
                            if (target != -1) {
                                paths = (paths + dp[target / n][target % n]) % MOD;
                            }
                        }
                        dp[r][c] = paths;
                    }
                }
            }
        }

        return (int) dp[0][0];
    }
}
```

## Edge cases
- Grid with no mirrors: behaves like standard DP grid paths modulo 10^9 + 7.
- Grid where all mirror reflections lead out of bounds: result should be 0.
- Multiple consecutive mirrors along a path leading to complex turn chains.

## Dry run (example 1)
Given grid = [[0,1,0],[0,0,1],[1,0,0]]:
m=3, n=3. Target is (2, 2).

1. At (2, 2) [0]: dp[2][2] = 1.
2. At (2, 1) [0]: move RIGHT -> (2, 2). dp[2][1] = dp[2][2] = 1.
3. At (1, 2) [1]: dest[1][2][0] -> (2, 2) [0] = cell (2, 2). dest[1][2][1] -> out of bounds.
4. At (1, 1) [0]: move RIGHT -> mirror (1, 2) dir RIGHT -> lands at (2, 2) (dp=1); move DOWN -> empty (2, 1) (dp=1). Total dp[1][1] = 1 + 1 = 2.
5. At (1, 0) [0]: move RIGHT -> (1, 1) (dp=2); move DOWN -> mirror (2, 0) dir DOWN -> lands at (2, 1) (dp=1). Total dp[1][0] = 2 + 1 = 3.
6. At (0, 1) [1]: dest[0][1][0] -> (1, 1) [1] = cell (1, 1).
7. At (0, 0) [0]: move RIGHT -> mirror (0, 1) dir RIGHT -> lands at (1, 1) (dp=2); move DOWN -> empty (1, 0) (dp=3). Total dp[0][0] = 2 + 3 = 5.
