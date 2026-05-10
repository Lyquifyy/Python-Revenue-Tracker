# Normalization Report

This document explains the normalization analysis of the Finance Tracker
schema. It walks through the original schema from CS665 Project 4, the
issues identified, the decomposition steps taken, and the final schema
the Python application uses.

---

## 1. Starting Point: The Project 4 Schema

For CS665 Project 4 I designed a personal expense tracker database in
MySQL with the following five tables:
users (
user_id PK,
username UNIQUE NOT NULL,
email UNIQUE NOT NULL,
first_name NOT NULL,
last_name NOT NULL,
date_joined DATE NOT NULL,
created_at, updated_at
)
categories (
category_id PK,
category_name NOT NULL,
description,
created_at
)
accounts (
account_id PK,
user_id FK -> users,
account_name NOT NULL,
account_type NOT NULL,
balance DECIMAL(12,2),
date_opened DATE NOT NULL,
created_at, updated_at
)
expenses (
expense_id PK,
user_id FK -> users,
category_id FK -> categories,
account_id FK -> accounts,
amount DECIMAL(10,2) NOT NULL,
description,
expense_date DATE NOT NULL,
payment_method,
created_at, updated_at
)
budgets (
budget_id PK,
user_id FK -> users,
category_id FK -> categories,
budget_limit DECIMAL(10,2) NOT NULL,
start_date DATE NOT NULL,
end_date DATE NOT NULL,
created_at, updated_at
)

This schema was mostly already in 3NF - every non-key attribute depends
only on its table's primary key, and there are no transitive
dependencies. However, when I started building Project 3 on top of
this design, I found two issues that required schema evolution.

## 2. Functional Dependencies in the Starting Schema

The functional dependencies (FDs) of the original schema:

- `users.user_id → username, email, first_name, last_name, date_joined, created_at, updated_at`
- `categories.category_id → category_name, description, created_at`
- `accounts.account_id → user_id, account_name, account_type, balance, date_opened, ...`
- `expenses.expense_id → user_id, category_id, account_id, amount, description, expense_date, payment_method, ...`
- `budgets.budget_id → user_id, category_id, budget_limit, start_date, end_date, ...`

Every non-key attribute depends on the (whole) primary key of its
table and only on that key. No partial dependencies (no composite
keys outside of junction tables), no transitive dependencies. The
starting schema satisfies 3NF.

## 3. Anomaly Identification

Even though the schema was in 3NF, I want to walk through the anomalies
that would exist in a poorly-normalized version of the same domain. If
all the columns lived in a single denormalized `transactions` table:
transactions_raw (
transaction_id, user_name, user_email, category_name, category_type,
account_name, account_type, account_balance, amount, description,
transaction_date, tag_list  -- comma-separated
)

This denormalized design would suffer from:

### Update Anomaly
Renaming a category from "Food" to "Groceries" would require updating
every transaction row containing "Food." Missing one would leave the
database with two categories that look conceptually identical but are
spelled differently. The normalized schema avoids this because the
category name lives in one place - update one row, every transaction
sees the new value immediately.

### Insertion Anomaly
A new category could not exist until at least one transaction was
recorded against it - there would be no row to put the category info
on. Same problem for accounts and budgets. The normalized schema lets
us define categories, accounts, and budgets independently of any
transaction activity.

### Deletion Anomaly
Deleting the last transaction in a category would silently destroy
the fact that the category ever existed. The normalized schema keeps
category definitions in their own table, so removing transaction
data does not lose category metadata.

### 1NF Violation (tag_list)
The comma-separated `tag_list` column does not contain atomic values
and therefore violates 1NF. Searching "all transactions tagged
'recurring'" would require a `LIKE '%recurring%'` query that also
matches `recurring-cleanup`, `non-recurring`, etc. The fix is to
extract tags into their own table with a junction table linking
transactions to tags - which is exactly what was needed for Project 3.

## 4. Schema Evolution for Project 3

Two issues drove the changes from Project 4 to Project 3:

### Issue 1: `expenses` only modeled outflow

The original `expenses` table assumed every transaction is an expense.
For Project 3's dashboard, which needs to display income vs. expense
aggregates, this is too narrow. I considered two ways to handle it:

- **Option A:** Add a `transaction_type` column to `expenses` (or a
  renamed `transactions` table) - `ENUM('income', 'expense')`.
- **Option B:** Add the type to `categories` instead, so a category
  intrinsically *is* income or expense, and the transaction inherits
  that type by reference.

I chose **Option B** because storing the type on `categories` removes
redundancy: every transaction in the "Salary" category is income by
definition, so storing "income" on every transaction row would
duplicate information already determined by the category. This is a
3NF-preserving choice - the transaction's type is a transitive
dependency `transaction_id → category_id → category_type`, which is
exactly what 3NF disallows being stored directly on the transaction.

