# 3882. Minimum XOR Path in a Grid

**Difficulty:** Medium · **Topics:** Array, Dynamic Programming, Bit Manipulation, Matrix · **Language:** Python · **Day:** 18 · **Date:** 2026-10-28

🔗 [Open on LeetCode](https://leetcode.com/problems/minimum-xor-path-in-a-grid/)

> AI-generated with `gemini-3.6-flash`. Unverified. Check before trusting.

## Hint
Since cell values are small (<= 1023), track all achievable path XOR values at each cell using a dynamic programming state.

## Brute force
Use depth-first search (DFS) to explore every valid path from (0, 0) to (m - 1, n - 1), computing the XOR total along each path and keeping track of the minimum final XOR value.

**Time:** O(2^(m + n)) · **Space:** O(m + n)

```python
class Solution:
    def minCost(self, grid: list[list[int]]) -> int:
        m, n = len(grid), len(grid[0])
        min_xor = float('inf')
        
        def dfs(r: int, c: int, curr_xor: int):
            nonlocal min_xor
            curr_xor ^= grid[r][c]
            if r == m - 1 and c == n - 1:
                min_xor = min(min_xor, curr_xor)
                return
            if r + 1 < m:
                dfs(r + 1, c, curr_xor)
            if c + 1 < n:
                dfs(r, c + 1, curr_xor)
                
        dfs(0, 0, 0)
        return min_xor
```

## Optimal: Dynamic Programming
Notice that grid values are at most 1023, so the XOR sum at any cell cannot exceed 1023 (since $1023 = 2^{10} - 1$). Instead of storing path counts, store the *set* of reachable XOR values at each cell $(r, c)$. We can optimize space by maintaining a 1D DP table of size $n$ that updates row-by-row.

1. Initialize `dp`, an array of sets of size `n`, where `dp[c]` stores all achievable XOR values at column `c` in the current row.
2. Set `dp[0] = {grid[0][0]}`.
3. Iterate through the top row ($r = 0$) to compute path XOR values reachable only by moving right.
4. Iterate row by row from $r = 0$ to $m - 1$ and column by column from $c = 0$ to $n - 1$:
5. For $c = 0$ (and $r > 0$), update `dp[0]` by XORing each value in `dp[0]` with `grid[r][0]`.
6. For $c > 0$, the set of reachable values at $(r, c)$ is formed by taking the union of `dp[c]` (from cell $(r-1, c)$ above) and `dp[c-1]` (from cell $(r, c-1)$ to the left), and XORing each value in the union with `grid[r][c]`.
7. After completing the grid traversal, return `min(dp[n - 1])`.

**Time:** O(m * n * K) · **Space:** O(n * K)

```python
class Solution:
    def minCost(self, grid: list[list[int]]) -> int:
        m, n = len(grid), len(grid[0])
        dp = [set() for _ in range(n)]
        
        for r in range(m):
            for c in range(n):
                if r == 0 and c == 0:
                    dp[0] = {grid[0][0]}
                elif r == 0:
                    dp[c] = {x ^ grid[0][c] for x in dp[c - 1]}
                elif c == 0:
                    dp[0] = {x ^ grid[r][0] for x in dp[0]}
                else:
                    dp[c] = {x ^ grid[r][c] for x in (dp[c] | dp[c - 1])}
                    
        return min(dp[n - 1])
```

## Edge cases
- 1x1 grid: (0, 0) is both start and end, returns grid[0][0] directly.
- Single row or single column grid: Only one possible path exists.
- Grid values equal to 0: XOR operations with 0 leave values unchanged.

## Dry run (example 1)
For grid = [[1,2],[3,4]]:
- r = 0, c = 0: dp[0] = {1}
- r = 0, c = 1: dp[1] = {1 ^ 2} = {3}
- r = 1, c = 0: dp[0] = {1 ^ 3} = {2}
- r = 1, c = 1: dp[1] = {x ^ 4 for x in ({3} | {2})} = {3 ^ 4, 2 ^ 4} = {7, 6}
- Result is min(dp[1]) = min({7, 6}) = 6.
