# 3727. Maximum Alternating Sum of Squares

**Difficulty:** Medium · **Topics:** Array, Greedy, Sorting · **Language:** C++ · **Day:** 3 · **Date:** 2026-10-13

🔗 [Open on LeetCode](https://leetcode.com/problems/maximum-alternating-sum-of-squares/)

> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.

## Hint
Count how many positive and negative terms appear in the alternating sum, then assign the largest squares accordingly.

## Brute force
Generate all permutations of the array, compute the alternating score of squares for each permutation, and find the maximum.

**Time:** O(n! * n) · **Space:** O(n)

```cpp
class Solution {
public:
    long long maxAlternatingSum(vector<int>& nums) {
        int n = nums.size();
        vector<int> p = nums;
        sort(p.begin(), p.end());
        long long maxScore = LLONG_MIN;
        do {
            long long currentScore = 0;
            for (int i = 0; i < n; ++i) {
                long long sq = 1LL * p[i] * p[i];
                if (i % 2 == 0) currentScore += sq;
                else currentScore -= sq;
            }
            maxScore = max(maxScore, currentScore);
        } while (next_permutation(p.begin(), p.end()));
        return maxScore;
    }
};
```

## Optimal: Greedy
In any valid rearrangement, exactly ceil(n / 2) elements will be placed at even indices (positive contribution) and floor(n / 2) elements will be placed at odd indices (negative contribution). To maximize the total score, greedily assign the elements with the largest squares to the even indices and those with the smallest squares to the odd indices.

1. Sort the array by the absolute value of each element in descending order.
2. The first ceil(n / 2) = (n + 1) / 2 elements will have positive contributions.
3. The remaining floor(n / 2) = n / 2 elements will have negative contributions.
4. Sum the squares of the first (n + 1) / 2 elements and subtract the squares of the remaining elements, using 64-bit integers to prevent overflow.

**Time:** O(n log n) · **Space:** O(1)

```cpp
class Solution {
public:
    long long maxAlternatingSum(vector<int>& nums) {
        int n = nums.size();
        sort(nums.begin(), nums.end(), [](int a, int b) {
            return std::abs(a) > std::abs(b);
        });
        
        long long score = 0;
        int positiveCount = (n + 1) / 2;
        for (int i = 0; i < n; ++i) {
            long long sq = 1LL * nums[i] * nums[i];
            if (i < positiveCount) {
                score += sq;
            } else {
                score -= sq;
            }
        }
        return score;
    }
};
```

## Edge cases
- n = 1: Only a single element, its square is returned with a positive sign.
- All elements are negative or zero: Absolute values correctly handle negative numbers and zeroes.
- Large values: Elements up to 40,000 squared require 64-bit integer (`long long`) to avoid overflow during summation.

## Dry run (example 1)
For nums = [1, 2, 3]:
1. n = 3, positiveCount = (3 + 1) / 2 = 2.
2. Sort descending by absolute value: nums becomes [3, 2, 1].
3. Elements at index 0 and 1 are added: 3^2 + 2^2 = 9 + 4 = 13.
4. Element at index 2 is subtracted: 13 - 1^2 = 12.
5. Return 12.
