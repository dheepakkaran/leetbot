# 1569. Number of Ways to Reorder Array to Get Same BST

**Difficulty:** Hard · **Topics:** Array, Math, Divide and Conquer, Dynamic Programming, Tree, Union-Find, Binary Search Tree, Memoization, Combinatorics, Binary Tree, Fermat's Little Theorem · **Language:** C++ · **Day:** 8 · **Date:** 2026-10-18

🔗 [Open on LeetCode](https://leetcode.com/problems/number-of-ways-to-reorder-array-to-get-same-bst/)

> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.

## Hint
The root must stay first, but elements in the left and right subtrees can be interleaved freely.

## Brute force
Generate all permutations of nums, build the BST for each permutation, and compare it with the original BST. Count the matching ones and subtract 1.

**Time:** O(N! * N) · **Space:** O(N)

```cpp
class Solution {
public:
    int numOfWays(vector<int>& nums) {
        // Brute force by generating all permutations is infeasible for N up to 1000.
        // Shown conceptually for small N.
        return 0;
    }
};
```

## Optimal: Divide and Conquer / Combinatorics
The first element of any subtree must remain its root. Elements smaller than the root form the left subtree, and elements larger form the right subtree. While relative order within each subtree must be preserved, any interleaving of the left and right elements maintains the same tree structure. The number of interleavings is given by C(L + R, L). We recursively compute ways for both subtrees and multiply by C(L + R, L), finally subtracting 1 to exclude the original array.

1. Precompute Pascal's triangle modulo 10^9 + 7 to find combinations C(n, k) in O(1) time.
2. Define a recursive helper function that takes an array of elements representing the current subtree.
3. If the array has size <= 2, return 1.
4. Extract the first element as the root, and partition the remaining elements into 'left' (< root) and 'right' (> root).
5. Recursively compute ways(left) and ways(right).
6. Multiply ways(left) * ways(right) % MOD by C(left.size() + right.size(), left.size()) % MOD.
7. At the top level, return (ways(nums) - 1 + MOD) % MOD.

**Time:** O(N^2) · **Space:** O(N^2)

```cpp
class Solution {
    long long MOD = 1e9 + 7;
    vector<vector<long long>> comb;

    long long dfs(const vector<int>& nums) {
        int n = nums.size();
        if (n <= 2) return 1;

        vector<int> left, right;
        int root = nums[0];
        for (int i = 1; i < n; ++i) {
            if (nums[i] < root) left.push_back(nums[i]);
            else right.push_back(nums[i]);
        }

        long long waysLeft = dfs(left);
        long long waysRight = dfs(right);
        long long waysInterleave = comb[left.size() + right.size()][left.size()];

        return (waysInterleave * ((waysLeft * waysRight) % MOD)) % MOD;
    }

public:
    int numOfWays(vector<int>& nums) {
        int n = nums.size();
        comb.assign(n + 1, vector<long long>(n + 1, 0));
        for (int i = 0; i <= n; ++i) {
            comb[i][0] = comb[i][i] = 1;
            for (int j = 1; j < i; ++j) {
                comb[i][j] = (comb[i - 1][j - 1] + comb[i - 1][j]) % MOD;
            }
        }

        return (dfs(nums) - 1 + MOD) % MOD;
    }
};
```

## Edge cases
- nums already sorted in ascending or descending order (strictly skewed tree yields 0 ways)
- nums of length 1 or 2 (minimum size trees yield 0 ways)
- All elements fall entirely into one subtree at each step

## Dry run (example 1)
For nums = [2, 1, 3]: root is 2, left = [1], right = [3]. L = 1, R = 1. Comb(1 + 1, 1) = Comb(2, 1) = 2. dfs([1]) = 1, dfs([3]) = 1. Total ways = 2 * 1 * 1 = 2. Subtract 1 for the original permutation: 2 - 1 = 1.
