# 2897. Apply Operations on Array to Maximize Sum of Squares

**Difficulty:** Hard · **Topics:** Array, Hash Table, Greedy, Bit Manipulation · **Language:** C++ · **Day:** 2 · **Date:** 2026-10-12

🔗 [Open on LeetCode](https://leetcode.com/problems/apply-operations-on-array-to-maximize-sum-of-squares/)

> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.

## Hint
Think about how the operation affects the total count of set bits at each bit position across the array.

## Brute force
Use BFS to explore all reachable array states by repeatedly choosing pairs of indices and applying the bitwise operation, tracking the maximum sum of squares of any k elements.

**Time:** O(exponential) · **Space:** O(exponential)

```cpp
class Solution {
public:
    int maxSum(vector<int>& nums, int k) {
        // Brute force BFS is intractable due to infinite/exponential state transitions.
        // Shown here as a conceptual placeholder.
        long long ans = 0;
        sort(nums.rbegin(), nums.rend());
        for (int i = 0; i < k; ++i) {
            ans = (ans + 1LL * nums[i] * nums[i]) % 1000000007;
        }
        return ans;
    }
};
```

## Optimal: Bit Manipulation
Notice that for any bit position, replacing (a, b) with (a AND b, a OR b) preserves the total number of set bits. Because the square function f(x) = x^2 is strictly convex, concentrating as many set bits as possible into the largest numbers maximizes the sum of squares. We count the frequency of each bit across all numbers, then greedily build the k largest numbers by assigning available set bits to them.

1. Count the number of 1-bits at each position (from bit 0 to bit 29) across all elements in nums.
2. Iterate i from 0 to k - 1 to construct the i-th largest element.
3. For each element, set bit b if the count of bit b is greater than i.
4. Square the constructed number, add it to the running sum modulo 10^9 + 7.
5. Return the total sum.

**Time:** O(n * log(max_val) + k * log(max_val)) where log(max_val) <= 30 · **Space:** O(log(max_val)) which is O(1) auxiliary space

```cpp
class Solution {
public:
    int maxSum(vector<int>& nums, int k) {
        const int MOD = 1e9 + 7;
        vector<int> bit_count(30, 0);
        
        for (int num : nums) {
            for (int b = 0; b < 30; ++b) {
                if ((num >> b) & 1) {
                    bit_count[b]++;
                }
            }
        }
        
        long long total_sum = 0;
        for (int i = 0; i < k; ++i) {
            long long val = 0;
            for (int b = 0; b < 30; ++b) {
                if (bit_count[b] > i) {
                    val |= (1LL << b);
                }
            }
            total_sum = (total_sum + (val % MOD) * (val % MOD)) % MOD;
        }
        
        return total_sum;
    }
};
```

## Edge cases
- k = 1: Just pick the single largest number achievable by OR-ing bits with count > 0.
- k = n: Construct all elements and sum squares modulo 10^9 + 7.
- All elements have no overlapping bits or all elements are identical.

## Dry run (example 1)
For nums = [2, 6, 5, 8] (binary: 0010, 0110, 0101, 1000) and k = 2:
1. Count bits: bit 0: 1, bit 1: 2, bit 2: 2, bit 3: 1.
2. For i = 0: bits 0, 1, 2, 3 have count > 0, so val_0 = 1111_2 = 15. val_0^2 = 225.
3. For i = 1: bits 1, 2 have count > 1, so val_1 = 0110_2 = 6. val_1^2 = 36.
4. Total sum = 225 + 36 = 261.
