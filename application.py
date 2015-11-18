from flask import Flask, render_template
import database as db

import oauth

app = Flask(__name__)
engine = None
DBSession = None


@app.route('/')
def view_main():
    return render_template('main.html')


@app.route('/login')
def view_login():
    return render_template('login.html')


@app.route('/logout')
def view_logout():
    return render_template('logout.html')


@app.route('/category/')
def view_category_one():
    return render_template('category.html')


@app.route('/category/<int:id>/')
def view_category(id):
    return render_template('category.html')


@app.route('/item/')
def view_item_one():
    return render_template('item.html')


@app.route('/item/<int:id>/')
def view_item(id):
    return render_template('item.html')


@app.route('/item/<int:id>/edit/')
def view_item_edit(id):
    return render_template('itemEdit.html')


@app.route('/item/<int:id>/delete/')
def view_item_delete(id):
    return render_template('itemDelete.html')


@app.route('/item/new/')
def view_item_new():
    return render_template('itemNew.html')


if __name__ == '__main__':
    engine, DBSession = db.init_db('sqlite:///catalog.db')
    secret_key = "something_secret"
    app.debug = True
    app.run(host='0.0.0.0', port=8008)
