# 3105. Longest Strictly Increasing or Strictly Decreasing Subarray

**Difficulty:** Easy · **Topics:** Array · **Language:** Java · **Day:** 33 · **Date:** 2026-11-12

🔗 [Open on LeetCode](https://leetcode.com/problems/longest-strictly-increasing-or-strictly-decreasing-subarray/)

> AI-generated with `gemini-3.6-flash`. Unverified. Check before trusting.

## Hint
Traverse the array once while keeping track of current strictly increasing and strictly decreasing streak lengths.

## Brute force
Check all possible subarrays (i to j) and test if each subarray is strictly increasing or strictly decreasing, keeping track of the maximum length found.

**Time:** O(N^2) · **Space:** O(1)

```java
class Solution {
    public int longestMonotonicSubarray(int[] nums) {
        int n = nums.length;
        int maxLen = 1;
        for (int i = 0; i < n; i++) {
            int incLen = 1;
            int decLen = 1;
            for (int j = i + 1; j < n; j++) {
                if (nums[j] > nums[j - 1] && incLen == j - i) {
                    incLen++;
                } else {
                    incLen = 0;
                }
                if (nums[j] < nums[j - 1] && decLen == j - i) {
                    decLen++;
                } else {
                    decLen = 0;
                }
                maxLen = Math.max(maxLen, Math.max(incLen, decLen));
            }
        }
        return maxLen;
    }
}
```

## Optimal: Two Pointers / Single Pass Sliding Window
Iterate through the array once while maintaining counters for the current strictly increasing streak (`inc`) and strictly decreasing streak (`dec`). Reset the appropriate counter whenever the monotonicity breaks.

1. Initialize `maxLen = 1`, `inc = 1`, and `dec = 1`.
2. Iterate from index 1 to `nums.length - 1`.
3. If `nums[i] > nums[i - 1]`, increment `inc` and reset `dec` to 1.
4. If `nums[i] < nums[i - 1]`, increment `dec` and reset `inc` to 1.
5. If `nums[i] == nums[i - 1]`, reset both `inc` and `dec` to 1.
6. Update `maxLen = Math.max(maxLen, Math.max(inc, dec))` at each step.
7. Return `maxLen`.

**Time:** O(N) · **Space:** O(1)

```java
class Solution {
    public int longestMonotonicSubarray(int[] nums) {
        int maxLen = 1;
        int inc = 1;
        int dec = 1;

        for (int i = 1; i < nums.length; i++) {
            if (nums[i] > nums[i - 1]) {
                inc++;
                dec = 1;
            } else if (nums[i] < nums[i - 1]) {
                dec++;
                inc = 1;
            } else {
                inc = 1;
                dec = 1;
            }
            maxLen = Math.max(maxLen, Math.max(inc, dec));
        }

        return maxLen;
    }
}
```

## Edge cases
- Single element array (length 1): returns 1.
- All elements are equal: returns 1 because strict monotonicity fails.
- Strictly increasing array throughout: returns array length.
- Strictly decreasing array throughout: returns array length.

## Dry run (example 1)
For nums = [1, 4, 3, 3, 2]:
- Initial state: maxLen = 1, inc = 1, dec = 1
- i = 1 (val 4 > 1): inc = 2, dec = 1, maxLen = 2
- i = 2 (val 3 < 4): inc = 1, dec = 2, maxLen = 2
- i = 3 (val 3 == 3): inc = 1, dec = 1, maxLen = 2
- i = 4 (val 2 < 3): inc = 1, dec = 2, maxLen = 2
Final answer: 2.
