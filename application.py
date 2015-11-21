from flask import Flask, render_template, request
import database as db
from models import Category, User, Item

import oauth

app = Flask(__name__)
engine = None
DBSession = None
session = None


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
def view_category_list():
    try:
        cats = session.query(Category).all()
    except db.NoResultFound:
        return "No categories available."
    return render_template('categories.html', categories=cats)


@app.route('/category/<int:id>/')
def view_category(id):
    try:
        cat = session.query(Category).filter_by(id=id).one()
    except db.NoResultFound:
        return "Category not found"
    return render_template('category.html', category=cat)


@app.route('/item/')
def view_item_one():
    if request.method == 'GET':
        try:
            item = session.query(Item).one()
        except db.NoResultFound:
            return "No items available."
        return render_template('item.html', item=item)
    # TODO: receive posted new items


@app.route('/item/<int:id>/')
def view_item(id):
    if request.method == 'GET':
        try:
            item = session.query(Item).filter_by(id=id).one()
        except db.NoResultFound:
            # TODO flash("item not found")
            return "Item not found"
        return render_template('item.html', item=item)
    else:
        print request.method
    # TODO: receive posted updated and deleted items


@app.route('/item/<int:id>/edit/')
def view_item_edit(id):
    try:
        item = session.query(Item).filter_by(id=id).one()
    except db.NoResultFound:
        return "Item not found"
    return render_template('itemEdit.html', item=item)


@app.route('/item/<int:id>/delete/')
def view_item_delete(id):
    try:
        item = session.query(Item).filter_by(id=id).one()
    except db.NoResultFound:
        return "Item not found"
    return render_template('itemDelete.html', item)


@app.route('/item/new/')
def view_item_new():
    return render_template('itemNew.html')


def init_db():
    global engine, DBSession, session
    engine, DBSession = db.init_db('sqlite:///catalog.db')
    session = DBSession()

if __name__ == '__main__':
    init_db()
    app.debug = True
    secret_key = "something_secret"
    app.run(host='0.0.0.0', port=8008)
