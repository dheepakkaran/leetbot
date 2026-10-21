# 3863. Minimum Operations to Sort a String

**Difficulty:** Medium · **Topics:** String · **Language:** Python · **Day:** 11 · **Date:** 2026-10-21

🔗 [Open on LeetCode](https://leetcode.com/problems/minimum-operations-to-sort-a-string/)

> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.

## Hint
Analyze the conditions under which the string can be sorted in 0, 1, 2, or 3 operations based on the characters at the boundary positions.

## Optimal: Greedy / Case Analysis
Any operation can only sort a proper substring, leaving at least one boundary character untouched if length is $n-1$. If the string is already sorted, 0 operations are needed. For $n = 2$, proper substrings have length 1 and sorting them changes nothing, so it's impossible (-1). For $n \ge 3$, if the first character is already the global minimum or the last is the global maximum, 1 operation on the remaining $n-1$ characters sorts the string. If the first character is the unique maximum AND the last character is the unique minimum, no single operation can place either in its correct boundary, requiring 3 operations. In all other cases, 2 operations suffice.

1. Check if $s$ is already sorted; if so, return 0.
2. If $n = 2$, return -1 since sorting length-1 substrings has no effect.
3. Find the minimum and maximum characters of $s$.
4. If $s[0] == \min(s)$ or $s[-1] == \max(s)$, return 1.
5. If $s[0] == \max(s)$, $s[-1] == \min(s)$, and both appear exactly once in $s$, return 3.
6. Otherwise, return 2.

**Time:** O(n) · **Space:** O(1)

```python
class Solution:
    def minOperations(self, s: str) -> int:
        n = len(s)
        if all(s[i] <= s[i + 1] for i in range(n - 1)):
            return 0
        if n == 2:
            return -1

        min_char = min(s)
        max_char = max(s)

        if s[0] == min_char or s[-1] == max_char:
            return 1

        if s[0] == max_char and s[-1] == min_char and s.count(max_char) == 1 and s.count(min_char) == 1:
            return 3

        return 2
```

## Edge cases
- String of length 1: already sorted, returns 0.
- String of length 2: if unsorted, impossible to sort using proper substrings, returns -1.
- String where min or max elements appear multiple times at boundaries.

## Dry run (example 1)
For s = 'dog': length n = 3. Check if sorted: 'd' <= 'o' but 'o' > 'g', so not sorted. n != 2. min_char = 'd', max_char = 'o'. Since s[0] == 'd' == min_char, we can sort the suffix s[1:] ('og' -> 'go') in 1 operation to get 'dgo'. Returns 1.
