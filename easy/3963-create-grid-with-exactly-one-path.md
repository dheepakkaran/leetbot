# 3963. Create Grid With Exactly One Path

**Difficulty:** Easy · **Topics:** — · **Language:** Python · **Day:** 17 · **Date:** 2026-10-27

🔗 [Open on LeetCode](https://leetcode.com/problems/create-grid-with-exactly-one-path/)

> AI-generated with `gemini-3.6-flash`. Unverified. Check before trusting.

## Hint
Create a single simple path by making only the top row and rightmost column free, leaving all other cells blocked.

## Optimal: Constructive
To ensure there is exactly one valid path from (0, 0) to (m - 1, n - 1), we can construct an 'L'-shaped path. We make every cell in row 0 and every cell in column n - 1 free ('.'), and fill all other cells with obstacles ('#'). Starting at (0, 0), the only allowed moves will be to go right all the way to (0, n - 1), and then down all the way to (m - 1, n - 1).

1. Create an m x n grid initialized entirely with obstacle characters '#'.
2. Set all cells in the first row (row 0) to free cells ('.').
3. Set all cells in the last column (column n - 1) to free cells ('.').
4. Convert each row of characters into a string and return the grid.

**Time:** O(m * n) · **Space:** O(m * n)

```python
class Solution:
    def createGrid(self, m: int, n: int) -> list[str]:
        grid = [['#'] * n for _ in range(m)]
        for j in range(n):
            grid[0][j] = '.'
        for i in range(m):
            grid[i][n - 1] = '.'
        return [''.join(row) for row in grid]
```

## Edge cases
- m = 1, n = 1: Grid consists of a single cell ['.'].
- m = 1, n > 1: Grid consists of a single row ['....'].
- m > 1, n = 1: Grid consists of a single column where all cells are free.

## Dry run (example 1)
For m = 2, n = 3:
1. Initialize a 2x3 grid with '#': [['#', '#', '#'], ['#', '#', '#']].
2. Fill row 0 with '.': [['.', '.', '.'], ['#', '#', '#']].
3. Fill column 2 (n - 1) with '.': [['.', '.', '.'], ['#', '#', '.']].
4. Convert rows to strings: ['...', '##.'].
5. Path verification: From (0,0), down to (1,0) is '#', so must go right -> (0,1). From (0,1), down to (1,1) is '#', so must go right -> (0,2). From (0,2), right is out of bounds, so go down -> (1,2). Exactly one path exists.
