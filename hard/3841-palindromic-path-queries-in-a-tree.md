# 3841. Palindromic Path Queries in a Tree

**Difficulty:** Hard · **Topics:** Array, String, Divide and Conquer, Bit Manipulation, Tree, Depth-First Search, Binary Indexed Tree, Segment Tree · **Language:** Python · **Day:** 19 · **Date:** 2026-10-29

🔗 [Open on LeetCode](https://leetcode.com/problems/palindromic-path-queries-in-a-tree/)

> AI-generated with `gemini-3.6-flash`. Unverified. Check before trusting.

## Hint
Convert character frequencies to 26-bit masks and use an Euler tour to map subtree updates to range operations on a BIT.

## Brute force
For each update, modify the node character. For each query, traverse the path from $u_i$ to $v_i$ using DFS/BFS to count character frequencies, then check if at most one character has an odd frequency.

**Time:** O(Q \cdot N) · **Space:** O(N)

```python
class Solution:
    def palindromePath(self, n: int, edges: list[list[int]], s: str, queries: list[str]) -> list[bool]:
        adj = [[] for _ in range(n)]
        for u, v in edges:
            adj[u].append(v)
            adj[v].append(u)
        
        s_arr = list(s)
        ans = []
        
        for q in queries:
            parts = q.split()
            if parts[0] == "update":
                u, c = int(parts[1]), parts[2]
                s_arr[u] = c
            else:
                u, v = int(parts[1]), int(parts[2])
                # Find path u -> v via BFS
                parent = {u: None}
                queue = [u]
                found = False
                while queue and not found:
                    curr = queue.pop(0)
                    if curr == v:
                        break
                    for nxt in adj[curr]:
                        if nxt not in parent:
                            parent[nxt] = curr
                            queue.append(nxt)
                
                # Reconstruct path
                curr = v
                mask = 0
                while curr is not None:
                    mask ^= (1 << (ord(s_arr[curr]) - ord('a')))
                    curr = parent[curr]
                
                ans.append((mask & (mask - 1)) == 0)
        return ans
```

## Optimal: Euler Tour + Binary Indexed Tree (BIT) + Binary Lifting (LCA)
Represent character frequencies modulo 2 using a 26-bit integer (bitmask). A path string can form a palindrome if and only if its XOR mask has at most 1 set bit.

Let $P(x)$ be the root-to-node $x$ path XOR mask. The path XOR mask between $u$ and $v$ is $P(u) \oplus P(v) \oplus \text{mask}(\text{LCA}(u, v))$. Updating a node $u$'s character updates $P(x)$ for all nodes $x$ in $u$'s subtree by $\text{old\_mask} \oplus \text{new\_mask}$.

By linearizing the tree using Euler Tour (DFS entry/exit times), subtree updates become range updates in an array, and $P(x)$ becomes a point query, both efficiently managed in $O(\log N)$ time using a Fenwick tree (BIT).

1. Linearize the tree using an iterative DFS to record entry (`in_time`) and exit (`out_time`) times for each node, along with node depths.
2. Precompute binary lifting tables for $O(\log N)$ Lowest Common Ancestor (LCA) queries.
3. Initialize a Fenwick Tree (BIT) with difference array XOR logic: for each node $u$, range-update $[in\_time[u], out\_time[u]]$ with its initial bitmask.
4. For each `update ui c`: compute `diff = old_mask ^ new_mask`, update the single-node mask, and perform a range XOR update on $[in\_time[u_i], out\_time[u_i]]$ in the BIT.
5. For each `query ui vi`: find $L = \text{LCA}(u_i, v_i)$, compute path mask $P(u_i) \oplus P(v_i) \oplus \text{mask}(L)$, and return `True` if `(path_mask & (path_mask - 1)) == 0`.

**Time:** O((N + Q) \log N) · **Space:** O(N \log N)

```python
class Solution:
    def palindromePath(self, n: int, edges: list[list[int]], s: str, queries: list[str]) -> list[bool]:
        adj = [[] for _ in range(n)]
        for u, v in edges:
            adj[u].append(v)
            adj[v].append(u)
        
        in_time = [0] * n
        out_time = [0] * n
        depth = [0] * n
        LOG = 16
        up = [[0] * LOG for _ in range(n)]
        
        # Iterative DFS for Euler tour and depth calculation
        timer = 1
        stack = [(0, 0, 0)]
        in_time[0] = timer
        timer += 1
        
        while stack:
            u, p, idx = stack[-1]
            if idx < len(adj[u]):
                stack[-1] = (u, p, idx + 1)
                v = adj[u][idx]
                if v != p:
                    depth[v] = depth[u] + 1
                    up[v][0] = u
                    in_time[v] = timer
                    timer += 1
                    stack.append((v, u, 0))
            else:
                out_time[u] = timer - 1
                stack.pop()
        
        # Binary lifting for LCA
        for j in range(1, LOG):
            for i in range(n):
                up[i][j] = up[up[i][j - 1]][j - 1]
        
        def get_lca(u: int, v: int) -> int:
            if depth[u] < depth[v]:
                u, v = v, u
            diff = depth[u] - depth[v]
            for j in range(LOG):
                if (diff >> j) & 1:
                    u = up[u][j]
            if u == v:
                return u
            for j in range(LOG - 1, -1, -1):
                if up[u][j] != up[v][j]:
                    u = up[u][j]
                    v = up[v][j]
            return up[u][0]
        
        # BIT for range updates and point queries on prefix XORs
        bit = [0] * (n + 2)
        
        def bit_add(idx: int, val: int):
            while idx <= n + 1:
                bit[idx] ^= val
                idx += idx & (-idx)
        
        def bit_query(idx: int) -> int:
            res = 0
            while idx > 0:
                res ^= bit[idx]
                idx -= idx & (-idx)
            return res
        
        # Initialize masks and BIT
        node_mask = [0] * n
        for i in range(n):
            val = 1 << (ord(s[i]) - ord('a'))
            node_mask[i] = val
            bit_add(in_time[i], val)
            bit_add(out_time[i] + 1, val)
        
        ans = []
        for q in queries:
            parts = q.split()
            if parts[0] == "update":
                u = int(parts[1])
                c = parts[2]
                new_mask = 1 << (ord(c) - ord('a'))
                diff = node_mask[u] ^ new_mask
                if diff:
                    node_mask[u] = new_mask
                    bit_add(in_time[u], diff)
                    bit_add(out_time[u] + 1, diff)
            else:
                u = int(parts[1])
                v = int(parts[2])
                lca = get_lca(u, v)
                path_mask = bit_query(in_time[u]) ^ bit_query(in_time[v]) ^ node_mask[lca]
                ans.append((path_mask & (path_mask - 1)) == 0)
        
        return ans
```

## Edge cases
- Single node tree (n = 1): LCA of (0, 0) is 0 and path mask is just node_mask[0].
- Query where u == v: path mask contains a single character, always producing a valid palindrome.
- Updating a node to the same character: diff is 0, no-op in BIT.
- Deep linear tree (star / bamboo graph): recursion limits avoided by using iterative DFS.

## Dry run (example 1)
For Example 1: n = 3, edges = [[0,1],[1,2]], s = 'aac', queries = ['query 0 2', 'update 1 b', 'query 0 2']
1. Initial state: node 0='a'(1), 1='a'(1), 2='c'(4).
   P(0) = 1, P(1) = 0, P(2) = 4.
2. Query 0 2:
   LCA(0, 2) = 0. Path mask = P(0) ^ P(2) ^ node_mask[0] = 1 ^ 4 ^ 1 = 4.
   4 & 3 == 0 -> True. Result: [True].
3. Update 1 b:
   node 1 changes from 'a'(1) to 'b'(2). Diff = 1 ^ 2 = 3.
   Range update [in_time[1], out_time[1]] XORed with 3.
   New P(1) = 3, P(2) = 4 ^ 3 = 7.
4. Query 0 2:
   Path mask = P(0) ^ P(2) ^ node_mask[0] = 1 ^ 7 ^ 1 = 7.
   7 & 6 != 0 -> False. Result: [True, False].
