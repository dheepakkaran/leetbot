# 1606. Find Servers That Handled Most Number of Requests

**Difficulty:** Hard · **Topics:** Array, Heap (Priority Queue), Simulation, Ordered Set · **Language:** Java · **Day:** 30 · **Date:** 2026-11-09

🔗 [Open on LeetCode](https://leetcode.com/problems/find-servers-that-handled-most-number-of-requests/)

> AI-generated with `gemini-3.6-flash`. Unverified. Check before trusting.

## Hint
Use a min-heap to free up completed servers and a balanced BST (TreeSet) to find the next available server index efficiently.

## Brute force
For each request, iterate through all $k$ servers starting from index `i % k` to find the first server whose available time is $\le \text{arrival}[i]$. Update its available time to $\text{arrival}[i] + \text{load}[i]$ and increment its count.

**Time:** O(n * k) · **Space:** O(k)

```java
class Solution {
    public List<Integer> busiestServers(int k, int[] arrival, int[] load) {
        long[] freeTime = new long[k];
        int[] count = new int[k];
        int n = arrival.length;
        
        for (int i = 0; i < n; i++) {
            int start = i % k;
            for (int j = 0; j < k; j++) {
                int server = (start + j) % k;
                if (freeTime[server] <= arrival[i]) {
                    freeTime[server] = arrival[i] + load[i];
                    count[server]++;
                    break;
                }
            }
        }
        
        int max = 0;
        for (int c : count) max = Math.max(max, c);
        List<Integer> res = new ArrayList<>();
        for (int i = 0; i < k; i++) {
            if (count[i] == max) res.add(i);
        }
        return res;
    }
}
```

## Optimal: Heap (Priority Queue) + Ordered Set (TreeSet)
We maintain two main data structures: a Min-Heap of busy servers ordered by completion time `(finish_time, server_id)`, and a `TreeSet` of available server IDs. For each request at `arrival[i]`, we first pop all completed tasks from the heap and add their server IDs back into the `TreeSet`. Then we query `ceiling(i % k)` on the `TreeSet` to find the first available server $\ge (i \% k)$. If none exists (returns null), we wrap around to `first()`. If a server is assigned, we remove it from `TreeSet`, add it to the min-heap with its finish time, and increment its processed request count.

1. Initialize `TreeSet` with all server IDs from 0 to k-1.
2. Initialize a Min-Heap storing pairs `{finish_time, server_id}` ordered by `finish_time`.
3. For each request `i`, poll elements from the Min-Heap with `finish_time <= arrival[i]` and insert their server IDs into `TreeSet`.
4. If `TreeSet` is empty, skip the request (it gets dropped).
5. Otherwise, query `ceiling(i % k)` on `TreeSet`. If null, take `first()`.
6. Remove the chosen server from `TreeSet`, push `{arrival[i] + load[i], server}` to the heap, and increment `count[server]`.
7. Find the maximum count handled by any server and return all server IDs achieving this maximum.

**Time:** O(n log k) · **Space:** O(k)

```java
import java.util.*;

class Solution {
    public List<Integer> busiestServers(int k, int[] arrival, int[] load) {
        int[] count = new int[k];
        TreeSet<Integer> available = new TreeSet<>();
        for (int i = 0; i < k; i++) {
            available.add(i);
        }
        
        // Min-heap storing int[]{finishTime, serverId}
        PriorityQueue<int[]> busy = new PriorityQueue<>((a, b) -> Integer.compare(a[0], b[0]));
        
        int n = arrival.length;
        for (int i = 0; i < n; i++) {
            int time = arrival[i];
            int end = time + load[i];
            
            // Free up servers that finished before or at current arrival time
            while (!busy.isEmpty() && busy.peek()[0] <= time) {
                available.add(busy.poll()[1]);
            }
            
            if (available.isEmpty()) {
                continue; // Drop request
            }
            
            int target = i % k;
            Integer server = available.ceiling(target);
            if (server == null) {
                server = available.first(); // Wrap around
            }
            
            available.remove(server);
            busy.offer(new int[]{end, server});
            count[server]++;
        }
        
        int max = 0;
        for (int c : count) {
            max = Math.max(max, c);
        }
        
        List<Integer> ans = new ArrayList<>();
        for (int i = 0; i < k; i++) {
            if (count[i] == max) {
                ans.add(i);
            }
        }
        return ans;
    }
}
```

## Edge cases
- k > arrival.length: More servers than requests, wrap around is never triggered and some servers remain unused.
- Multiple servers tied for busiest: All tied server IDs should be included in the output.
- All requests dropped except first batch: When load times are very high compared to arrival times.
- Wrap-around requirement: Request assigned to server 0 when target server `i % k` is busy along with all servers > `i % k`.

## Dry run (example 1)
k = 3, arrival = [1,2,3,4,5], load = [5,2,3,3,3]
Initial state: available = {0, 1, 2}, busy = [], count = [0, 0, 0]

- i = 0: time = 1, target = 0. No busy servers to free.
  ceiling(0) = 0. Assign server 0 (busy until 1+5=6). count[0]=1.
  available = {1, 2}, busy = [{6, 0}]

- i = 1: time = 2, target = 1. No busy servers to free.
  ceiling(1) = 1. Assign server 1 (busy until 2+2=4). count[1]=1.
  available = {2}, busy = [{4, 1}, {6, 0}]

- i = 2: time = 3, target = 2. No busy servers to free.
  ceiling(2) = 2. Assign server 2 (busy until 3+3=6). count[2]=1.
  available = {}, busy = [{4, 1}, {6, 0}, {6, 2}]

- i = 3: time = 4, target = 0.
  Free busy server {4, 1} since finish 4 <= time 4. available = {1}.
  target = 0. ceiling(0) = 1. Assign server 1 (busy until 4+3=7). count[1]=2.
  available = {}, busy = [{6, 0}, {6, 2}, {7, 1}]

- i = 4: time = 5, target = 1.
  Peek heap: finish 6 > time 5. No servers freed. available = {}.
  Request 4 is dropped.

Final counts: [1, 2, 1]. Max count = 2. Result = [1].
