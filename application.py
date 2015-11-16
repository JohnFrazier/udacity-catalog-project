from flask import Flask, render_template
import database as db

import oauth

app = Flask(__name__)
engine = None
DBSession = None


@app.route('/')
def mainview():
    return render_template('main.html')

if __name__ == '__main__':
    engine, DBSession = db.init_db('sqlite:///catalog.db')
    secret_key = "something_secret"
    app.debug = True
    app.run(host='0.0.0.0', port=8008)
