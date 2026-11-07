# 1882. Process Tasks Using Servers

**Difficulty:** Medium · **Topics:** Array, Heap (Priority Queue) · **Language:** Java · **Day:** 28 · **Date:** 2026-11-07

🔗 [Open on LeetCode](https://leetcode.com/problems/process-tasks-using-servers/)

> AI-generated with `gemini-3.6-flash`. Unverified. Check before trusting.

## Hint
Maintain available and occupied servers using two priority queues, advancing current time directly to when a server becomes free if none are available.

## Brute force
Simulate time second-by-second. At each second, check which servers become available and process the task queue by linear scanning all $n$ servers to find the best available server.

**Time:** O(max_time \cdot n) · **Space:** O(n)

```java
class Solution {
    public int[] assignTasks(int[] servers, int[] tasks) {
        int n = servers.length;
        int m = tasks.length;
        int[] ans = new int[m];
        long[] freeAt = new long[n];
        int taskIdx = 0;
        long time = 0;
        
        while (taskIdx < m) {
            time = Math.max(time, taskIdx);
            int bestServer = -1;
            for (int i = 0; i < n; i++) {
                if (freeAt[i] <= time) {
                    if (bestServer == -1 || servers[i] < servers[bestServer] || 
                       (servers[i] == servers[bestServer] && i < bestServer)) {
                        bestServer = i;
                    }
                }
            }
            if (bestServer == -1) {
                long nextFree = Long.MAX_VALUE;
                for (int i = 0; i < n; i++) nextFree = Math.min(nextFree, freeAt[i]);
                time = nextFree;
            } else {
                ans[taskIdx] = bestServer;
                freeAt[bestServer] = time + tasks[taskIdx];
                taskIdx++;
            }
        }
        return ans;
    }
}
```

## Optimal: Heap (Priority Queue)
Use two min-heaps: `freeServers` ordered by `(weight, index)` for available servers, and `busyServers` ordered by `(freeTime, weight, index)` for occupied servers.

For each task $j$ at time $j$, we:
1. Advance `currentTime` to $\max(\text{currentTime}, j)$.
2. If `freeServers` is empty, advance `currentTime` to the earliest completion time in `busyServers`.
3. Release all servers from `busyServers` whose `freeTime` $\le \text{currentTime}$ into `freeServers`.
4. Pop the highest priority server from `freeServers`, assign task $j$, and push it to `busyServers` with updated `freeTime = currentTime + tasks[j]`.

1. Initialize `freeServers` heap with all server indices sorted by weight then index.
2. Initialize `busyServers` heap storing `[freeTime, serverIndex]` sorted by freeTime, then weight, then index.
3. Iterate `j` from 0 to `m - 1`.
4. Set `currentTime = Math.max(currentTime, j)`.
5. If `freeServers` is empty, fast-forward `currentTime = busyServers.peek()[0]`.
6. Move all servers with `freeTime <= currentTime` from `busyServers` to `freeServers`.
7. Pop the top server from `freeServers`, record its index in `ans[j]`, and add `[currentTime + tasks[j], serverIndex]` to `busyServers`.

**Time:** O((n + m) \log n) · **Space:** O(n)

```java
import java.util.PriorityQueue;

class Solution {
    public int[] assignTasks(int[] servers, int[] tasks) {
        int n = servers.length;
        int m = tasks.length;
        int[] ans = new int[m];
        
        // freeServers sorted by (weight, index)
        PriorityQueue<Integer> freeServers = new PriorityQueue<>((a, b) -> {
            if (servers[a] != servers[b]) {
                return Integer.compare(servers[a], servers[b]);
            }
            return Integer.compare(a, b);
        });
        
        for (int i = 0; i < n; i++) {
            freeServers.offer(i);
        }
        
        // busyServers sorted by (freeTime, weight, index)
        // element: long[]{freeTime, serverIndex}
        PriorityQueue<long[]> busyServers = new PriorityQueue<>((a, b) -> {
            if (a[0] != b[0]) {
                return Long.compare(a[0], b[0]);
            }
            int weightA = servers[(int) a[1]];
            int weightB = servers[(int) b[1]];
            if (weightA != weightB) {
                return Integer.compare(weightA, weightB);
            }
            return Long.compare(a[1], b[1]);
        });
        
        long currentTime = 0;
        for (int j = 0; j < m; j++) {
            currentTime = Math.max(currentTime, j);
            
            if (freeServers.isEmpty()) {
                currentTime = busyServers.peek()[0];
            }
            
            while (!busyServers.isEmpty() && busyServers.peek()[0] <= currentTime) {
                long[] freed = busyServers.poll();
                freeServers.offer((int) freed[1]);
            }
            
            int serverIdx = freeServers.poll();
            ans[j] = serverIdx;
            busyServers.offer(new long[]{currentTime + tasks[j], serverIdx});
        }
        
        return ans;
    }
}
```

## Edge cases
- More tasks than servers (m > n): tests empty `freeServers` condition and time jump.
- Multiple servers free at the exact same time: tie-breaking by weight and index.
- Time values exceeding integer bounds: tasks duration sum can exceed 32-bit int, handled using 64-bit long for currentTime and freeTime.

## Dry run (example 1)
For servers = [3, 3, 2], tasks = [1, 2, 3, 2, 1, 2]:
- Start: freeServers = [2 (w=2), 0 (w=3), 1 (w=3)], busyServers = []
- j=0 (tasks[0]=1): currentTime=0. Pick server 2. ans[0]=2. busyServers = [[1, 2]]
- j=1 (tasks[1]=2): currentTime=1. Server 2 becomes free at t=1. freeServers = [2, 0, 1]. Pick server 2. ans[1]=2. busyServers = [[3, 2]]
- j=2 (tasks[2]=3): currentTime=2. Server 2 busy until 3. freeServers = [0, 1]. Pick server 0. ans[2]=0. busyServers = [[3, 2], [5, 0]]
- j=3 (tasks[3]=2): currentTime=3. Server 2 becomes free. freeServers = [2, 1]. Pick server 2. ans[3]=2. busyServers = [[5, 0], [5, 2]]
- j=4 (tasks[4]=1): currentTime=4. freeServers = [1]. Pick server 1. ans[4]=1. busyServers = [[5, 0], [5, 2], [5, 1]]
- j=5 (tasks[5]=2): currentTime=5. All servers free at t=5. freeServers = [2, 0, 1]. Pick server 2. ans[5]=2.
- Result: [2, 2, 0, 2, 1, 2].
