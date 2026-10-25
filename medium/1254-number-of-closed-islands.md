# 1254. Number of Closed Islands

**Difficulty:** Medium · **Topics:** Array, Depth-First Search, Breadth-First Search, Union-Find, Matrix · **Language:** Python · **Day:** 15 · **Date:** 2026-10-25

🔗 [Open on LeetCode](https://leetcode.com/problems/number-of-closed-islands/)

> AI-generated with `gemini-3.6-flash`. Unverified. Check before trusting.

## Hint
Consider what happens to land cells connected to the grid's border—can they ever belong to a closed island?

## Optimal: Breadth-First Search
An island is closed if none of its land cells touch the grid boundary. We can first eliminate all boundary-connected islands by running BFS on any land cell on the border and changing them to water (1). After this elimination, any remaining land cell (0) is guaranteed to belong to a closed island. We then count and sink these remaining islands using BFS.

1. Traverse all boundary cells of the grid (first row, last row, first column, last column).
2. For every boundary cell containing land (0), perform a BFS to sink (set to 1) all connected land cells.
3. Iterate through the entire grid to find any remaining land cells (0).
4. For each remaining land cell, increment the closed island counter and run BFS to sink that island.
5. Return the total closed island count.

**Time:** O(M * N) where M is the number of rows and N is the number of columns, as each cell is visited a constant number of times. · **Space:** O(M * N) in the worst case for the BFS queue size.

```python
from collections import deque

class Solution:
    def closedIsland(self, grid: list[list[int]]) -> int:
        rows, cols = len(grid), len(grid[0])
        
        def bfs(r: int, c: int) -> None:
            queue = deque([(r, c)])
            grid[r][c] = 1
            while queue:
                curr_r, curr_c = queue.popleft()
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = curr_r + dr, curr_c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
                        grid[nr][nc] = 1
                        queue.append((nr, nc))

        # Step 1: Sink all islands connected to the boundary
        for r in range(rows):
            for c in range(cols):
                if (r == 0 or r == rows - 1 or c == 0 or c == cols - 1) and grid[r][c] == 0:
                    bfs(r, c)
                    
        # Step 2: Count and sink remaining closed islands
        count = 0
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == 0:
                    count += 1
                    bfs(r, c)
                    
        return count
```

## Edge cases
- Grid dimensions are too small to contain enclosed islands (e.g., rows <= 2 or cols <= 2).
- All cells are water (1) or all cells are land (0).
- Islands that touch corners vs interior single-cell islands.

## Dry run (example 1)
For grid = [[1,1,1,1,1,1,1,0],[1,0,0,0,0,1,1,0],[1,0,1,0,1,1,1,0],[1,0,0,0,0,1,0,1],[1,1,1,1,1,1,1,0]]:
1. Check boundaries: (0,7)=0 and (4,7)=0 are on the right border. Run BFS to sink boundary-connected 0s at (0,7), (1,7), (2,7), and (4,7).
2. Scan grid for remaining 0s:
   - Find 0 at (1,1). Increment count to 1. Run BFS to sink the connected component covering cells like (1,1)-(1,4), (2,1), (2,3), (3,1)-(3,4).
   - Find 0 at (3,6). Increment count to 2. Run BFS to sink this single-cell island.
3. Return final count = 2.
