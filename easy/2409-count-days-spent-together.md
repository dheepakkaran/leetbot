# 2409. Count Days Spent Together

**Difficulty:** Easy · **Topics:** Math, String · **Language:** Python · **Day:** 14 · **Date:** 2026-10-24

🔗 [Open on LeetCode](https://leetcode.com/problems/count-days-spent-together/)

> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.

## Hint
Convert dates into the day of the year (1-365) to reduce this to finding the intersection of two 1D intervals.

## Brute force
Convert each date into a day-of-year integer (from 1 to 365), then iterate through all 365 days of the year, counting how many days fall within both Alice's and Bob's stay.

**Time:** O(1) · **Space:** O(1)

```python
class Solution:
    def countDaysTogether(self, arriveAlice: str, leaveAlice: str, arriveBob: str, leaveBob: str) -> int:
        days_in_months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        def to_day_of_year(date: str) -> int:
            m, d = map(int, date.split("-"))
            return sum(days_in_months[:m - 1]) + d
        
        a_start = to_day_of_year(arriveAlice)
        a_end = to_day_of_year(leaveAlice)
        b_start = to_day_of_year(arriveBob)
        b_end = to_day_of_year(leaveBob)
        
        count = 0
        for day in range(1, 366):
            if a_start <= day <= a_end and b_start <= day <= b_end:
                count += 1
        return count
```

## Optimal: Interval Intersection
Convert each date into the sequential day of the year (1 to 365). The overlap of two intervals [start1, end1] and [start2, end2] is [max(start1, start2), min(end1, end2)]. If the overlap start is at or before the overlap end, the count is overlap_end - overlap_start + 1; otherwise, 0.

1. Define a helper function to convert 'MM-DD' into the nth day of the year using month day counts.
2. Convert arriveAlice, leaveAlice, arriveBob, and leaveBob to day-of-year integers.
3. Calculate overlap_start = max(arriveAlice_day, arriveBob_day) and overlap_end = min(leaveAlice_day, leaveBob_day).
4. Return max(0, overlap_end - overlap_start + 1).

**Time:** O(1) · **Space:** O(1)

```python
class Solution:
    def countDaysTogether(self, arriveAlice: str, leaveAlice: str, arriveBob: str, leaveBob: str) -> int:
        days_in_months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        def to_day_of_year(date: str) -> int:
            m, d = map(int, date.split("-"))
            return sum(days_in_months[:m - 1]) + d
        
        start = max(to_day_of_year(arriveAlice), to_day_of_year(arriveBob))
        end = min(to_day_of_year(leaveAlice), to_day_of_year(leaveBob))
        
        return max(0, end - start + 1)
```

## Edge cases
- No overlap between stays (leaveAlice < arriveBob or leaveBob < arriveAlice)
- One person's stay is completely inside the other person's stay
- Same arrival and departure date for a person (1-day stay)
- Overlap is exactly 1 day (e.g., leaveAlice == arriveBob)

## Dry run (example 1)
arriveAlice = '08-15', leaveAlice = '08-18', arriveBob = '08-16', leaveBob = '08-19'
- Days before August (Jan-Jul) sum: 31 + 28 + 31 + 30 + 31 + 30 + 31 = 212
- to_day_of_year('08-15') = 212 + 15 = 227
- to_day_of_year('08-18') = 212 + 18 = 230
- to_day_of_year('08-16') = 212 + 16 = 228
- to_day_of_year('08-19') = 212 + 19 = 231
- start = max(227, 228) = 228
- end = min(230, 231) = 230
- result = max(0, 230 - 228 + 1) = 3
