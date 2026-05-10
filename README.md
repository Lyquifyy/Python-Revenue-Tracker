# Finance Tracker

A single-user personal finance application that tracks accounts,
categories, transactions, tags, and monthly budgets. Built for
CS665 Project 3.

## Project Description

The application allows a user to manage multiple financial accounts
(checking, savings, credit cards, cash), categorize transactions as
income or expense, tag transactions for cross-cutting labels like
"tax-deductible" or "recurring," and set monthly budget limits per
category. The dashboard shows aggregate insights including total
balance, monthly income vs. expenses, top spending categories, and
average transaction size.

**Audience:** A single user managing their own personal finances.
No authentication is included by design - the rubric calls for a
focused scope, and adding auth would dilute the database work that
this project is graded on.

## Tech Stack

- **Python 3.10+**
- **Flask** + **Flask-SQLAlchemy** + **Flask-WTF**
- **SQLite** (file-based, zero-setup)
- **Bootstrap-free Jinja2 templates** with inline styles
- **WTForms** for server-side validation

## Schema

See [`NORMALIZATION.md`](NORMALIZATION.md) for the full normalization
analysis. The final schema (in 3NF) consists of:

- `users` - registered users (single seeded user in this app)
- `accounts` - financial accounts owned by a user
- `categories` - income/expense classifications
- `transactions` - individual financial transactions (the main entity)
- `tags` - reusable labels
- `transaction_tags` - many-to-many junction between transactions and tags
- `budgets` - per-category monthly spending limits

## Installation

1. **Clone the repository:**
```bash
   git clone <your-repo-url>
   cd <repo-folder>
```

2. **Create and activate a virtual environment:**
```bash
   python -m venv venv

   # Linux / macOS
   source venv/bin/activate

   # Windows PowerShell
   venv\Scripts\activate
```

3. **Install dependencies:**
```bash
   pip install -r requirements.txt
```

## Database Setup

The application uses SQLite and automatically creates the database
file (`finance.db`) and seeds a default user on first launch. No
manual setup is required for normal use.

A `.sql` schema file is included for the grading rubric requirement:

```bash
sqlite3 finance.db < schema.sql
```

This produces the same tables that the application would auto-create
via SQLAlchemy.

## Running the App

Start the development server:

```bash
python app.py
```

Then open <http://127.0.0.1:5000> in your browser.

## Main Features

| Page | URL | What it does |
|---|---|---|
| Dashboard | `/` | Summary cards (SUM/COUNT/AVG), top categories, recent activity |
| Accounts list | `/accounts` | View, edit, delete all accounts |
| New account | `/accounts/new` | Create a new account |
| Transactions list | `/transactions` | View, edit, delete all transactions |
| New transaction | `/transactions/new` | Record a transaction (with atomic balance update) |

### Workflow

1. Create one or more **accounts** (e.g., "Checking", "Visa").
2. Create **categories** (e.g., "Groceries" expense, "Salary" income).
3. Record **transactions** - the account balance updates *atomically*
   with the new transaction inside a SQL transaction.
4. View the **dashboard** for aggregate summaries.

## SQL Transaction Logic

The rubric's "transaction logic" requirement is implemented in three
places, all inside `try/except` blocks with explicit rollback:

- **Creating a transaction** inserts a row AND updates the account
  balance atomically.
- **Editing a transaction** reverses the old balance impact AND
  applies the new one AND updates the row - three operations in a
  single SQL transaction.
- **Deleting a transaction** reverses the balance impact AND deletes
  the row atomically.

In every case, if any step fails, all changes are rolled back so
the database is never left in an inconsistent state.

## Documentation

- [`NORMALIZATION.md`](NORMALIZATION.md) - 3NF analysis and decomposition
- [`AI_LOG.md`](AI_LOG.md) - Generative AI usage disclosure
- [`schema.sql`](schema.sql) - Final SQL schema