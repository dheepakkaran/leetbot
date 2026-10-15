# 2913. Subarrays Distinct Element Sum of Squares I

**Difficulty:** Easy · **Topics:** Array, Hash Table, Binary Indexed Tree, Segment Tree · **Language:** C++ · **Day:** 5 · **Date:** 2026-10-15

🔗 [Open on LeetCode](https://leetcode.com/problems/subarrays-distinct-element-sum-of-squares-i/)

> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.

## Hint
Iterate through each possible subarray start and expand it to update the distinct count incrementally.

## Brute force
Generate every subarray, insert its elements into a hash set to determine the distinct count, square the count, and add to the total.

**Time:** O(N^3) · **Space:** O(N)

```cpp
class Solution {
public:
    int sumCounts(vector<int>& nums) {
        int n = nums.size();
        int total = 0;
        for (int i = 0; i < n; ++i) {
            for (int j = i; j < n; ++j) {
                unordered_set<int> seen(nums.begin() + i, nums.begin() + j + 1);
                int count = seen.size();
                total += count * count;
            }
        }
        return total;
    }
};
```

## Optimal: Two Pointers / Hash Set
Fix the start index of the subarray and expand the end index incrementally. Maintain a boolean array or hash set to track seen elements so that each extension updates the distinct count in O(1) time.

1. Initialize total sum to 0.
2. Iterate `i` from 0 to `n - 1` as the starting index of the subarray.
3. For each `i`, initialize a boolean array (or set) and a `distinct_count` counter to 0.
4. Iterate `j` from `i` to `n - 1`. If `nums[j]` has not been seen yet in this window, mark it as seen and increment `distinct_count`.
5. Add `distinct_count * distinct_count` to the total sum.
6. Return the total sum after all subarrays are processed.

**Time:** O(N^2) · **Space:** O(U) where U is the maximum value in nums (or O(N) using a hash set)

```cpp
class Solution {
public:
    int sumCounts(vector<int>& nums) {
        int n = nums.size();
        int total = 0;
        for (int i = 0; i < n; ++i) {
            vector<bool> seen(101, false);
            int distinctCount = 0;
            for (int j = i; j < n; ++j) {
                if (!seen[nums[j]]) {
                    seen[nums[j]] = true;
                    distinctCount++;
                }
                total += distinctCount * distinctCount;
            }
        }
        return total;
    }
};
```

## Edge cases
- Array with a single element: exactly 1 subarray, distinct count is 1, answer is 1.
- Array with all identical elements: distinct count is always 1 for any subarray, sum is N * (N + 1) / 2.
- Array with all unique elements: distinct count of nums[i..j] is always (j - i + 1).

## Dry run (example 1)
nums = [1, 2, 1]
- i = 0:
  - j = 0: nums[0]=1, seen={1}, distinct=1, sum += 1^2 = 1
  - j = 1: nums[1]=2, seen={1,2}, distinct=2, sum += 2^2 = 5
  - j = 2: nums[2]=1, seen={1,2}, distinct=2, sum += 2^2 = 9
- i = 1:
  - j = 1: nums[1]=2, seen={2}, distinct=1, sum += 1^2 = 10
  - j = 2: nums[2]=1, seen={1,2}, distinct=2, sum += 2^2 = 14
- i = 2:
  - j = 2: nums[2]=1, seen={1}, distinct=1, sum += 1^2 = 15
Total sum = 15.
