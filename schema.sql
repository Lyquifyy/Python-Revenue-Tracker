-- ============================================================
-- Finance Tracker - 3rd Normal Form Schema (SQLite)
-- ============================================================
-- This file is generated from the SQLAlchemy models.
-- See NORMALIZATION.md for the design decisions behind it.
-- ============================================================

PRAGMA foreign_keys = ON;

CREATE TABLE categories (
	category_id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	category_type VARCHAR(10) NOT NULL, 
	description VARCHAR(255), 
	PRIMARY KEY (category_id), 
	UNIQUE (name)
);

CREATE TABLE tags (
	tag_id INTEGER NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	PRIMARY KEY (tag_id), 
	UNIQUE (name)
);

CREATE TABLE users (
	user_id INTEGER NOT NULL, 
	username VARCHAR(50) NOT NULL, 
	email VARCHAR(100) NOT NULL, 
	first_name VARCHAR(50) NOT NULL, 
	last_name VARCHAR(50) NOT NULL, 
	date_joined DATE NOT NULL, 
	PRIMARY KEY (user_id), 
	UNIQUE (username), 
	UNIQUE (email)
);

CREATE TABLE accounts (
	account_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	account_type VARCHAR(20) NOT NULL, 
	balance NUMERIC(12, 2) NOT NULL, 
	date_opened DATE NOT NULL, 
	PRIMARY KEY (account_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id), 
	UNIQUE (name)
);

CREATE TABLE budgets (
	budget_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	category_id INTEGER NOT NULL, 
	budget_limit NUMERIC(10, 2) NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	PRIMARY KEY (budget_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id), 
	FOREIGN KEY(category_id) REFERENCES categories (category_id)
);

CREATE TABLE transactions (
	transaction_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	account_id INTEGER NOT NULL, 
	category_id INTEGER NOT NULL, 
	amount NUMERIC(12, 2) NOT NULL, 
	description VARCHAR(255) NOT NULL, 
	transaction_date DATE NOT NULL, 
	PRIMARY KEY (transaction_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id), 
	FOREIGN KEY(account_id) REFERENCES accounts (account_id), 
	FOREIGN KEY(category_id) REFERENCES categories (category_id)
);

CREATE TABLE transaction_tags (
	transaction_id INTEGER NOT NULL, 
	tag_id INTEGER NOT NULL, 
	PRIMARY KEY (transaction_id, tag_id), 
	FOREIGN KEY(transaction_id) REFERENCES transactions (transaction_id), 
	FOREIGN KEY(tag_id) REFERENCES tags (tag_id)
);

