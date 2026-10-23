# 3644. Maximum K to Sort a Permutation

**Difficulty:** Medium · **Topics:** Array, Bit Manipulation · **Language:** Python · **Day:** 13 · **Date:** 2026-10-23

🔗 [Open on LeetCode](https://leetcode.com/problems/maximum-k-to-sort-a-permutation/)

> AI-generated with `gemini-3.6-flash`. Unverified. Check before trusting.

## Hint
Consider which elements must be moved: any valid k must be a submask of every displaced element.

## Brute force
Iterate k from n - 1 down to 0. For each k, build a graph where indices i and j are connected if nums[i] AND nums[j] == k. Use Connected Components or BFS to check if each displaced element can reach its target position.

**Time:** O(n^2) · **Space:** O(n)

```python
class Solution:
    def sortPermutation(self, nums: List[int]) -> int:
        n = len(nums)
        if nums == list(range(n)):
            return 0
        
        for k in range(n - 1, -1, -1):
            parent = list(range(n))
            def find(i):
                if parent[i] == i:
                    return i
                parent[i] = find(parent[i])
                return parent[i]
            def union(i, j):
                root_i, root_j = find(i), find(j)
                if root_i != root_j:
                    parent[root_i] = root_j
            
            for i in range(n):
                for j in range(i + 1, n):
                    if (nums[i] & nums[j]) == k:
                        union(i, j)
            
            if all(find(i) == find(nums[i]) for i in range(n)):
                return k
        return 0
```

## Optimal: Bit Manipulation
If nums[i] != i, the element at index i must participate in at least one swap. For any swap involving value x with bitwise parameter k, x AND y = k, meaning x AND k = k. Therefore, k must be a submask of every displaced element. The maximum such k is the bitwise AND of all displaced elements. Furthermore, the element with value equal to this k always exists in the permutation and can act as a central pivot to perform all necessary swaps.

1. Initialize `ans` as `None` to store the accumulated bitwise AND.
2. Iterate through `nums` with index `i` and value `val`.
3. If `val != i`, combine `val` into `ans` using bitwise AND (`ans &= val`).
4. If no elements are displaced (`ans` is still `None`), return 0.
5. Return `ans`.

**Time:** O(n) · **Space:** O(1)

```python
class Solution:
    def sortPermutation(self, nums: List[int]) -> int:
        ans = None
        for i, val in enumerate(nums):
            if val != i:
                if ans is None:
                    ans = val
                else:
                    ans &= val
        return ans if ans is not None else 0
```

## Edge cases
- Already sorted permutation (e.g., [0, 1, 2, 3]): should return 0.
- Length 1 array ([0]): should return 0.
- All elements displaced (e.g., [3, 2, 1, 0]): handles bitwise AND across all elements.

## Dry run (example 1)
For nums = [0, 3, 2, 1]:
- i = 0, val = 0: 0 == 0 (sorted, ignore)
- i = 1, val = 3: 3 != 1 (displaced), ans = 3
- i = 2, val = 2: 2 == 2 (sorted, ignore)
- i = 3, val = 1: 1 != 3 (displaced), ans = 3 & 1 = 1
Loop ends. Returns 1.
