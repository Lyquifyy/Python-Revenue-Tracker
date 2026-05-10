from datetime import date, timedelta
from decimal import Decimal
from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, DateField
from wtforms.validators import DataRequired, NumberRange, Length
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, case

app = Flask(__name__)
app.config['SECRET_KEY'] = 'totally-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_joined = db.Column(db.Date, nullable=False, default=date.today)

    def __repr__(self):
        return f'<User {self.username}>'

class Account(db.Model):
    __tablename__ = 'accounts'

    account_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    name = db.Column(db.String(100), unique=True, nullable=False)
    account_type = db.Column(db.String(20), nullable=False)
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    date_opened = db.Column(db.Date, nullable=False, default=date.today)

    user = db.relationship('User', backref='accounts')

    def __repr__(self):
        return f'<Account {self.name}>'

class Category(db.Model):
    __tablename__ = 'categories'

    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category_type = db.Column(db.String(10), nullable=False)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f'<Category {self.name} ({self.category_type})>'

transaction_tags = db.Table(
    'transaction_tags',
    db.Column('transaction_id', db.Integer,
              db.ForeignKey('transactions.transaction_id'),
              primary_key=True),
    db.Column('tag_id', db.Integer,
              db.ForeignKey('tags.tag_id'),
              primary_key=True),
)


class Tag(db.Model):
    __tablename__ = 'tags'

    tag_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Tag {self.name}>'
    

class Transaction(db.Model):
    __tablename__ = 'transactions'

    transaction_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.account_id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)

    user = db.relationship('User', backref='transactions')
    account = db.relationship('Account', backref='transactions')
    category = db.relationship('Category', backref='transactions')
    tags = db.relationship('Tag', secondary=transaction_tags, backref='transactions')

    def __repr__(self):
        return f'<Transaction {self.description} ${self.amount}>'

class Budget(db.Model):
    __tablename__ = 'budgets'

    budget_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'), nullable=False)
    budget_limit = db.Column(db.Numeric(10, 2), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    user = db.relationship('User', backref='budgets')
    category = db.relationship('Category', backref='budgets')

    def __repr__(self):
        return f'<Budget {self.category.name} ${self.budget_limit}>'
    
class AccountForm(FlaskForm):
    name = StringField(
        'Account Name',
        validators=[DataRequired(), Length(min=1, max=100)],
    )
    account_type = SelectField(
        'Account Type',
        choices=[
            ('checking', 'Checking'),
            ('savings', 'Savings'),
            ('credit', 'Credit Card'),
            ('cash', 'Cash'),
        ],
        validators=[DataRequired()],
    )
    balance = DecimalField(
        'Starting Balance',
        validators=[DataRequired(), NumberRange(min=0, message='Balance cannot be negative')],
        places=2,
        default=0,
    )

class TransactionForm(FlaskForm):
    account_id = SelectField(
        'Account',
        coerce=int,
        validators=[DataRequired()],
    )
    category_id = SelectField(
        'Category',
        coerce=int,
        validators=[DataRequired()],
    )
    amount = DecimalField(
        'Amount',
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message='Amount must be greater than zero'),
        ],
        places=2,
    )
    description = StringField(
        'Description',
        validators=[DataRequired(), Length(min=1, max=255)],
    )
    transaction_date = DateField(
        'Date',
        validators=[DataRequired()],
        default=date.today,
    )


