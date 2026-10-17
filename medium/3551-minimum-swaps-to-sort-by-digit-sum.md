# 3551. Minimum Swaps to Sort by Digit Sum

**Difficulty:** Medium · **Topics:** Array, Hash Table, Sorting · **Language:** C++ · **Day:** 7 · **Date:** 2026-10-17

🔗 [Open on LeetCode](https://leetcode.com/problems/minimum-swaps-to-sort-by-digit-sum/)

> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.

## Hint
Determine the target sorted order, then find the number of disjoint cycles in the permutation mapping.

## Brute force
Model the array states as a graph where each edge represents a swap of two elements, and use Breadth-First Search (BFS) to find the shortest path from the initial array to the target sorted array.

**Time:** O(N! * N^2) · **Space:** O(N! * N)

```cpp
class Solution {
public:
    int minSwaps(vector<int>& nums) {
        // Breadth-First Search exploring all possible permutations
        int n = nums.size();
        auto getDigitSum = [](int x) {
            int s = 0;
            while (x > 0) {
                s += x % 10;
                x /= 10;
            }
            return s;
        };
        
        vector<int> target = nums;
        sort(target.begin(), target.end(), [&](int a, int b) {
            int sa = getDigitSum(a), sb = getDigitSum(b);
            if (sa != sb) return sa < sb;
            return a < b;
        });
        
        if (nums == target) return 0;
        
        queue<pair<vector<int>, int>> q;
        set<vector<int>> visited;
        q.push({nums, 0});
        visited.insert(nums);
        
        while (!q.empty()) {
            auto [curr, steps] = q.front();
            q.pop();
            
            if (curr == target) return steps;
            
            for (int i = 0; i < n; ++i) {
                for (int j = i + 1; j < n; ++j) {
                    swap(curr[i], curr[j]);
                    if (!visited.count(curr)) {
                        visited.insert(curr);
                        q.push({curr, steps + 1});
                    }
                    swap(curr[i], curr[j]);
                }
            }
        }
        return -1;
    }
};
```

## Optimal: Cycle Decomposition
Compute the target sorted order using a custom comparator that compares digit sums (and values for ties). The minimum number of swaps to rearrange an array into target order is N minus the number of disjoint cycles in the permutation mapping each element from its current position to its target position.

1. Define a helper function to compute the digit sum of an integer.
2. Create an array of pairs/indices and sort it based on digit sum, breaking ties with the integer value.
3. Construct a visited array of size N to track which elements have been counted in permutation cycles.
4. Iterate through the array; for each unvisited index, trace its cycle by following the target index until returning to the start.
5. For each cycle of length L, L - 1 swaps are needed. Summing this over all cycles gives N - (number of cycles).

**Time:** O(N log N) · **Space:** O(N)

```cpp
class Solution {
public:
    int minSwaps(vector<int>& nums) {
        int n = nums.size();
        auto getDigitSum = [](int x) {
            int sum = 0;
            while (x > 0) {
                sum += x % 10;
                x /= 10;
            }
            return sum;
        };

        // Store {digit_sum, value, original_index}
        vector<pair<pair<int, int>, int>> sortedNums(n);
        for (int i = 0; i < n; ++i) {
            sortedNums[i] = {{getDigitSum(nums[i]), nums[i]}, i};
        }

        sort(sortedNums.begin(), sortedNums.end());

        vector<bool> visited(n, false);
        int swaps = 0;

        for (int i = 0; i < n; ++i) {
            if (visited[i] || sortedNums[i].second == i) {
                continue;
            }

            int cycleSize = 0;
            int curr = i;
            while (!visited[curr]) {
                visited[curr] = true;
                curr = sortedNums[curr].second;
                cycleSize++;
            }

            if (cycleSize > 0) {
                swaps += (cycleSize - 1);
            }
        }

        return swaps;
    }
};
```

## Edge cases
- Array is already sorted (0 swaps).
- Array of size 1 (0 swaps).
- All elements have the same digit sum, falling back to numerical sorting.
- Numbers with large values up to 10^9 (digit sum handled properly without overflow).

## Dry run (example 1)
For nums = [37, 100]:
1. Digit sums: 37 -> 10, 100 -> 1.
2. sortedNums becomes: [{{1, 100}, 1}, {{10, 37}, 0}].
3. Target sorted order places original index 1 at index 0, and original index 0 at index 1.
4. Cycle starting at i = 0: visit 0, next is sortedNums[0].second = 1. From 1, next is sortedNums[1].second = 0 (already visited). Cycle length is 2.
5. Swaps required: 2 - 1 = 1.
