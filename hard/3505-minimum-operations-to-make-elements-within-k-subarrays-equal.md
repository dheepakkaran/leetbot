# 3505. Minimum Operations to Make Elements Within K Subarrays Equal

**Difficulty:** Hard · **Topics:** Array, Hash Table, Math, Dynamic Programming, Sliding Window, Heap (Priority Queue) · **Language:** Java · **Day:** 25 · **Date:** 2026-11-04

🔗 [Open on LeetCode](https://leetcode.com/problems/minimum-operations-to-make-elements-within-k-subarrays-equal/)

> AI-generated with `gemini-3.6-flash`. Unverified. Check before trusting.

## Hint
Find the minimum operation cost for every window of size x using a sliding median, then apply dynamic programming to select k non-overlapping windows.

## Brute force
For every possible starting position of a window of size x, sort the window elements to find the median and calculate the median cost. Then, use recursion with memoization to find the minimum sum of costs for choosing k non-overlapping windows.

**Time:** O(N * x log x + k * N) · **Space:** O(N * k)

```java
class Solution {
    public long minOperations(int[] nums, int x, int k) {
        int n = nums.length;
        long[] cost = new long[n - x + 1];
        for (int i = 0; i <= n - x; i++) {
            int[] window = java.util.Arrays.copyOfRange(nums, i, i + x);
            java.util.Arrays.sort(window);
            long median = window[x / 2];
            long c = 0;
            for (int val : window) {
                c += Math.abs((long) val - median);
            }
            cost[i] = c;
        }
        long[][] dp = new long[k + 1][n + 1];
        for (int j = 1; j <= k; j++) {
            java.util.Arrays.fill(dp[j], Long.MAX_VALUE / 2);
        }
        for (int j = 1; j <= k; j++) {
            for (int i = j * x; i <= n; i++) {
                dp[j][i] = Math.min(dp[j][i - 1], dp[j - 1][i - x] + cost[i - x]);
            }
        }
        return dp[k][n];
    }
}
```

## Optimal: Sliding Window + Dynamic Programming + Heap (Priority Queue)
The optimal target value for all elements in a subarray of size x to be equal is the median of that subarray. We maintain the median and element sums of a sliding window of size x using two heaps with lazy deletion in O(N log x) time. After computing `cost[i]` for all valid window start positions `i`, we use dynamic programming: `dp[j][i]` stores the minimum cost to choose `j` non-overlapping subarrays within the prefix `nums[0...i-1]`. The transition is `dp[j][i] = min(dp[j][i-1], dp[j-1][i-x] + cost[i-x])`.

1. Use two heaps (max-heap for smaller half, min-heap for larger half) to maintain the median of a sliding window of size x.
2. Calculate the operational cost for each window of size x using sum differences relative to the median.
3. Define `dp[j][i]` as the minimum cost to pick `j` non-overlapping windows of length x ending at or before index `i`.
4. Iterate `j` from 1 to `k` and `i` from `j * x` to `N` to update DP states.
5. Return `dp[k][N]` as the result.

**Time:** O(N log x + k * N) · **Space:** O(k * N)

```java
class Solution {
    static class MedianFinder {
        private final java.util.PriorityQueue<Long> lower = new java.util.PriorityQueue<>(java.util.Collections.reverseOrder());
        private final java.util.PriorityQueue<Long> upper = new java.util.PriorityQueue<>();
        private final java.util.Map<Long, Integer> delayedLower = new java.util.HashMap<>();
        private final java.util.Map<Long, Integer> delayedUpper = new java.util.HashMap<>();
        private int lowerSize = 0, upperSize = 0;
        private long sumLower = 0, sumUpper = 0;

        public void add(long x) {
            if (lower.isEmpty() || x <= lower.peek()) {
                lower.add(x);
                sumLower += x;
                lowerSize++;
            } else {
                upper.add(x);
                sumUpper += x;
                upperSize++;
            }
            rebalance();
        }

        public void remove(long x) {
            if (!lower.isEmpty() && x <= lower.peek()) {
                delayedLower.put(x, delayedLower.getOrDefault(x, 0) + 1);
                sumLower -= x;
                lowerSize--;
            } else {
                delayedUpper.put(x, delayedUpper.getOrDefault(x, 0) + 1);
                sumUpper -= x;
                upperSize--;
            }
            prune(lower, delayedLower);
            prune(upper, delayedUpper);
            rebalance();
        }

        private void prune(java.util.PriorityQueue<Long> pq, java.util.Map<Long, Integer> delayed) {
            while (!pq.isEmpty() && delayed.getOrDefault(pq.peek(), 0) > 0) {
                long val = pq.poll();
                delayed.put(val, delayed.get(val) - 1);
            }
        }

        private void rebalance() {
            while (lowerSize > upperSize + 1) {
                prune(lower, delayedLower);
                long val = lower.poll();
                upper.add(val);
                sumLower -= val;
                sumUpper += val;
                lowerSize--;
                upperSize++;
                prune(lower, delayedLower);
            }
            while (lowerSize < upperSize) {
                prune(upper, delayedUpper);
                long val = upper.poll();
                lower.add(val);
                sumUpper -= val;
                sumLower += val;
                upperSize--;
                lowerSize++;
                prune(upper, delayedUpper);
            }
            prune(lower, delayedLower);
            prune(upper, delayedUpper);
        }

        public long getCost(int windowSize) {
            long median = lower.peek();
            if (windowSize % 2 == 1) {
                return sumUpper - sumLower + median;
            } else {
                return sumUpper - sumLower;
            }
        }
    }

    public long minOperations(int[] nums, int x, int k) {
        int n = nums.length;
        long[] cost = new long[n - x + 1];
        MedianFinder finder = new MedianFinder();

        for (int i = 0; i < n; i++) {
            finder.add(nums[i]);
            if (i >= x) {
                finder.remove(nums[i - x]);
            }
            if (i >= x - 1) {
                cost[i - x + 1] = finder.getCost(x);
            }
        }

        long[][] dp = new long[k + 1][n + 1];
        for (int j = 1; j <= k; j++) {
            java.util.Arrays.fill(dp[j], Long.MAX_VALUE / 2);
        }

        for (int j = 1; j <= k; j++) {
            for (int i = j * x; i <= n; i++) {
                dp[j][i] = Math.min(dp[j][i - 1], dp[j - 1][i - x] + cost[i - x]);
            }
        }

        return dp[k][n];
    }
}
```

## Edge cases
- k * x == nums.length: The subarrays cover the array entirely without gaps.
- x is even vs x is odd: Cost calculation slightly differs due to exact median position.
- Negative array elements: Sums and costs must handle negative inputs without underflow.
- Large cost sum: Intermediate sums exceed Integer.MAX_VALUE, so long must be used throughout.

## Dry run (example 1)
For nums = [5, -2, 1, 3, 7, 3, 6, 4, -1], x = 3, k = 2:
1. Compute costs for all size-3 windows:
   - Window 0 [5,-2,1]: sorted [-2,1,5], median 1, cost = 7
   - Window 1 [-2,1,3]: sorted [-2,1,3], median 1, cost = 5
   - Window 2 [1,3,7]: sorted [1,3,7], median 3, cost = 6
   - Window 3 [3,7,3]: sorted [3,3,7], median 3, cost = 4
   - Window 4 [7,3,6]: sorted [3,6,7], median 6, cost = 4
   - Window 5 [3,6,4]: sorted [3,4,6], median 4, cost = 3
   - Window 6 [6,4,-1]: sorted [-1,4,6], median 4, cost = 7
   cost array = [7, 5, 6, 4, 4, 3, 7].
2. DP for k = 2:
   - Pick window starting at index 1 (cost 5) and index 5 (cost 3).
   - Total cost = 5 + 3 = 8.
