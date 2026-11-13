# 3420. Count Non-Decreasing Subarrays After K Operations

**Difficulty:** Hard · **Topics:** Array, Stack, Segment Tree, Queue, Sliding Window, Monotonic Stack, Monotonic Queue · **Language:** Java · **Day:** 34 · **Date:** 2026-11-13

🔗 [Open on LeetCode](https://leetcode.com/problems/count-non-decreasing-subarrays-after-k-operations/)

> AI-generated with `gemini-3.6-flash`. Unverified. Check before trusting.

## Hint
Process left endpoints in reverse while maintaining a monotonic deque of prefix maximum blocks to track operation costs efficiently.

## Brute force
Iterate through all possible subarrays nums[L...R]. For each subarray, compute the required operations by calculating the sum of (max(nums[L...i]) - nums[i]) for all i in [L, R]. Count how many subarrays need at most k operations.

**Time:** O(N^2) · **Space:** O(1)

```java
class Solution {
    public long countNonDecreasingSubarrays(int[] nums, int k) {
        int n = nums.length;
        long count = 0;
        for (int l = 0; l < n; l++) {
            long cost = 0;
            int maxVal = 0;
            for (int r = l; r < n; r++) {
                maxVal = Math.max(maxVal, nums[r]);
                cost += (maxVal - nums[r]);
                if (cost <= k) {
                    count++;
                } else {
                    break;
                }
            }
        }
        return count;
    }
}
```

## Optimal: Sliding Window + Monotonic Deque
Maintain a sliding window [L, R] where R is the rightmost valid index such that the cost of making nums[L...R] non-decreasing is <= k. As L moves left (from n-1 down to 0), the max prefix values over indices [L, R] are represented as a monotonic deque of contiguous blocks (start, end, val).

When L decreases to L-1:
1. A new block starting at L-1 with value nums[L-1] is prepended to the deque.
2. Any blocks at the front of the deque with val <= nums[L-1] are merged into this new block, and total_cost is updated with the cost increase.
3. While total_cost > k, we decrement R, subtracting index R's cost contribution from total_cost and shrinking/popping the rightmost block of the deque.
4. Add (R - L + 1) to the total count.

1. Initialize total_cost = 0, R = n - 1, ans = 0, and a double-ended queue storing blocks (start, end, val).
2. Iterate L from n - 1 down to 0.
3. Create a block for L with val = nums[L]. While the front block has val <= nums[L], pop it, add its cost increase to total_cost, and extend the new block's end.
4. Push the new block to the front of the deque.
5. While total_cost > k, remove index R from the window: subtract (last_block.val - nums[R]) from total_cost and shrink/pop the rightmost block, then decrement R.
6. Add (R - L + 1) to ans.
7. Return ans.

**Time:** O(N) · **Space:** O(N)

```java
import java.util.ArrayDeque;
import java.util.Deque;

class Solution {
    static class Block {
        int start, end;
        long val;
        Block(int start, int end, long val) {
            this.start = start;
            this.end = end;
            this.val = val;
        }
    }

    public long countNonDecreasingSubarrays(int[] nums, int k) {
        int n = nums.length;
        Deque<Block> deque = new ArrayDeque<>();
        long totalCost = 0;
        long ans = 0;
        int r = n - 1;

        for (int l = n - 1; l >= 0; l--) {
            Block b = new Block(l, l, nums[l]);
            while (!deque.isEmpty() && deque.peekFirst().val <= nums[l]) {
                Block first = deque.pollFirst();
                long len = first.end - first.start + 1;
                totalCost += (nums[l] - first.val) * len;
                b.end = first.end;
            }
            deque.addFirst(b);

            while (totalCost > k) {
                Block last = deque.peekLast();
                totalCost -= (last.val - nums[r]);
                last.end--;
                if (last.start > last.end) {
                    deque.pollLast();
                }
                r--;
            }

            ans += (r - l + 1);
        }

        return ans;
    }
}
```

## Edge cases
- Single element array (n = 1): cost is 0 <= k, returns 1.
- Array already non-decreasing: operation cost is 0 for all subarrays, returns n * (n + 1) / 2.
- Strictly decreasing array: large operation costs, k limits window sizes properly.
- Large values of nums[i] and k (up to 10^9): integer overflow prevented by using long for costs.

## Dry run (example 1)
Walkthrough with nums = [6, 3, 1, 2, 4, 4], k = 7:
- L = 5 (nums[5] = 4): Block(5, 5, 4) added. cost = 0 <= 7. R = 5. ans += 1 (1).
- L = 4 (nums[4] = 4): Merges Block(5,5,4) -> Block(4, 5, 4). cost = 0. R = 5. ans += 2 (3).
- L = 3 (nums[3] = 2): Block(3, 3, 2) added. cost = 0. R = 5. ans += 3 (6).
- L = 2 (nums[2] = 1): Block(2, 2, 1) added. cost = 0. R = 5. ans += 4 (10).
- L = 1 (nums[1] = 3): Pops (2,2,1) [+2 cost] and (3,3,2) [+1 cost]. Adds Block(1,3,3). totalCost = 3 <= 7. R = 5. ans += 5 (15).
- L = 0 (nums[0] = 6): Pops (1,3,3) [+9 cost] and (4,5,4) [+4 cost]. Adds Block(0,5,6). totalCost = 16 > 7.
  - Shrink R=5: cost -= (6-4)=2 -> 14
  - Shrink R=4: cost -= (6-4)=2 -> 12
  - Shrink R=3: cost -= (6-2)=4 -> 8
  - Shrink R=2: cost -= (6-1)=5 -> 3 <= 7. R ends at 1.
  - ans += (1 - 0 + 1) = 2 (17).
Result = 17.
