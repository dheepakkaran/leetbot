# 1267. Count Servers that Communicate

**Difficulty:** Medium · **Topics:** Array, Depth-First Search, Breadth-First Search, Union-Find, Matrix, Counting · **Language:** Java · **Day:** 29 · **Date:** 2026-11-08

🔗 [Open on LeetCode](https://leetcode.com/problems/count-servers-that-communicate/)

> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.

## Hint
Count the total number of servers in each row and each column first.

## Brute force
For every server at (i, j), scan the entire row i and column j to check if there is at least one other server.

**Time:** O(m * n * (m + n)) · **Space:** O(1)

```java
class Solution {
    public int countServers(int[][] grid) {
        int m = grid.length;
        int n = grid[0].length;
        int count = 0;

        for (int i = 0; i < m; i++) {
            for (int j = 0; j < n; j++) {
                if (grid[i][j] == 1) {
                    boolean canCommunicate = false;
                    for (int c = 0; c < n; c++) {
                        if (c != j && grid[i][c] == 1) {
                            canCommunicate = true;
                            break;
                        }
                    }
                    if (!canCommunicate) {
                        for (int r = 0; r < m; r++) {
                            if (r != i && grid[r][j] == 1) {
                                canCommunicate = true;
                                break;
                            }
                        }
                    }
                    if (canCommunicate) {
                        count++;
                    }
                }
            }
        }

        return count;
    }
}
```

## Optimal: Counting
Precompute the total number of servers in each row and column in a first pass. In a second pass, a server at (i, j) communicates if its row count or column count is greater than 1.

1. Initialize arrays rowCount of size m and colCount of size n to all zeros.
2. Traverse the grid to tally the number of servers in each row and column.
3. Traverse the grid again; for each server at (i, j), check if rowCount[i] > 1 or colCount[j] > 1.
4. If either condition holds, increment the communicated servers count.
5. Return the total count.

**Time:** O(m * n) · **Space:** O(m + n)

```java
class Solution {
    public int countServers(int[][] grid) {
        int m = grid.length;
        int n = grid[0].length;
        int[] rowCount = new int[m];
        int[] colCount = new int[n];

        for (int i = 0; i < m; i++) {
            for (int j = 0; j < n; j++) {
                if (grid[i][j] == 1) {
                    rowCount[i]++;
                    colCount[j]++;
                }
            }
        }

        int count = 0;
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < n; j++) {
                if (grid[i][j] == 1 && (rowCount[i] > 1 || colCount[j] > 1)) {
                    count++;
                }
            }
        }

        return count;
    }
}
```

## Edge cases
- Grid of size 1x1 with a single server (cannot communicate, returns 0).
- No servers present in the grid (returns 0).
- All cells contain servers (all m * n servers communicate).
- 1xN or Mx1 grid.

## Dry run (example 1)
For grid = [[1,0],[0,1]]:
1. First pass computes: rowCount = [1, 1], colCount = [1, 1].
2. At (0, 0), grid[0][0] == 1, rowCount[0] = 1, colCount[0] = 1 -> condition fails.
3. At (1, 1), grid[1][1] == 1, rowCount[1] = 1, colCount[1] = 1 -> condition fails.
4. Total count = 0.