The `expenses` table was renamed `transactions` and the `payment_method`
column was dropped (it duplicated information already on `accounts`).

### Issue 2: No many-to-many relationships

The original schema had no many-to-many relationships - just a handful
of one-to-many. Project 3's rubric requires at least one M2M.

I added a `tags` table and a `transaction_tags` junction table so a
transaction can carry multiple cross-cutting labels (e.g.,
`tax-deductible`, `recurring`) and a single tag can apply to many
transactions. This was also a chance to demonstrate avoiding the 1NF
violation that would have occurred if I'd tried to store tags as a
comma-separated string on the transaction row.

## 5. Final Relational Schema (3NF)
users (
user_id PK,
username UNIQUE NOT NULL,
email UNIQUE NOT NULL,
first_name NOT NULL,
last_name NOT NULL,
date_joined DATE NOT NULL
)
categories (
category_id PK,
name UNIQUE NOT NULL,
category_type NOT NULL CHECK IN ('income', 'expense'),
description
)
accounts (
account_id PK,
user_id FK -> users(user_id) NOT NULL,
name UNIQUE NOT NULL,
account_type NOT NULL,
balance DECIMAL(12,2) NOT NULL DEFAULT 0,
date_opened DATE NOT NULL
)
transactions (
transaction_id PK,
user_id FK -> users(user_id) NOT NULL,
account_id FK -> accounts(account_id) NOT NULL,
category_id FK -> categories(category_id) NOT NULL,
amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
description NOT NULL,
transaction_date DATE NOT NULL
)
tags (
tag_id PK,
name UNIQUE NOT NULL
)
transaction_tags (
transaction_id FK -> transactions(transaction_id),
tag_id FK -> tags(tag_id),
PRIMARY KEY (transaction_id, tag_id)
)
budgets (
budget_id PK,
user_id FK -> users(user_id) NOT NULL,
category_id FK -> categories(category_id) NOT NULL,
budget_limit DECIMAL(10,2) NOT NULL,
start_date DATE NOT NULL,
end_date DATE NOT NULL
)

### Functional dependencies in the final schema

- `users.user_id → username, email, first_name, last_name, date_joined`
- `categories.category_id → name, category_type, description`
- `accounts.account_id → user_id, name, account_type, balance, date_opened`
- `transactions.transaction_id → user_id, account_id, category_id, amount, description, transaction_date`
- `tags.tag_id → name`
- `budgets.budget_id → user_id, category_id, budget_limit, start_date, end_date`
- `transaction_tags(transaction_id, tag_id)` - composite key, no other attributes

Every non-key attribute is functionally dependent on the (whole)
primary key of its table and only that key. The schema is in 3NF.

### How the final schema resolves each anomaly

| Anomaly | How it's fixed |
|---|---|
| Update | Renaming a category updates one row in `categories`. Transactions reference it by ID. |
| Insertion | Accounts and categories can be created independently - no transaction required. |
| Deletion | Deleting the last transaction in a category leaves the category itself intact. |
| 1NF (tags) | Tags live in their own table. Queries are clean joins, not substring matching. |

## 6. A Design Decision Worth Calling Out: Stored Balance

`accounts.balance` is technically *derivable* from the sum of related
transactions - a strict purist might call its storage a denormalization
because the value can be computed from other data. I chose to store it
explicitly for two reasons:

1. **Performance.** Showing the dashboard would otherwise require
   summing every transaction on every page load, which doesn't scale.
2. **Atomic transaction logic demonstration.** Updating the stored
   balance alongside the new transaction row, inside a single SQL
   transaction with rollback on failure, is the canonical example of
   why DB transactions exist - and is exactly what Project 3's rubric
   asks for.

The data integrity risk is mitigated by the fact that the stored
balance is *only* mutated through the same atomic transaction that
inserts, edits, or deletes a transaction row. There is no UI path
that lets a user edit the balance directly. The `edit_account` form
shows the balance as read-only text and explicitly explains that it
is derived from transaction history.

This is the kind of trade-off real systems make all the time: strict
normalization vs. read performance and clean atomic invariants. I
think the trade-off is worth it here, and the architecture protects
the integrity guarantee.

## 7. Summary

- The starting Project 4 schema was already mostly in 3NF.
- For Project 3, the `expenses` table was generalized to `transactions`,
  with the income/expense type moved to `categories` to avoid a
  transitive dependency.
- A `tags` table and `transaction_tags` junction were added to support
  many-to-many tagging without violating 1NF.
- `accounts.balance` is a deliberate, controlled denormalization to
  support atomic balance updates inside SQL transactions.
- The final 7-table schema (6 entities + 1 junction) satisfies 3NF
  and supports every functional requirement of the application.