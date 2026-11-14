# 3364. Minimum Positive Sum Subarray

**Difficulty:** Easy · **Topics:** Array, Sliding Window, Prefix Sum · **Language:** Java · **Day:** 35 · **Date:** 2026-11-14

🔗 [Open on LeetCode](https://leetcode.com/problems/minimum-positive-sum-subarray/)

> AI-generated with `gemini-3.6-flash`. Unverified. Check before trusting.

## Hint
Consider maintaining prefix sums in a balanced BST (TreeMap) for a sliding window of valid start indices.

## Brute force
Iterate through all allowed subarray lengths from l to r. For each length, use a sliding window to calculate the sum of every subarray of that length and track the minimum positive sum.

**Time:** O(N * (r - l + 1)) · **Space:** O(1)

```java
class Solution {
    public int minimumSumSubarray(List<Integer> nums, int l, int r) {
        int minSum = Integer.MAX_VALUE;
        int n = nums.size();
        
        for (int len = l; len <= r; len++) {
            int currentSum = 0;
            for (int i = 0; i < len; i++) {
                currentSum += nums.get(i);
            }Division:
            if (currentSum > 0) {
                minSum = Math.min(minSum, currentSum);
            }
            for (int i = len; i < n; i++) {
                currentSum += nums.get(i) - nums.get(i - len);
                if (currentSum > 0) {
                    minSum = Math.min(minSum, currentSum);
                }
            }
        }
        
        return minSum == Integer.MAX_VALUE ? -1 : minSum;
    }
}
```

## Optimal: Prefix Sum + Sliding Window + TreeMap
Using prefix sums, any subarray sum ending at index i with length between l and r is pref[i] - pref[j], where j is in [i - r, i - l]. To minimize pref[i] - pref[j] > 0, we need to find the largest pref[j] in that index range such that pref[j] < pref[i]. A TreeMap maintains the frequency of prefix sums in the sliding window of size (r - l + 1), allowing O(log N) lookup using lowerKey().

1. Compute the prefix sum array `pref` of length `N + 1`.
2. Initialize a `TreeMap<Integer, Integer>` to maintain a sliding window of available prefix sums `pref[j]` where `i - r <= j <= i - l`.
3. Iterate `i` from `l` to `N`:
4. 1. Insert `pref[i - l]` into the TreeMap.
5. 2. If `i - r - 1 >= 0`, remove `pref[i - r - 1]` from the TreeMap to maintain the window size.
6. 3. Use `map.lowerKey(pref[i])` to find the largest valid `pref[j] < pref[i]`.
7. 4. Update `minSum` with `pref[i] - lowerKey` if it exists.
8. Return `minSum` if found, else `-1`.

**Time:** O(N log(r - l + 1)) · **Space:** O(N)

```java
class Solution {
    public int minimumSumSubarray(List<Integer> nums, int l, int r) {
        int n = nums.size();
        int[] pref = new int[n + 1];
        for (int i = 0; i < n; i++) {
            pref[i + 1] = pref[i] + nums.get(i);
        }

        int minSum = Integer.MAX_VALUE;
        TreeMap<Integer, Integer> map = new TreeMap<>();

        for (int i = l; i <= n; i++) {
            int addVal = pref[i - l];
            map.put(addVal, map.getOrDefault(addVal, 0) + 1);

            if (i - r - 1 >= 0) {
                int removeVal = pref[i - r - 1];
                int count = map.get(removeVal);
                if (count == 1) {
                    map.remove(removeVal);
                } else {
                    map.put(removeVal, count - 1);
                }
            }

            Integer lower = map.lowerKey(pref[i]);
            if (lower != null) {
                minSum = Math.min(minSum, pref[i] - lower);
            }
        }

        return minSum == Integer.MAX_VALUE ? -1 : minSum;
    }
}
```

## Edge cases
- No subarray has a sum > 0 (e.g., all negative elements): return -1.
- l == r: fixed subarray size, window contains exactly 1 prefix sum candidate at each step.
- l == 1 and r == nums.size(): any contiguous subarray is valid.

## Dry run (example 1)
For nums = [3, -2, 1, 4], l = 2, r = 3:
- pref = [0, 3, 1, 2, 6]
- i = 2: Add pref[0]=0 -> map={0:1}. pref[2]=1. lowerKey(1)=0 -> candidate = 1-0 = 1. minSum = 1.
- i = 3: Add pref[1]=3 -> map={0:1, 3:1}. pref[3]=2. lowerKey(2)=0 -> candidate = 2-0 = 2. minSum = min(1, 2) = 1.
- i = 4: Add pref[2]=1 -> map={0:1, 1:1, 3:1}. Remove pref[0]=0 -> map={1:1, 3:1}. pref[4]=6. lowerKey(6)=3 -> candidate = 6-3 = 3. minSum = min(1, 3) = 1.
- Result: 1.
