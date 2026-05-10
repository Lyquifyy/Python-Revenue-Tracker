from flask import Flask
from flask_sqlalchemy import SQLAlchemy

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


@app.route('/')
def hello():
    accounts = Account.query.all()
    return f'<h1>Finance Tracker</h1><p>Accounts in DB: {len(accounts)}</p>'


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)