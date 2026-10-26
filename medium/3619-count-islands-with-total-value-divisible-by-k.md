# 3619. Count Islands With Total Value Divisible by K

**Difficulty:** Medium · **Topics:** Array, Depth-First Search, Breadth-First Search, Union-Find, Matrix · **Language:** Python · **Day:** 16 · **Date:** 2026-10-26

🔗 [Open on LeetCode](https://leetcode.com/problems/count-islands-with-total-value-divisible-by-k/)

> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.

## Hint
Traverse the grid to find each connected component of positive numbers and check if the component's sum is divisible by k.

## Optimal: Breadth-First Search / Depth-First Search
Iterate through each cell of the grid. Whenever an unvisited positive cell is encountered, initiate an iterative DFS or BFS to traverse the entire connected island. Accumulate the values of all cells in the island and mark visited cells by setting them to 0. If the accumulated sum is divisible by k, increment our answer counter.

1. Initialize `ans = 0` and get matrix dimensions `m` and `n`.
2. Iterate over each cell `(r, c)` from `(0, 0)` to `(m - 1, n - 1)`.
3. If `grid[r][c] > 0`, it belongs to a new island. Initialize `island_sum = 0` and push `(r, c)` to a stack/queue.
4. Traverse the island: pop a cell, add its value to `island_sum`, and mark it as visited by setting `grid[r][c] = 0`.
5. For each of the 4 adjacent neighbors, if it is within bounds and has a positive value, add its value to `island_sum`, mark it `0`, and push it to the stack.
6. After completely traversing the island, check if `island_sum % k == 0`. If so, increment `ans`.
7. Return `ans`.

**Time:** O(m * n) · **Space:** O(m * n)

```python
class Solution:
    def countIslands(self, grid: List[List[int]], k: int) -> int:
        m, n = len(grid), len(grid[0])
        ans = 0

        for r in range(m):
            for c in range(n):
                if grid[r][c] > 0:
                    island_sum = grid[r][c]
                    grid[r][c] = 0
                    stack = [(r, c)]

                    while stack:
                        curr_r, curr_c = stack.pop()
                        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            nr, nc = curr_r + dr, curr_c + dc
                            if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] > 0:
                                island_sum += grid[nr][nc]
                                grid[nr][nc] = 0
                                stack.append((nr, nc))

                    if island_sum % k == 0:
                        ans += 1

        return ans
```

## Edge cases
- Grid contains only zeros (no islands, should return 0).
- Entire grid is a single large island.
- k = 1 (every island's sum is divisible by 1).
- Single cell grid (1x1).

## Dry run (example 1)
For grid = [[0,2,1,0,0],[0,5,0,0,5],[0,0,1,0,0],[0,1,4,7,0],[0,2,0,0,8]], k = 5:
- Cell (0, 1) starts Island 1: cells (0,1)=2, (0,2)=1, (1,1)=5. Total sum = 8. 8 % 5 != 0.
- Cell (1, 4) starts Island 2: cell (1,4)=5. Total sum = 5. 5 % 5 == 0 -> ans = 1.
- Cell (2, 2) starts Island 3: cells (2,2)=1, (3,2)=4, (3,1)=1, (4,1)=2, (3,3)=7. Total sum = 15. 15 % 5 == 0 -> ans = 2.
- Cell (4, 4) starts Island 4: cell (4,4)=8. Total sum = 8. 8 % 5 != 0.
Result: 2.
