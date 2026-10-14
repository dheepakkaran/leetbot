# 3723. Maximize Sum of Squares of Digits

**Difficulty:** Medium · **Topics:** Math, Greedy · **Language:** C++ · **Day:** 4 · **Date:** 2026-10-14

🔗 [Open on LeetCode](https://leetcode.com/problems/maximize-sum-of-squares-of-digits/)

> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.

## Hint
Convexity of $f(x) = x^2$ means making digits as extreme as possible (as many 9s as possible).

## Optimal: Greedy
Because $f(x) = x^2$ is strictly convex, for any $a \le b$, transferring 1 from $a$ to $b$ strictly increases the sum of squares: $(a-1)^2 + (b+1)^2 > a^2 + b^2$. Thus, to maximize the sum of squares, the multiset of digits must contain as many 9s as possible, at most one non-zero remainder digit $r = \text{sum} \bmod 9$, and all remaining positions filled with 0s. To maximize the integer itself, place the largest digits first: all 9s, then $r$ (if $r > 0$), then all 0s. Since $\text{sum} \ge 1$, the first digit will always be non-zero.

1. Check if $\text{sum} > 9 \times \text{num}$. If so, it is impossible, return "".
2. Calculate $k = \lfloor \text{sum} / 9 \rfloor$ and $r = \text{sum} \bmod 9$.
3. Construct the string starting with $k$ copies of '9'.
4. If $r > 0$, append the digit character for $r$.
5. Pad the remaining $\text{num} - k - (r > 0 ? 1 : 0)$ positions with '0's.
6. Return the constructed string.

**Time:** O(num) · **Space:** O(num)

```cpp
class Solution {
public:
    string maxSumOfSquares(int num, int sum) {
        if (sum > 9LL * num) {
            return "";
        }
        
        int count9 = sum / 9;
        int rem = sum % 9;
        
        string result = "";
        result.reserve(num);
        
        result.append(count9, '9');
        if (rem > 0) {
            result.push_back('0' + rem);
        }
        
        int zeros = num - count9 - (rem > 0 ? 1 : 0);
        result.append(zeros, '0');
        
        return result;
    }
};
```

## Edge cases
- sum > 9 * num: Impossible, return empty string.
- sum is an exact multiple of 9: No remainder digit, followed directly by zeros.
- num = 1: Single digit number.
- sum = 9 * num: String consists purely of '9's.

## Dry run (example 1)
For num = 2, sum = 3: 3 <= 9 * 2 (18). count9 = 3 / 9 = 0, rem = 3 % 9 = 3. Append zero 9s. rem > 0, so append '3'. zeros = 2 - 0 - 1 = 1, append one '0'. Result is "30".
