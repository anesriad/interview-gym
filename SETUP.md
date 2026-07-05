# One-time setup

Do these once, then you never touch them again.

## 1. VSCode extensions
Install these two (Extensions panel, `Cmd+Shift+X`):
- **Python** (ms-python.python)
- **Jupyter** (ms-toolsai.jupyter)

## 2. Python environment (already created)
A virtual env lives in `.venv/` with all dependencies installed. To use it:
- **In the terminal:** `source .venv/bin/activate`
- **In notebooks:** when you open a `.ipynb`, pick the kernel in the top-right and choose the
  interpreter at `.venv/bin/python`.

To reinstall/update deps later: `.venv/bin/python -m pip install -r requirements.txt`

## 3. Build the practice database (already built)
```
.venv/bin/python db/build_db.py     # rebuild/reset the SQL practice DB
.venv/bin/python data/make_data.py  # rebuild/reset the ML csv
```
Both were run during setup; re-run anytime to reset the data.

## 4. Recommended VSCode settings
Add to your settings (`Cmd+,` → open JSON) to reduce the notebook save/refresh friction:
```json
"files.autoSave": "afterDelay",
"files.autoSaveDelay": 1000
```

## Daily use
- Dock the Claude chat panel to one side; keep your notebook tab in the main area.
- In the chat: `/practice sql window-functions` (or just `/practice` to let the mentor pick).
- Solve solo in the notebook (Shift+Enter). This costs no tokens.
- When you want feedback: `/review`. Feedback lands in the chat + `feedback.md`.
- The mentor edits your notebook **only if you explicitly ask**.

## How SQL runs in a notebook
Top cell of any SQL notebook:
```python
%load_ext sql
%sql duckdb:///db/practice.db
```
Then query in a cell:
```python
%%sql
SELECT * FROM orders LIMIT 5;
```
Results render as an inline table.