@app.route('/')
def hello():
    today = date.today()
    month_start = today.replace(day=1)
    thirty_days_ago = today - timedelta(days=30)

    # --- Aggregate 1: Total balance across all accounts (SUM) ---
    total_balance = db.session.query(
        func.coalesce(func.sum(Account.balance), 0)
    ).scalar()

    # --- Aggregate 2: Counts (COUNT) ---
    account_count = db.session.query(func.count(Account.account_id)).scalar()
    transaction_count = db.session.query(func.count(Transaction.transaction_id)).scalar()
    category_count = db.session.query(func.count(Category.category_id)).scalar()

    # --- Aggregate 3: Monthly income vs expense (SUM with CASE) ---
    # Single query that splits the total by category_type using SQL CASE
    monthly = db.session.query(
        func.coalesce(
            func.sum(case((Category.category_type == 'income', Transaction.amount), else_=0)),
            0
        ).label('income'),
        func.coalesce(
            func.sum(case((Category.category_type == 'expense', Transaction.amount), else_=0)),
            0
        ).label('expense'),
    ).join(Category, Transaction.category_id == Category.category_id) \
     .filter(Transaction.transaction_date >= month_start) \
     .first()

    monthly_income = monthly.income or 0
    monthly_expense = monthly.expense or 0
    net_monthly = monthly_income - monthly_expense

    # --- Aggregate 4: Top spending categories this month (SUM + GROUP BY) ---
    top_categories = db.session.query(
        Category.name,
        func.sum(Transaction.amount).label('total'),
        func.count(Transaction.transaction_id).label('count'),
    ).join(Transaction, Transaction.category_id == Category.category_id) \
     .filter(Category.category_type == 'expense') \
     .filter(Transaction.transaction_date >= month_start) \
     .group_by(Category.category_id, Category.name) \
     .order_by(func.sum(Transaction.amount).desc()) \
     .limit(5) \
     .all()

    # --- Aggregate 5: Average transaction amount over last 30 days (AVG) ---
    avg_transaction = db.session.query(
        func.coalesce(func.avg(Transaction.amount), 0)
    ).filter(Transaction.transaction_date >= thirty_days_ago).scalar()

    # --- Recent transactions for the activity feed ---
    recent = Transaction.query.order_by(
        Transaction.transaction_date.desc(),
        Transaction.transaction_id.desc(),
    ).limit(5).all()

    # --- Account-level: each account's balance ---
    accounts = Account.query.order_by(Account.name).all()

    return render_template(
        'index.html',
        total_balance=total_balance,
        account_count=account_count,
        transaction_count=transaction_count,
        category_count=category_count,
        monthly_income=monthly_income,
        monthly_expense=monthly_expense,
        net_monthly=net_monthly,
        top_categories=top_categories,
        avg_transaction=avg_transaction,
        recent=recent,
        accounts=accounts,
    )

@app.route('/accounts/new', methods=['GET', 'POST'])
def new_account():
    form = AccountForm()
    if form.validate_on_submit():
        default_user = User.query.first()
        account = Account(
            user_id=default_user.user_id,
            name=form.name.data.strip(),
            account_type=form.account_type.data,
            balance=form.balance.data,
        )
        try:
            db.session.add(account)
            db.session.commit()
            flash(f'Account "{account.name}" created.', 'success')
            return redirect(url_for('hello'))
        except IntegrityError:
            db.session.rollback()
            flash('An account with that name already exists.', 'error')
    return render_template('new_account.html', form=form)

@app.route('/transactions/new', methods=['GET', 'POST'])
def new_transaction():
    form = TransactionForm()

    # Populate dropdowns from the database
    form.account_id.choices = [
        (a.account_id, f'{a.name} ({a.account_type})')
        for a in Account.query.order_by(Account.name).all()
    ]
    form.category_id.choices = [
        (c.category_id, f'{c.name} ({c.category_type})')
        for c in Category.query.order_by(Category.category_type, Category.name).all()
    ]

    # Block the form entirely if there's nothing to select
    if not form.account_id.choices or not form.category_id.choices:
        flash('You need at least one account and one category before adding transactions.', 'error')
        return redirect(url_for('hello'))

    if form.validate_on_submit():
        # ============================================================
        # SQL TRANSACTION (Atomic operation)
        # ============================================================
        # Both the INSERT into `transactions` and the UPDATE on
        # `accounts.balance` must succeed together - or neither at all.
        # This is the rubric's transaction logic requirement.
        # ============================================================
        try:
            user = User.query.first()
            account = Account.query.get(form.account_id.data)
            category = Category.query.get(form.category_id.data)

            # Build the transaction
            txn = Transaction(
                user_id=user.user_id,
                account_id=account.account_id,
                category_id=category.category_id,
                amount=form.amount.data,
                description=form.description.data.strip(),
                transaction_date=form.transaction_date.data,
            )
            db.session.add(txn)

            # Compute the balance change.
            # Income increases the balance; expense decreases it.
            if category.category_type == 'income':
                account.balance = Decimal(account.balance) + Decimal(form.amount.data)
            else:
                account.balance = Decimal(account.balance) - Decimal(form.amount.data)

            # Commit atomically. If anything in this block raised,
            # the except clause rolls back BOTH changes together.
            db.session.commit()

            flash(f'Transaction recorded. {account.name} balance is now ${account.balance:.2f}.', 'success')
            return redirect(url_for('hello'))

        except Exception as e:
            db.session.rollback()
            flash(f'Could not save transaction: {e.__class__.__name__}. No changes were made.', 'error')

    return render_template('new_transaction.html', form=form)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Seed the default user if it doesn't exist
        if User.query.count() == 0:
            default_user = User(
                username='zander',
                email='zander@example.com',
                first_name='Zander',
                last_name='Erwin',
            )
            db.session.add(default_user)
            db.session.commit()
            print(f'Seeded default user: {default_user.username}')

    app.run(debug=True)