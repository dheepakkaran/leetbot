# 2747. Count Zero Request Servers

**Difficulty:** Medium · **Topics:** Array, Hash Table, Sliding Window, Sorting · **Language:** Java · **Day:** 27 · **Date:** 2026-11-06

🔗 [Open on LeetCode](https://leetcode.com/problems/count-zero-request-servers/)

> AI-generated with `gemini-3.5-flash-lite`. Unverified. Check before trusting.

## Hint
Try sorting both the logs by time and the queries to process them efficiently using a sliding window.

## Brute force
For each query, iterate through all logs to count how many unique servers had at least one request within the window [queries[i] - x, queries[i]]. Then subtract from n.

**Time:** O(Q * L) · **Space:** O(n)

```java
class Solution {
    public int[] countServers(int n, int[][] logs, int x, int[] queries) {
        int q = queries.length;
        int[] ans = new int[q];
        for (int i = 0; i < q; i++) {
            int start = queries[i] - x;
            int end = queries[i];
            java.util.Set<Integer> active = new java.util.HashSet<>();
            for (int[] log : logs) {
                if (log[1] >= start && log[1] <= end) {
                    active.add(log[0]);
                }
            }
            ans[i] = n - active.size();
        }
        return ans;
    }
}
```

## Optimal: Sliding Window and Sorting
Sort the queries along with their original indices. Also sort the logs by their time. Use a two-pointer sliding window to maintain the frequency of server requests within the current query window [query - x, query], updating a hash map or frequency array, and compute the number of servers with zero requests.

1. Store queries along with their indices and sort them in increasing order of query time.
2. Sort the logs array based on the request time.
3. Maintain a sliding window [L, R] over logs for the current query time interval [q - x, q], adding logs to a frequency map of server IDs as R advances, and removing as L advances.
4. The number of servers with zero requests is n minus the size of the frequency map.

**Time:** O(L log L + Q log Q) · **Space:** O(n + L + Q)

```java
class Solution {
    public int[] countServers(int n, int[][] logs, int x, int[] queries) {
        int qLen = queries.length;
        int[][] sortedQueries = new int[qLen][2];
        for (int i = 0; i < qLen; i++) {
            sortedQueries[i][0] = queries[i];
            sortedQueries[i][1] = i;
        }
        java.util.Arrays.sort(sortedQueries, (a, b) -> Integer.compare(a[0], b[0]));
        java.util.Arrays.sort(logs, (a, b) -> Integer.compare(a[1], b[1]));

        int[] ans = new int[qLen];
        java.util.Map<Integer, Integer> freq = new java.util.HashMap<>();
        int L = 0, R = 0;
        int logsLen = logs.length;

        for (int i = 0; i < qLen; i++) {
            int qTime = sortedQueries[i][0];
            int origIdx = sortedQueries[i][1];
            int startTime = qTime - x;
            int endTime = qTime;

            while (R < logsLen && logs[R][1] <= endTime) {
                freq.put(logs[R][0], freq.getOrDefault(logs[R][0], 0) + 1);
                R++;
            }
            while (L < logsLen && logs[L][1] < startTime) {
                freq.put(logs[L][0], freq.get(logs[L][0]) - 1);
                if (freq.get(logs[L][0]) == 0) {
                    freq.remove(logs[L][0]);
                }
                L++;
            }
            ans[origIdx] = n - freq.size();
        }
        return ans;
    }
}
```

## Edge cases
- All logs fall outside of all query windows, meaning all servers have zero requests.
- Multiple requests for the same server within the same window.
- Queries with no matching logs in the window.

## Dry run (example 1)
n = 3, logs = [[1,3],[2,6],[1,5]], x = 5, queries = [10,11]. Sorted queries: [10 (idx 0), 11 (idx 1)]. Sorted logs: [1,3], [1,5], [2,6]. For query 10, window is [5, 10]. R includes logs [1,5] and [2,6]. Map has server 1 and 2. Zero-request servers = 3 - 2 = 1. For query 11, window is [6, 11]. L advances past [1,3] and [1,5], leaving only [2,6]. Map has server 2. Zero-request servers = 3 - 1 = 2. Output: [1, 2].
