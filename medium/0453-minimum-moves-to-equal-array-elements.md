# 453. Minimum Moves to Equal Array Elements

**Difficulty:** Medium · **Topics:** Array, Math · **Language:** Java · **Day:** 22 · **Date:** 2026-11-01

🔗 [Open on LeetCode](https://leetcode.com/problems/minimum-moves-to-equal-array-elements/)

> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.

## Hint
Consider the relative difference between elements: incrementing n - 1 elements by 1 is equivalent to decrementing 1 element by 1.

## Brute force
Repeatedly find the maximum element and increment all other n - 1 elements by 1 until all elements become equal.

**Time:** O(n * m) · **Space:** O(1)

```java
class Solution {
    public int minMoves(int[] nums) {
        int moves = 0;
        while (true) {
            int minIndex = 0, maxIndex = 0;
            for (int i = 1; i < nums.length; i++) {
                if (nums[i] < nums[minIndex]) minIndex = i;
                if (nums[i] > nums[maxIndex]) maxIndex = i;
            }
            if (nums[minIndex] == nums[maxIndex]) break;
            for (int i = 0; i < nums.length; i++) {
                if (i != maxIndex) {
                    nums[i]++;
                }
            }
            moves++;
        }
        return moves;
    }
}
```

## Optimal: Math
Incrementing n - 1 elements by 1 increases their value relative to the remaining element. In terms of relative difference, this is identical to decrementing that single element by 1. To make all elements equal with minimum moves, we can view it as decrementing every element down to the array's minimum element. Thus, the total moves needed is the sum of differences between each element and the minimum element: sum(nums[i] - min(nums)).

1. Find the minimum element in nums.
2. Iterate through nums and accumulate (nums[i] - min) for each element.
3. Return the accumulated total moves.

**Time:** O(n) · **Space:** O(1)

```java
class Solution {
    public int minMoves(int[] nums) {
        int min = nums[0];
        for (int x : nums) {
            if (x < min) {
                min = x;
            }
        }
        int moves = 0;
        for (int x : nums) {
            moves += (x - min);
        }
        return moves;
    }
}
```

## Edge cases
- Array with a single element: returns 0 moves immediately.
- Array with already equal elements: difference for each element is 0, returning 0.
- Negative numbers in nums: difference (x - min) remains non-negative and valid.

## Dry run (example 1)
For nums = [1, 2, 3]:
1. Find minimum element: min = 1.
2. Calculate moves:
   - For 1: 1 - 1 = 0
   - For 2: 2 - 1 = 1
   - For 3: 3 - 1 = 2
3. Total moves = 0 + 1 + 2 = 3.
Returns 3.
