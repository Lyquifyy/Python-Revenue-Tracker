from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Account(db.Model):
    __tablename__ = 'accounts'

    account_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    account_type = db.Column(db.String(20), nullable=False)
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    def __repr__(self):
        return f'<Account {self.name}>'

class Category(db.Model):
    __tablename__ = 'categories'

    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category_type = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<Category {self.name} ({self.category_type})>'


class Transaction(db.Model):
    __tablename__ = 'transactions'

    transaction_id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
        db.Integer,
        db.ForeignKey('accounts.account_id'),
        nullable=False,
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.category_id'),
        nullable=False,
    )
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)

    account = db.relationship('Account', backref='transactions')
    category = db.relationship('Category', backref='transactions')

    def __repr__(self):
        return f'<Transaction {self.description} ${self.amount}>'

@app.route('/')
def hello():
    accounts = Account.query.all()
    categories = Category.query.all()
    transactions = Transaction.query.order_by(Transaction.transaction_date.desc()).all()

    return render_template(
        'index.html',
        accounts=accounts,
        categories=categories,
        transactions=transactions,
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)