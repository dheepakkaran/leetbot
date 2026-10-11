# 2778. Sum of Squares of Special Elements

**Difficulty:** Easy · **Topics:** Array, Enumeration · **Language:** C++ · **Day:** 1 · **Date:** 2026-10-11

🔗 [Open on LeetCode](https://leetcode.com/problems/sum-of-squares-of-special-elements/)

> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.

## Hint
Check which 1-based indices divide the total length of the array evenly.

## Brute force
Iterate through every index from 1 to n, check if n is divisible by the index, and accumulate the square of nums[i - 1] if it is.

**Time:** O(n) · **Space:** O(1)

```cpp
class Solution {
public:
    int sumOfSquares(vector<int>& nums) {
        int n = nums.size();
        int sum = 0;
        for (int i = 1; i <= n; ++i) {
            if (n % i == 0) {
                sum += nums[i - 1] * nums[i - 1];
            }
        }
        return sum;
    }
};
```

## Optimal: Enumeration
Find all divisors of n in pairs up to sqrt(n) to avoid iterating through all n elements.

1. Initialize an accumulator sum to 0 and find the length n of nums.
2. Iterate i from 1 while i * i <= n.
3. If i divides n, add nums[i - 1]^2 to sum.
4. If i != n / i, also add nums[n / i - 1]^2 to sum.
5. Return the accumulated sum.

**Time:** O(sqrt(n)) · **Space:** O(1)

```cpp
class Solution {
public:
    int sumOfSquares(vector<int>& nums) {
        int n = nums.size();
        int sum = 0;
        for (int i = 1; i * i <= n; ++i) {
            if (n % i == 0) {
                sum += nums[i - 1] * nums[i - 1];
                if (i != n / i) {
                    sum += nums[n / i - 1] * nums[n / i - 1];
                }
            }
        }
        return sum;
    }
};
```

## Edge cases
- n = 1 (single element array): loop runs once for i = 1, handles paired divisor correctly without double counting.
- n is a prime number: only i = 1 and i = n will be added.
- n is a perfect square: i == n / i must be checked to prevent adding the square twice.

## Dry run (example 1)
For nums = [1, 2, 3, 4] with n = 4:
- i = 1: 4 % 1 == 0. Add nums[0]^2 = 1. Since 1 != 4, also add nums[3]^2 = 16. sum = 17.
- i = 2: 4 % 2 == 0. Add nums[1]^2 = 4. Since 2 == 4 / 2, do not add again. sum = 21.
- i = 3: 3 * 3 > 4, loop terminates.
Return 21.
