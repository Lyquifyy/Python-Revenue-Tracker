from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello():
    return '<h1>Finance Tracker</h1><p>It lives!</p>'


if __name__ == '__main__':
    app.run(debug=True)