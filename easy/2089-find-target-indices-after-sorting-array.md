# 2089. Find Target Indices After Sorting Array

**Difficulty:** Easy · **Topics:** Array, Binary Search, Sorting · **Language:** C++ · **Day:** 9 · **Date:** 2026-10-19

🔗 [Open on LeetCode](https://leetcode.com/problems/find-target-indices-after-sorting-array/)

> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.

## Hint
Consider how the counts of elements strictly less than and equal to the target determine its final positions without full sorting.

## Brute force
Sort the input array in non-decreasing order, then iterate through the sorted array to find and record all indices where the element equals the target.

**Time:** O(n log n) · **Space:** O(1)

```cpp
class Solution {
public:
    vector<int> targetIndices(vector<int>& nums, int target) {
        sort(nums.begin(), nums.end());
        vector<int> result;
        for (int i = 0; i < nums.size(); ++i) {
            if (nums[i] == target) {
                result.push_back(i);
            }
        }
        return result;
    }
};
```

## Optimal: Counting
In a sorted array, all elements strictly less than target appear before target, and all elements equal to target appear consecutively immediately after. By counting how many numbers are smaller than target and how many equal target in a single pass, we can directly generate the target indices.

1. Initialize two counters: `lessCount = 0` and `equalCount = 0`.
2. Iterate through `nums`: increment `lessCount` if `num < target`, and `equalCount` if `num == target`.
3. Construct the result vector containing indices from `lessCount` to `lessCount + equalCount - 1`.
4. Return the result vector.

**Time:** O(n) · **Space:** O(1)

```cpp
class Solution {
public:
    vector<int> targetIndices(vector<int>& nums, int target) {
        int lessCount = 0;
        int equalCount = 0;
        
        for (int num : nums) {
            if (num < target) {
                lessCount++;
            } else if (num == target) {
                equalCount++;
            }
        }
        
        vector<int> result;
        for (int i = 0; i < equalCount; ++i) {
            result.push_back(lessCount + i);
        }
        
        return result;
    }
};
```

## Edge cases
- Target does not exist in nums (returns empty list).
- All elements in nums are equal to target.
- Array contains only one element (nums.size() == 1).

## Dry run (example 1)
For nums = [1, 2, 5, 2, 3] and target = 2:
1. 1 < 2: lessCount = 1
2. 2 == 2: equalCount = 1
3. 5 > 2: no change
4. 2 == 2: equalCount = 2
5. 3 > 2: no change
Final counts: lessCount = 1, equalCount = 2.
Output indices start at lessCount (1) for equalCount (2) times: [1, 2].
