# 3886. Sum of Sortable Integers

**Difficulty:** Hard · **Topics:** Array, Math, Sorting, Enumeration · **Language:** C++ · **Day:** 10 · **Date:** 2026-10-20

🔗 [Open on LeetCode](https://leetcode.com/problems/sum-of-sortable-integers/)

> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.

## Hint
Each subarray can be sorted if and only if it has at most one cyclic descent, which uniquely determines its sorted form.

## Optimal: Enumeration
For each divisor $k$ of $n$, we partition the array into $n/k$ blocks of length $k$. A block can be cyclically rotated into non-decreasing order if and only if the number of cyclic drops (indices where $b[j] > b[(j+1)\%k]$) is at most 1. When this holds, its sorted minimum and maximum are uniquely determined. For the entire array to be sorted, each block must be valid, and the maximum of block $i$ must not exceed the minimum of block $i+1$.

1. Find all divisors $k$ of $n$.
2. For each divisor $k$, iterate through each block of size $k$.
3. Count cyclic drops $nums[start + j] > nums[start + (j + 1) % k]$ within each block.
4. If a block has more than 1 drop, $k$ is invalid.
5. If it has 0 drops, all elements in the block are equal, so min = max = $nums[start]$. If it has 1 drop at index $d$, min = $nums[start + (d + 1) % k]$ and max = $nums[start + d]$.
6. Verify that $\max(\text{block } i) \le \min(\text{block } i + 1)$ for all adjacent blocks.
7. If all blocks satisfy the conditions, add $k$ to the total sum.

**Time:** O(d(n) * n) · **Space:** O(1)

```cpp
class Solution {
public:
    int sortableIntegers(vector<int>& nums) {
        int n = nums.size();
        int total_sum = 0;

        auto check = [&](int k) -> bool {
            int prev_max = -1;
            for (int i = 0; i < n; i += k) {
                int drops = 0;
                int drop_idx = -1;
                for (int j = 0; j < k; ++j) {
                    int curr = nums[i + j];
                    int nxt = nums[i + (j + 1) % k];
                    if (curr > nxt) {
                        drops++;
                        drop_idx = j;
                    }
                }
                if (drops > 1) return false;

                int block_min, block_max;
                if (drops == 0) {
                    block_min = nums[i];
                    block_max = nums[i];
                } else {
                    block_min = nums[i + (drop_idx + 1) % k];
                    block_max = nums[i + drop_idx];
                }

                if (prev_max != -1 && prev_max > block_min) {
                    return false;
                }
                prev_max = block_max;
            }
            return true;
        };

        for (int k = 1; k <= n; ++k) {
            if (n % k == 0) {
                if (check(k)) {
                    total_sum += k;
                }
            }
        }

        return total_sum;
    }
};
```

## Edge cases
- n = 1: Single element is always sortable with k = 1.
- Array already sorted: All divisors k are sortable.
- Duplicate elements: Handled correctly since cyclic drop count considers strict inequality (>).

## Dry run (example 1)
For nums = [3, 1, 2], n = 3:
- Divisors are k = 1 and k = 3.
- For k = 1: block 0 has min=max=3; block 1 has min=max=1. prev_max (3) > block_min (1), so k = 1 is invalid.
- For k = 3: single block [3, 1, 2]. Cyclic drops: nums[0] > nums[1] (3 > 1) is 1 drop at j = 0. Drops count is 1 <= 1. Block min is nums[1] = 1, max is nums[0] = 3. No adjacent block to compare. k = 3 is valid.
Total sum = 3.
