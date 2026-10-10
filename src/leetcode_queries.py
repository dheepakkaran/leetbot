"""LeetCode GraphQL queries, verified live against https://leetcode.com/graphql.

The API is unofficial. Every query here was run by `scripts/smoke_leetcode.py`
before being wired into the client. Changes from the spec's starting points
are listed in DECISIONS.md.
"""

GRAPHQL_URL = "https://leetcode.com/graphql"
REST_PROBLEMS_URL = "https://leetcode.com/api/problems/algorithms/"

# Only the "algorithms" category: database/shell/pandas/JS/concurrency problems
# have no C++/Python/Java snippets, so they can never be picked.
PROBLEM_CATEGORY = "algorithms"

DAILY_PROBLEM = """
query dailyProblem {
  activeDailyCodingChallengeQuestion {
    date
    link
    question {
      questionFrontendId
      title
      titleSlug
      difficulty
      isPaidOnly
      topicTags { name slug }
    }
  }
}
"""

QUESTION_DETAIL = """
query questionDetail($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionFrontendId
    title
    titleSlug
    difficulty
    isPaidOnly
    content
    exampleTestcases
    codeSnippets { langSlug code }
    topicTags { name slug }
  }
}
"""

# Spec field `paidOnly` does not exist on QuestionNode; the live API uses `isPaidOnly`.
# acRate is a percentage (0-100). limit: -1 returns every question in one response.
PROBLEM_LIST = """
query problemList($categorySlug: String!) {
  problemsetQuestionList: questionList(categorySlug: $categorySlug, limit: -1, skip: 0, filters: {}) {
    total: totalNum
    questions: data {
      questionFrontendId
      title
      titleSlug
      difficulty
      acRate
      isPaidOnly
      topicTags { slug }
    }
  }
}
"""

# Fallback 1. `filters.filterCombineType` is required; pages are capped at 100.
# Here difficulty is upper-case (EASY) and acRate is a fraction (0-1).
PROBLEM_LIST_V2 = """
query problemListV2($categorySlug: String!, $skip: Int!, $limit: Int!) {
  problemsetQuestionListV2(categorySlug: $categorySlug, limit: $limit, skip: $skip, filters: {filterCombineType: ALL}) {
    totalLength
    hasMore
    questions {
      questionFrontendId
      title
      titleSlug
      difficulty
      acRate
      paidOnly
      topicTags { slug }
    }
  }
}
"""

USER_STATS = """
query userStats($u: String!) {
  allQuestionsCount { difficulty count }
  matchedUser(username: $u) {
    profile { ranking }
    submitStatsGlobal { acSubmissionNum { difficulty count } }
    userCalendar { streak totalActiveDays submissionCalendar }
  }
}
"""

# Used when the current streak reaches Jan 1 and the previous year is needed.
USER_CALENDAR_YEAR = """
query userCalendarYear($u: String!, $year: Int) {
  matchedUser(username: $u) {
    userCalendar(year: $year) { streak totalActiveDays submissionCalendar }
  }
}
"""

# `id` and `timestamp` come back as strings.
RECENT_AC = """
query recentAc($u: String!, $limit: Int!) {
  recentAcSubmissionList(username: $u, limit: $limit) { id title titleSlug timestamp }
}
"""

# Exposes `lang` (e.g. "python3"), so sync records the language actually used.
RECENT_SUBMISSIONS = """
query recentSubmissions($u: String!, $limit: Int!) {
  recentSubmissionList(username: $u, limit: $limit) { titleSlug timestamp statusDisplay lang }
}
"""
