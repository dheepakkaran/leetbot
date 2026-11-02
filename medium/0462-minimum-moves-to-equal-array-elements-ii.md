# 462. Minimum Moves to Equal Array Elements II

**Difficulty:** Medium · **Topics:** Array, Math, Sorting · **Language:** Java · **Day:** 23 · **Date:** 2026-11-02

🔗 [Open on LeetCode](https://leetcode.com/problems/minimum-moves-to-equal-array-elements-ii/)

> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.

## Hint
Consider which statistical measure minimizes the sum of absolute deviations.

## Brute force
Try choosing each element in the array as the target value and calculate the total number of moves needed to convert all elements to that value. The optimal value must be one of the numbers already in the array.

**Time:** O(n^2) · **Space:** O(1)

```java
class Solution {
    public int minMoves2(int[] nums) {
        long minMoves = Long.MAX_VALUE;
        for (int target : nums) {
            long currentMoves = 0;
            for (int x : nums) {
                currentMoves += Math.abs((long) x - target);
            }
            minMoves = Math.min(minMoves, currentMoves);
        }
        return (int) minMoves;
    }
}
```

## Optimal: Median / Sorting
The sum of absolute differences |x - k| is minimized when k is chosen as the median of the array. Sorting the array brings the median to index n / 2. We can sum up the absolute differences between each element and the median, or pair elements from opposite ends using two pointers.

1. Sort the array nums in non-decreasing order.
2. Initialize two pointers, left at 0 and right at nums.length - 1.
3. While left < right, add (nums[right] - nums[left]) to the total moves, then increment left and decrement right.
4. Return the total moves accumulated.

**Time:** O(n log n) · **Space:** O(1)

```java
import java.util.Arrays;

class Solution {
    public int minMoves2(int[] nums) {
        Arrays.sort(nums);
        int moves = 0;
        int left = 0, right = nums.length - 1;
        while (left < right) {
            moves += nums[right] - nums[left];
            left++;
            right--;
        }
        return moves;
    }
}
```

## Edge cases
- Array with a single element: 0 moves needed.
- Array with even number of elements: any value between the two middle elements yields the minimum moves.
- All elements already equal: 0 moves needed.
- Negative numbers and large values up to 10^9: subtraction nums[right] - nums[left] cannot overflow 32-bit signed int because the result fits in integer as guaranteed by the problem.

## Dry run (example 1)
For nums = [1, 2, 3]:
1. Sort nums: [1, 2, 3].
2. Initialize left = 0, right = 2, moves = 0.
3. left < right: moves += nums[2] - nums[0] = 3 - 1 = 2; left = 1, right = 1.
4. left == right, loop terminates.
5. Return moves = 2.
