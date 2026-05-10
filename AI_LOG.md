# AI Assistance Log

This document discloses every instance where Generative AI was used
during the development of this project, as required by the course
AI policy.

---

## Tool Used Throughout

**Tool:** Claude (Anthropic), accessed via the web interface at claude.ai.

**Approach:** AI was used as a pair-programming assistant. I worked
through the project incrementally - asking for guidance one step at a
time, writing or modifying the code in my own editor, running and
debugging it myself, and only moving to the next step after each
piece was working and committed. I did not paste entire AI outputs
into my project without review.

---

## Entry 1 - Project Scoping and Schema Design

**Prompt summary:**
> Help me design a Flask-based finance tracker for CS665 Project 3:
> personal budgeting, single user, no preference on database.

**AI Output:**
- Recommended SQLite (file-based, zero-setup, sufficient for the rubric)
- Suggested a five-table schema: accounts, categories, transactions,
  tags, transaction_tags (junction).
- Mapped each rubric requirement to a specific feature.

**My modifications / verifications:**
- After realizing the rubric required me to use my previously
  designed database from Project 4, I had Claude help reconstruct
  the schema from my earlier work (users, accounts, categories,
  expenses, budgets) and then adapt it to Project 3's needs.
- I made the design decision to keep `users` as a seeded single-row
  table rather than drop it, so the multi-user structure of the
  original schema is preserved.

---

## Entry 2 - Project Scaffolding (Step-by-step)

**Prompt summary:**
> Walk me through setting up the Flask project from scratch -
> environment, dependencies, first hello-world, then incrementally
> add models, templates, forms.

**AI Output:**
- A step-by-step build sequence: venv setup, hello world, then
  SQLAlchemy models, then Jinja templates, then WTForms.
- Each step kept to one concept so it could be committed independently.

**My modifications / verifications:**
- I wrote each file by hand in VS Code, then tested in the browser
  before moving on.
- Hit several issues that I debugged with Claude's help:
  - Forgot to save `app.py` before running it - learned to check the
    VS Code tab dot indicator.
  - SQLAlchemy `ImportError` because I hadn't actually added the
    `Category` and `Transaction` classes to `app.py` yet.
  - REPL indentation errors from pasting multi-line blocks - switched
    to running test scripts instead, which is a cleaner workflow.
---

## Entry 3 - Schema Drift on Model Changes

**Prompt summary:**
> I added a `user_id` column to accounts but I'm getting "no such
> column: accounts.user_id" at runtime.

**AI Output:**
- Explained that `db.create_all()` only creates tables that don't
  exist - it never alters existing ones.
- Recommended deleting the SQLite file and letting SQLAlchemy
  recreate it fresh, since this is a class project with no real
  data to preserve.
- Mentioned that production systems use migration tools like Alembic
  for this problem.

**My modifications / verifications:**
- Deleted `finance.db` and `instance/finance.db`, restarted the app,
  and confirmed the new schema was created correctly.
- Noted that this is something I would handle very differently in a
  production environment - blowing away the database is not an
  option once it has user data.

---

## Entry 4 - SQL Transaction Logic for Balance Updates

**Prompt summary:**
> Help me implement the atomic balance update logic for transactions:
> creating, editing, and deleting must all keep the account balance
> in sync inside a single SQL transaction.

**AI Output:**
- Provided the create/edit/delete routes wrapping all DB mutations
  in `try/except` blocks with `db.session.commit()` on success and
  `db.session.rollback()` on failure.
- Explained that SQLAlchemy's session is transactional by default -
  every `add` and attribute change is staged until `commit()` flushes
  them atomically.
- Suggested a `balance_delta(amount, category_type)` helper to keep
  the same calculation from being duplicated across three routes.

**My modifications / verifications:**
- I verified the rollback path by temporarily adding
  `raise Exception("Simulated mid-transaction failure")` just before
  `db.session.commit()` in the create route, then confirmed that
  the account balance did NOT change and no transaction row was
  inserted. The red flash message appeared as expected.
- I tested the edit logic with four scenarios: changing amount only,
  changing account, changing the category type (income ↔ expense),
  and deleting. Verified the resulting balances by hand each time.

---

## Entry 5 - Dashboard Aggregate Queries

**Prompt summary:**
> Help me build/design the summary dashboard with SUM, COUNT, AVG queries
> demonstrating the aggregate functions requirement.

**AI Output:**
- Five aggregate queries using `func.sum`, `func.count`, `func.avg`,
  and a `case()` expression to compute monthly income and expense
  in a single SELECT.
- Recommended `coalesce(value, 0)` to avoid `None` propagation when
  the tables are empty.

**My modifications / verifications:**
- Tested the dashboard against known data: I created six known
  transactions and verified by hand that the totals on the page
  matched what I calculated independently.

---

## Entry 6 - Funny Financial Advisor Feature

**Prompt summary:**
> Add a feature that shows a context-aware financial roast at the
> top of the dashboard on each load.

**AI Output:**
- A `get_financial_quip()` function that queries the same aggregates
  as the dashboard, picks an applicable template based on the user's
  data, and falls back to generic jokes when no contextual templates
  fit.
- Styled banner template addition.

**My modifications / verifications:**
- No changes were made since I already liked it to begin with.

---