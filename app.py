from datetime import date
from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField
from wtforms.validators import DataRequired, NumberRange, Length
from sqlalchemy.exc import IntegrityError

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

@app.route('/')
def hello():
    accounts = Account.query.all()
    categories = Category.query.all()
    transactions = Transaction.query.order_by(Transaction.transaction_date.desc()).all()
    budgets = Budget.query.all()

    return render_template(
        'index.html',
        accounts=accounts,
        categories=categories,
        transactions=transactions,
        budgets=budgets,
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