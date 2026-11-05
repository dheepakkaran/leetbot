# 1385. Find the Distance Value Between Two Arrays

**Difficulty:** Easy · **Topics:** Array, Two Pointers, Binary Search, Sorting · **Language:** Java · **Day:** 26 · **Date:** 2026-11-05

🔗 [Open on LeetCode](https://leetcode.com/problems/find-the-distance-value-between-two-arrays/)

> AI-generated with `gemini-3.6-flash`. Unverified. Check before trusting.

## Hint
Check if any element in arr2 falls within the range [x - d, x + d] for each x in arr1.

## Brute force
For each element `x` in `arr1`, iterate through every element `y` in `arr2`. If any `|x - y| <= d`, mark `x` as invalid and stop checking `arr2` for this element. Otherwise, increment the count.

**Time:** O(N * M) · **Space:** O(1)

```java
class Solution {
    public int findTheDistanceValue(int[] arr1, int[] arr2, int d) {
        int count = 0;
        for (int x : arr1) {
            boolean valid = true;
            for (int y : arr2) {
                if (Math.abs(x - y) <= d) {
                    valid = false;
                    break;
                }
            }
            if (valid) {
                count++;
            }
        }
        return count;
    }
}
```

## Optimal: Binary Search
Sort `arr2`. For each element `x` in `arr1`, use binary search to determine if any element in `arr2` lies in the closed range `[x - d, x + d]`. If no element exists in this range, `x` contributes to the distance value count.

1. Sort `arr2` in ascending order.
2. Initialize `count = 0`.
3. For each element `x` in `arr1`, perform a binary search on `arr2` to check for elements in range `[x - d, x + d]`.
4. If `arr2[mid]` falls inside `[x - d, x + d]`, then `x` is invalid.
5. If `arr2[mid] < x - d`, search the right half; if `arr2[mid] > x + d`, search the left half.
6. If binary search completes without finding any such element, increment `count`.
7. Return `count`.

**Time:** O((M + N) log M) · **Space:** O(log M)

```java
import java.util.Arrays;

class Solution {
    public int findTheDistanceValue(int[] arr1, int[] arr2, int d) {
        Arrays.sort(arr2);
        int count = 0;
        for (int x : arr1) {
            if (isValid(arr2, x, d)) {
                count++;
            }
        }
        return count;
    }

    private boolean isValid(int[] arr2, int val, int d) {
        int low = 0, high = arr2.length - 1;
        while (low <= high) {
            int mid = low + (high - low) / 2;
            if (arr2[mid] >= val - d && arr2[mid] <= val + d) {
                return false;
            }
            if (arr2[mid] < val - d) {
                low = mid + 1;
            } else {
                high = mid - 1;
            }
        }
        return true;
    }
}
```

## Edge cases
- d = 0: strictly requires no exact duplicate values between arr1 element and arr2.
- Negative numbers: array elements can be negative (e.g., -1000 to 1000), range [x - d, x + d] correctly handles negative bounds.
- Single element arrays: arr1 or arr2 containing only 1 element.

## Dry run (example 1)
arr1 = [4, 5, 8], arr2 = [10, 9, 1, 8], d = 2
Sorted arr2 = [1, 8, 9, 10]

1. x = 4, target range = [4 - 2, 4 + 2] = [2, 6]:
   - mid=1 (val=8) > 6 -> high=0
   - mid=0 (val=1) < 2 -> low=1
   - Loop ends -> No element in [2, 6] -> 4 is VALID. (count = 1)

2. x = 5, target range = [5 - 2, 5 + 2] = [3, 7]:
   - mid=1 (val=8) > 7 -> high=0
   - mid=0 (val=1) < 3 -> low=1
   - Loop ends -> No element in [3, 7] -> 5 is VALID. (count = 2)

3. x = 8, target range = [8 - 2, 8 + 2] = [6, 10]:
   - mid=1 (val=8) is in [6, 10] -> INVALID. (count remains 2)

Result: 2
