from flask import Flask, render_template, request
from flask import flash, redirect
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
        flash("No categories available.")
    return render_template('categories.html', categories=cats)


@app.route('/category/<int:id>/')
def view_category(id):
    try:
        cat = session.query(Category).filter_by(id=id).one()
    except db.NoResultFound:
        flash("Category not found")
        return redirect("/category/")
    return render_template('category.html', category=cat)


@app.route('/item/')
def view_item_one():
    if request.method == 'GET':
        items = [None]
        try:
            items = session.query(Item).all()
        except db.NoResultFound:
            flash("No items available")
        return render_template('item.html', items=items)
    # TODO: receive posted new items


@app.route('/item/<int:id>/')
def view_item(id):
    if request.method == 'GET':
        try:
            item = session.query(Item).filter_by(id=id).one()
        except db.NoResultFound:
            flash("Item not found")
            return redirect("/item/")
        return render_template('item.html', item=item)
    else:
        pass
        # TODO: receive posted updated and deleted items


@app.route('/item/<int:id>/edit/')
def view_item_edit(id):
    try:
        item = session.query(Item).filter_by(id=id).one()
    except db.NoResultFound:
        flash("Item not found")
        return redirect("/item/")
    return render_template('itemEdit.html', item=item)


@app.route('/item/<int:id>/delete/')
def view_item_delete(id):
    try:
        item = session.query(Item).filter_by(id=id).one()
    except db.NoResultFound:
        flash("Item not found")
        return redirect("/item/")
    return render_template('itemDelete.html', item=item)


@app.route('/item/new/', methods=['POST', 'GET'])
def view_item_new():
    cats = session.query(Category).all()
    if request.method == 'POST':

        if request.form['categoryName'] not in cats:
            cat = Category(name=request.form['categoryName'])
            session.add(cat)
            flash("%s added to categories." % cat.name)
        else:
            cat = session.query(Category).filter_by(request.form['CategoryName'])

        newItem = Item(
            name=request.form['itemName'],
            description=request.form['description'],
            category_id=cat.id)
        # TODO user_id=...
        session.add(newItem)
        session.commit()
        flash("%s added to items." % newItem.name)
        return redirect("/item/")

    else:
        return render_template('itemNew.html', categories=cats)


def init_db(path):
    global engine, DBSession, session
    engine, DBSession = db.init_db(path)
    session = DBSession()

if __name__ == '__main__':
    init_db('sqlite:///catalog.db')
    app.debug = True
    app.secret_key = "something_secret"
    app.run(host='0.0.0.0', port=8008)
