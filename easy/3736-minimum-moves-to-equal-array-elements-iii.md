# 3736. Minimum Moves to Equal Array Elements III

**Difficulty:** Easy · **Topics:** Array, Math · **Language:** Java · **Day:** 24 · **Date:** 2026-11-03

🔗 [Open on LeetCode](https://leetcode.com/problems/minimum-moves-to-equal-array-elements-iii/)

> AI-generated with `gemini-3.6-flash`. Unverified. Check before trusting.

## Hint
Since you can only increase elements, what target value minimizes the required increments?

## Optimal: Greedy / Math
Since we can only increase elements, all elements must eventually reach at least the maximum value in the array. Any target value larger than the maximum would require extra moves for all elements. Thus, the optimal target value is the maximum element in `nums`. The total moves needed is the sum of differences between the maximum element and each array element.

1. Find the maximum element `maxVal` in `nums`.
2. Iterate through `nums` and accumulate `maxVal - num` into a moves counter.
3. Return the total moves counter.

**Time:** O(N) · **Space:** O(1)

```java
class Solution {
    public int minMoves(int[] nums) {
        int maxVal = nums[0];
        for (int num : nums) {
            if (num > maxVal) {
                maxVal = num;
            }
        }
        
        int moves = 0;
        for (int num : nums) {
            moves += maxVal - num;
        }
        
        return moves;
    }
}
```

## Edge cases
- Single element array (e.g., [5]) -> 0 moves.
- Array where all elements are already equal (e.g., [3, 3, 3]) -> 0 moves.
- Large variation in values (e.g., [1, 100]) -> 99 moves.

## Dry run (example 1)
For nums = [2, 1, 3]:
1. Find maximum value: maxVal = max(2, 1, 3) = 3.
2. Calculate moves:
   - For nums[0] = 2: 3 - 2 = 1 move
   - For nums[1] = 1: 3 - 1 = 2 moves
   - For nums[2] = 3: 3 - 3 = 0 moves
3. Total moves = 1 + 2 + 0 = 3.
4. Return 3.
