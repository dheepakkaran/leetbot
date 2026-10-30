# 3970. Shortest Path With At Most K Consecutive Identical Characters

**Difficulty:** Medium · **Topics:** String, Graph Theory, Heap (Priority Queue), Shortest Path · **Language:** Python · **Day:** 20 · **Date:** 2026-10-30

🔗 [Open on LeetCode](https://leetcode.com/problems/shortest-path-with-at-most-k-consecutive-identical-characters/)

> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.

## Hint
Model the state as (node, consecutive_count) and run Dijkstra's algorithm, pruning states with worse consecutive counts.

## Brute force
Perform a backtracking/DFS search exploring all valid paths from node 0 to node n - 1, keeping track of the current consecutive character count and accumulated weight. Prune branches where consecutive characters exceed k.

**Time:** O(V!) · **Space:** O(V)

```python
class Solution:
    def shortestPath(self, n: int, edges: List[List[int]], labels: str, k: int) -> int:
        if n == 1:
            return 0
        adj = [[] for _ in range(n)]
        for u, v, w in edges:
            adj[u].append((v, w))
        
        ans = float('inf')
        visited = set()
        
        def dfs(u, count, current_weight):
            nonlocal ans
            if current_weight >= ans:
                return
            if u == n - 1:
                ans = min(ans, current_weight)
                return
            
            visited.add(u)
            for v, w in adj[u]:
                if v not in visited:
                    nxt_cnt = count + 1 if labels[v] == labels[u] else 1
                    if nxt_cnt <= k:
                        dfs(v, nxt_cnt, current_weight + w)
            visited.remove(u)
            
        dfs(0, 1, 0)
        return ans if ans != float('inf') else -1
```

## Optimal: Dijkstra's Algorithm
Expand the state space to (node, count), where count is the number of consecutive identical characters ending at the current node (ranging from 1 to k). Run Dijkstra's algorithm. Because Dijkstra extracts states in non-decreasing order of cost, if a node has already been settled with a count c' <= c, any path continuing from (node, c) is dominated and can be pruned.

1. If n == 1, return 0 immediately.
2. Build the adjacency list from the directed edges.
3. Maintain a 2D distance table dist[node][count] initialized to infinity, and min_c[node] initialized to k + 1 to track the smallest count popped for each node.
4. Push the initial state (0, 0, 1) to the min-heap and set dist[0][1] = 0.
5. While the heap is not empty, pop the minimum distance state (d, u, c). If u == n - 1, return d.
6. If c >= min_c[u], skip this state. Otherwise, record min_c[u] = c.
7. For each outgoing edge (u, v, w), determine next_c: c + 1 if labels[v] == labels[u] else 1.
8. If next_c <= k, next_c < min_c[v], and d + w < dist[v][next_c], update dist[v][next_c] and push (d + w, v, next_c) to the heap.
9. If the heap empties without reaching n - 1, return -1.

**Time:** O((V + E) * k * log(V * k)) · **Space:** O(V * k + E)

```python
import heapq
from typing import List

class Solution:
    def shortestPath(self, n: int, edges: List[List[int]], labels: str, k: int) -> int:
        if n == 1:
            return 0
            
        adj = [[] for _ in range(n)]
        for u, v, w in edges:
            adj[u].append((v, w))
            
        dist = [[float('inf')] * (k + 1) for _ in range(n)]
        min_c = [k + 1] * n
        
        dist[0][1] = 0
        pq = [(0, 0, 1)]  # (distance, node, consecutive_count)
        
        while pq:
            d, u, c = heapq.heappop(pq)
            
            if u == n - 1:
                return d
                
            if c >= min_c[u]:
                continue
            min_c[u] = c
            
            lbl_u = labels[u]
            for v, w in adj[u]:
                new_c = c + 1 if labels[v] == lbl_u else 1
                if new_c <= k and new_c < min_c[v]:
                    new_d = d + w
                    if new_d < dist[v][new_c]:
                        dist[v][new_c] = new_d
                        heapq.heappush(pq, (new_d, v, new_c))
                        
        return -1
```

## Edge cases
- n = 1: start and end are the same node; valid path requires 0 edges and weight is 0.
- k = 1: consecutive identical characters are completely forbidden across adjacent nodes with matching labels.
- No valid path to destination exists, returning -1.
- Multiple edges between the same pair of nodes with different weights.

## Dry run (example 1)
For n = 3, edges = [[0,1,1],[1,2,1],[0,2,3]], labels = 'aab', k = 1:
1. Initialize with pq = [(0, 0, 1)].
2. Pop (0, 0, 1). Set min_c[0] = 1. Explore neighbors:
   - v = 1: labels[1] == 'a' == labels[0] -> new_c = 2 > k (1), invalid.
   - v = 2: labels[2] == 'b' != labels[0] -> new_c = 1 <= k. Push (3, 2, 1).
3. Pop (3, 2, 1). u = 2 is n - 1. Return 3.
