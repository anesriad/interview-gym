// Static cheat-sheet cards for the "Rules" popup. No LLM — written once, reused forever.
export const RULES = [
  {
    id: "sql-order", area: "SQL", label: "SQL order of execution",
    body: `Written order ≠ execution order:

\`\`\`
FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT
\`\`\`

Consequences:
- **WHERE can't see SELECT aliases** (they don't exist yet) — but ORDER BY can.
- **WHERE filters rows before grouping; HAVING filters groups after.**
- Window functions run at SELECT time → you can't filter on them directly; wrap in a subquery/CTE.`
  },
  {
    id: "sql-joins", area: "SQL", label: "JOIN types",
    body: `\`\`\`sql
A INNER JOIN B ON …   -- only matching rows
A LEFT  JOIN B ON …   -- all of A; B columns NULL if no match
A FULL  JOIN B ON …   -- everything from both sides
A CROSS JOIN B        -- every combination
\`\`\`

- **Anti-join** (in A but not B): \`LEFT JOIN … WHERE b.key IS NULL\` or \`NOT EXISTS\`.
- **Fan-out trap**: joining one-to-many then aggregating double-counts. Aggregate each table in its own CTE first, then join.`
  },
  {
    id: "sql-where-having", area: "SQL", label: "WHERE vs HAVING",
    body: `- **WHERE** — filters **rows**, before GROUP BY. Cheaper; use whenever possible.
- **HAVING** — filters **groups**, after aggregation; can use aggregates.

\`\`\`sql
SELECT city, COUNT(*) AS n
FROM trips
WHERE status = 'completed'   -- row condition
GROUP BY city
HAVING COUNT(*) >= 100;      -- group condition
\`\`\`

Rule of thumb: if the condition doesn't contain an aggregate, it belongs in WHERE.`
  },
  {
    id: "sql-window", area: "SQL", label: "Window functions",
    body: `\`\`\`sql
ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY ts DESC)  -- 1,2,3… no ties
RANK()       OVER (…)   -- 1,1,3 (gaps) · DENSE_RANK: 1,1,2
LAG(x)  OVER (ORDER BY month)          -- previous row's value
SUM(x)  OVER (PARTITION BY g)          -- group total on every row
SUM(x)  OVER (ORDER BY d)              -- running total
\`\`\`

**Top-1 per group**: aggregate → ROW_NUMBER in a subquery → \`WHERE rn = 1\`.
**% of total**: \`100.0 * SUM(x) / SUM(SUM(x)) OVER ()\` next to a GROUP BY.`
  },
  {
    id: "sql-cte", area: "SQL", label: "CTEs (WITH)",
    body: `\`\`\`sql
WITH pay AS (
    SELECT user_id, SUM(amount) AS total FROM payments GROUP BY user_id
), top AS (
    SELECT * FROM pay ORDER BY total DESC LIMIT 10
)
SELECT * FROM top JOIN users USING (user_id);
\`\`\`

- Comma-separate multiple CTEs; later ones can reference earlier ones.
- Use CTEs to name steps (readability in interviews) and to filter on window results.`
  },
  {
    id: "sql-null", area: "SQL", label: "NULL traps",
    body: `- \`x = NULL\` is never true — use \`IS NULL\` / \`IS NOT NULL\`.
- **\`NOT IN (subquery)\` returns nothing if the subquery contains a NULL.** Use \`NOT EXISTS\`.
- \`COUNT(*)\` counts rows; \`COUNT(col)\` skips NULLs — that difference is often the answer.
- Aggregates ignore NULLs; \`AVG\` divides by non-null count only.
- \`COALESCE(x, 0)\` for defaults after LEFT JOINs.`
  },
  {
    id: "sql-dates", area: "SQL", label: "Dates (DuckDB / Postgres)",
    body: `\`\`\`sql
DATE_TRUNC('month', ts)::DATE          -- month bucket
ts::DATE                               -- timestamp → date
d + INTERVAL 30 DAY                    -- date arithmetic
DATE_DIFF('day', d1, d2)               -- duckdb (postgres: d2 - d1)
EXTRACT(dow FROM d)                    -- day of week
\`\`\`

Cohort pattern: bucket by \`DATE_TRUNC('month', signup_date)\`, compare event dates with \`BETWEEN signup AND signup + INTERVAL 30 DAY\`.`
  },
  {
    id: "py-function", area: "Python", label: "Functions",
    body: `\`\`\`python
def f(a, b=2, *args, **kwargs):
    return a + b        # no return → returns None
\`\`\`

- **Mutable default trap**: \`def f(x, acc=[])\` shares one list across calls. Use \`acc=None\` then \`acc = acc or []\`.
- Lambdas for keys: \`sorted(items, key=lambda t: (-t[1], t[0]))\`.
- Inner helper functions (for DFS etc.) can read outer variables; assignment needs \`nonlocal\`.`
  },
  {
    id: "py-loops", area: "Python", label: "Loops & comprehensions",
    body: `\`\`\`python
for i, x in enumerate(nums):      # index + value
for a, b in zip(xs, ys):          # parallel iterate
for i in range(len(s) - 1, -1, -1):  # backwards

squares = [x*x for x in nums if x > 0]        # list comp
lookup  = {u.id: u for u in users}            # dict comp
seen    = {x for x in nums}                   # set comp
\`\`\`

\`while\` + two pointers: move \`left\`/\`right\` based on a condition; guarantee progress each iteration or you'll loop forever.`
  },
  {
    id: "py-collections", area: "Python", label: "Counter, defaultdict, deque, heapq",
    body: `\`\`\`python
from collections import Counter, defaultdict, deque
Counter(nums).most_common(2)      # [(val, count), …]
d = defaultdict(list); d[k].append(x)   # no KeyError
q = deque([start]); q.popleft()   # BFS queue, O(1) both ends

import heapq                       # min-heap
heapq.heappush(h, (dist, node)); heapq.heappop(h)
# max-heap: push negatives
\`\`\`

dict/set membership is O(1) — the answer to most "make it faster" follow-ups.`
  },
  {
    id: "py-sorting", area: "Python", label: "Sorting",
    body: `\`\`\`python
sorted(nums)                      # new list
nums.sort(reverse=True)           # in place
sorted(words, key=len)
sorted(items, key=lambda t: (-t[1], t[0]))  # freq desc, value asc
\`\`\`

- Tuple keys = multi-level sort; negate numbers for descending per-field.
- Python's sort is **stable**: equal keys keep their original order.
- Sorting costs O(n log n) — say so, and mention if a heap/bucket beats it.`
  },
  {
    id: "py-strings", area: "Python", label: "Strings & slicing",
    body: `\`\`\`python
s[2:5], s[:3], s[::-1]            # slice, prefix, reverse
s.split(','), ' '.join(parts)
s.strip(), s.lower(), s.startswith('ab')
s.replace('a', 'b')               # strings are immutable — this returns a new one
\`\`\`

Building a string in a loop? Collect parts in a list and \`''.join(parts)\` — repeated \`+=\` is O(n²).`
  },
  {
    id: "pd-groupby", area: "Python", label: "pandas groupby & cleaning",
    body: `\`\`\`python
df.groupby('plan')['churned'].mean()
df.groupby('city').agg(n=('id', 'count'), rev=('fare', 'sum'))
df['col'].fillna(df['col'].median())
df.loc[df.contract == 'monthly', 'churned'].mean()
pd.get_dummies(df[['plan', 'contract']])
df['col'].value_counts(normalize=True)
\`\`\`

Mean of a 0/1 column = rate. \`.isna().sum()\` first, always.`
  },
  {
    id: "ml-confusion", area: "ML", label: "Confusion matrix & P/R/F1",
    body: `|            | Pred + | Pred − |
|------------|--------|--------|
| **Actual +** | TP     | FN     |
| **Actual −** | FP     | TN     |

- **Precision** = TP / (TP+FP) — "when I flag, am I right?" Optimize when FPs are costly (spam).
- **Recall** = TP / (TP+FN) — "did I catch them all?" Optimize when FNs are costly (cancer, fraud).
- **F1** = harmonic mean — single number when classes are imbalanced.
- Accuracy lies under imbalance: 95% negatives → predicting "all negative" scores 95%.`
  },
  {
    id: "ml-metrics", area: "ML", label: "AUC, accuracy & thresholds",
    body: `- **ROC AUC** = P(random positive scores higher than random negative). Threshold-free; 0.5 = coin flip. Use \`predict_proba\`, not \`predict\`.
- Accuracy depends on the 0.5 threshold and the class balance — always compare to the majority-class baseline.
- Heavy imbalance? Prefer **precision-recall AUC** over ROC.
- Regression: MAE (robust, interpretable) vs RMSE (punishes big misses).`
  },
  {
    id: "ml-recipe", area: "ML", label: "sklearn recipe & leakage",
    body: `\`\`\`python
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25,
                                      random_state=42, stratify=y)
model = LogisticRegression(max_iter=1000).fit(Xtr, ytr)
auc = roc_auc_score(yte, model.predict_proba(Xte)[:, 1])
\`\`\`

**Leakage rules**: fit imputers/scalers/encoders on **train only**, then transform test. Never let IDs, the target, or post-outcome features into X. \`stratify=y\` keeps class balance in both splits.`
  },
];
