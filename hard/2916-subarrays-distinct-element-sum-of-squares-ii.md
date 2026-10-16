# 2916. Subarrays Distinct Element Sum of Squares II

**Difficulty:** Hard · **Topics:** Array, Hash Table, Binary Indexed Tree, Segment Tree · **Language:** C++ · **Day:** 6 · **Date:** 2026-10-16

🔗 [Open on LeetCode](https://leetcode.com/problems/subarrays-distinct-element-sum-of-squares-ii/)

> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.

## Hint
Consider how the distinct count of subarrays ending at index j changes from j - 1 when appending nums[j].

## Brute force
For every starting index i, iterate through all ending indices j and maintain a hash set or frequency map to track distinct elements, accumulating the square of the distinct count.

**Time:** O(n^2) · **Space:** O(n)

```cpp
class Solution {
public:
    int sumCounts(vector<int>& nums) {
        int n = nums.size();
        long long ans = 0;
        const int MOD = 1e9 + 7;
        for (int i = 0; i < n; ++i) {
            unordered_set<int> seen;
            for (int j = i; j < n; ++j) {
                seen.insert(nums[j]);
                long long cnt = seen.size();
                ans = (ans + cnt * cnt) % MOD;
            }
        }
        return ans;
    }
};
```

## Optimal: Segment Tree
Let f(i, j) be the distinct count of nums[i..j]. When moving from j - 1 to j, f(i, j) increases by 1 for all i in (last_pos[nums[j]], j], and remains unchanged for i <= last_pos[nums[j]]. Since (f + 1)^2 = f^2 + 2f + 1, a segment tree with lazy propagation can maintain both the sum of f and the sum of f^2 over all active subarray start points.

1. Build a segment tree over indices [0, n - 1] where each node tracks sum1 = sum(f(i)), sum2 = sum(f(i)^2), and a lazy tag for range additions.
2. When updating a node of length len by adding v: sum2 becomes sum2 + 2 * v * sum1 + v^2 * len; sum1 becomes sum1 + v * len.
3. Track the last seen index of each value using an array or hash map.
4. Iterate j from 0 to n - 1: find the previous occurrence of nums[j] (let it be last, default -1). Update the range [last + 1, j] with +1.
5. Add the total sum of squares from the segment tree to the running answer, taking modulo 10^9 + 7.
6. Update the last seen index of nums[j] to j and return the total answer.

**Time:** O(n log n) · **Space:** O(n + max(nums))

```cpp
class Solution {
    static const int MOD = 1e9 + 7;

    struct Node {
        long long sum1 = 0;
        long long sum2 = 0;
        long long lazy = 0;
    };

    vector<Node> tree;

    void apply(int node, int l, int r, long long v) {
        long long len = r - l + 1;
        tree[node].sum2 = (tree[node].sum2 + 2 * v % MOD * tree[node].sum1 % MOD + v * v % MOD * len) % MOD;
        tree[node].sum1 = (tree[node].sum1 + v * len) % MOD;
        tree[node].lazy = (tree[node].lazy + v) % MOD;
    }

    void pushDown(int node, int l, int r) {
        if (tree[node].lazy != 0) {
            int mid = l + (r - l) / 2;
            apply(2 * node, l, mid, tree[node].lazy);
            apply(2 * node + 1, mid + 1, r, tree[node].lazy);
            tree[node].lazy = 0;
        }
    }

    void pushUp(int node) {
        tree[node].sum1 = (tree[2 * node].sum1 + tree[2 * node + 1].sum1) % MOD;
        tree[node].sum2 = (tree[2 * node].sum2 + tree[2 * node + 1].sum2) % MOD;
    }

    void update(int node, int l, int r, int ql, int qr, long long v) {
        if (ql <= l && r <= qr) {
            apply(node, l, r, v);
            return;
        }
        pushDown(node, l, r);
        int mid = l + (r - l) / 2;
        if (ql <= mid) update(2 * node, l, mid, ql, qr, v);
        if (qr > mid) update(2 * node + 1, mid + 1, r, ql, qr, v);
        pushUp(node);
    }

public:
    int sumCounts(vector<int>& nums) {
        int n = nums.size();
        tree.assign(4 * n, Node());
        vector<int> last(100001, -1);
        long long total_ans = 0;

        for (int j = 0; j < n; ++j) {
            int prev = last[nums[j]];
            update(1, 0, n - 1, prev + 1, j, 1);
            total_ans = (total_ans + tree[1].sum2) % MOD;
            last[nums[j]] = j;
        }

        return (total_ans + MOD) % MOD;
    }
};
```

## Edge cases
- Array with all identical elements (e.g., [2, 2]): the range to update shrinks after the first occurrence.
- Array with all distinct elements: update range is always [0, j].
- Single element array (n = 1): trivial 1^2 = 1.
- Max constraints (n = 10^5) requiring efficient O(n log n) time and 64-bit integer arithmetic to prevent overflow.

## Dry run (example 1)
nums = [1, 2, 1]
j = 0, val = 1: prev = -1. Range [0, 0] += 1. tree[1].sum2 = 1^2 = 1. total_ans = 1. last[1] = 0.
j = 1, val = 2: prev = -1. Range [0, 1] += 1. f is now [2, 1]. tree[1].sum2 = 2^2 + 1^2 = 5. total_ans = 1 + 5 = 6. last[2] = 1.
j = 2, val = 1: prev = 0. Range [1, 2] += 1. f is now [2, 2, 1]. tree[1].sum2 = 2^2 + 2^2 + 1^2 = 9. total_ans = 6 + 9 = 15. last[1] = 2.
Result: 15.
