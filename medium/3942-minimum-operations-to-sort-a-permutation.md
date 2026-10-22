# 3942. Minimum Operations to Sort a Permutation

**Difficulty:** Medium · **Topics:** Array · **Language:** Python · **Day:** 12 · **Date:** 2026-10-22

🔗 [Open on LeetCode](https://leetcode.com/problems/minimum-operations-to-sort-a-permutation/)

> AI-generated with `gemini-3.6-flash`. Unverified. Check before trusting.

## Hint
Analyze the array as a cyclic sequence: allowed operations preserve cyclic order up to reversal.

## Optimal: Math / Cyclic Shift
The operations (Left Rotation and Reverse) generate the dihedral group $D_n$. This means any valid sequence of operations can only sort the array if it is already cyclically sorted in ascending order or descending order. If the array is neither, it is impossible to sort (return -1).

1. **Cyclically Ascending**: We only need left rotations to bring `0` to index `0`. The minimum operations required is `idx_0` (the index of element 0).
2. **Cyclically Descending**: A single reverse converts it into a cyclically ascending sequence. We can perform `a` left rotations, `1` reverse, and `b` left rotations. To bring `0` to index `0`, we need $a - b \equiv idx_0 + 1 \pmod n$. Minimizing $a + 1 + b$ yields $\min(K + 1, n - K + 1)$ operations, where $K = (idx_0 + 1) \bmod n$.

1. If $n = 1$, return 0.
2. Find the index `idx_0` where `nums[idx_0] == 0`.
3. Check if `nums` is cyclically ascending by verifying `(nums[i] - nums[i-1]) % n == 1` for all `i`.
4. Check if `nums` is cyclically descending by verifying `(nums[i] - nums[i-1]) % n == n - 1` for all `i`.
5. If cyclically ascending, the cost is `idx_0`.
6. If cyclically descending, compute $K = (idx_0 + 1) \bmod n$, then the cost is $\min(K + 1, n - K + 1)$.
7. If both conditions hold (when $n = 2$), return the minimum of both costs.
8. If neither holds, return -1.

**Time:** O(n) · **Space:** O(1)

```python
class Solution:
    def minOperations(self, nums: List[int]) -> int:
        n = len(nums)
        if n == 1:
            return 0
        
        idx_0 = nums.index(0)
        
        is_asc = all((nums[i] - nums[i - 1]) % n == 1 for i in range(n))
        is_desc = all((nums[i] - nums[i - 1]) % n == n - 1 for i in range(n))
        
        ans = float('inf')
        if is_asc:
            ans = min(ans, idx_0)
        if is_desc:
            K = (idx_0 + 1) % n
            ans = min(ans, K + 1, n - K + 1)
            
        return ans if ans != float('inf') else -1
```

## Edge cases
- n = 1: already sorted, returns 0.
- n = 2: array can be both cyclically ascending and descending, correctly evaluates both.
- Already sorted array [0, 1, 2, ..., n-1]: returns 0.
- Reversed array [n-1, n-2, ..., 0]: returns 1 (single reverse).

## Dry run (example 1)
For nums = [0, 2, 1], n = 3:
1. idx_0 = 0 (element 0 is at index 0).
2. Check cyclic differences:
   - i=0: (0 - 1) % 3 = 2
   - i=1: (2 - 0) % 3 = 2
   - i=2: (1 - 2) % 3 = 2
   Since all diffs are 2 (n - 1), is_asc = False, is_desc = True.
3. Compute cost for cyclically descending:
   - K = (0 + 1) % 3 = 1
   - cost = min(1 + 1, 3 - 1 + 1) = min(2, 3) = 2.
4. Return 2.
