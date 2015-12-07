from flask import Flask, render_template, request
from flask import flash, redirect, make_response
from flask import session as login_session

import database as db
from models import Category, User, Item
import json

from oauth import generateStateString, getUserDataFB
from oauth import fb_user_info_fields

app = Flask(__name__)
engine = None
DBSession = None
session = None


def isActiveSession(login_session):
    return 'user_info' in login_session.keys()


@app.route('/')
def view_main():
    return render_template('main.html')


@app.route('/login/')
def view_login():
    state = generateStateString()
    login_session['state'] = state
    return render_template('login.html', state=state)


def make_json_response(response, code):
    resp = make_response(response, code)
    resp.headers['Content-Type'] = 'application/json'
    return resp


@app.route('/fbconnect', methods=['POST'])
def fb_oauth_request():
    user = None
    user_info = {}
    # do not request real data if testing
    if app.config['TESTING'] is True:
        print "testing enabled, not adding fb user"
        # and request.data == 'testytesttest':
        user_info = {'user_id': 42}
        for f in fb_user_info_fields:
            user_info[f] = 'test_%s' % f
        login_session['state'] = 'testingstate'
        login_session['user_info'] = user_info
        flash("You are now logged in as %s" %
              user_info['username'])
        return make_json_response(json.dumps("ok"), 200)

    else:
        if request.args.get('state') != login_session['state']:
            print "fbconnect: bad state parameter"
            return make_json_response(json.dumps('invalid state parameter.'), 401)

        # continue oauth flow
        user_info = getUserDataFB(request)
        if 'error' in user_info.keys():
            return make_json_response(user_info['error'], 400)

    # oauth successful

    # check db for existing user
    try:
        user = session.query(User).filter_by(email=user_info['email']).one()
    except db.NoResultFound:
        # create a new user
        user = User()
        user.fb_id = user_info['facebook_id']
        user.email = user_info['email']
        user.picture = user_info['picture']
        user.provider = user_info['provider']
        user.name = user_info['username']
        session.add(user)
        session.commit()

    user_info['user_id'] = user.id

    flash("You are now logged in as %s" %
          user_info['username'])

    # add user to session
    login_session['user_info'] = user_info
    return make_json_response(json.dumps("ok"), 200)


@app.route('/logout/')
def view_logout():
    if not isActiveSession(login_session):
        flash("Error: You are already logged out.")
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
    items = [None]
    try:
        cat = session.query(Category).filter_by(id=id).one()
        items = session.query(Item).filter_by(category_id=id)
    except db.NoResultFound:
        flash("Category not found")
        return redirect("/category/")
    return render_template('category.html', category=cat, items=items)


@app.route('/item/')
def view_items():
    items = [None]
    try:
        items = session.query(Item).all()
    except db.NoResultFound:
        flash("No items available")
    return render_template('item.html', items=items)


@app.route('/item/<int:id>/', methods=['POST', 'GET'])
def view_item(id):
    try:
        item = session.query(Item).filter_by(
            id=id).one()
    except db.NoResultFound:
        flash("Item not found")
        return redirect("/item/")
    if request.method == 'POST':
        if not isActiveSession(login_session):
            flash("Error: not logged in.")
            return render_template('itemDetail.html', item=item)
        if request.form['requestType'] == "edit":
            item.name = request.form['itemName']
            item.category_id = request.form['category_id']
            item.description = request.form['description']
            session.add(item)
            session.commit()
            flash("%s updated." % item.name)
        elif request.form['requestType'] == "delete":
            session.delete(item)
            session.commit()
            flash("%s deleted" % item.name)
            return redirect("/item/")
    return render_template('itemDetail.html', item=item)


@app.route('/item/<int:id>/edit/')
def view_item_edit(id):
    if not isActiveSession(login_session):
        flash("Error: You must be logged in.")
        return redirect('/item/%s/' % id)
    try:
        item = session.query(Item).filter_by(id=id).one()
    except db.NoResultFound:
        flash("Item not found")
        return redirect("/item/")
    else:
        return render_template('itemEdit.html', item=item)


@app.route('/item/<int:id>/delete/')
def view_item_delete(id):
    if not isActiveSession(login_session):
        flash("Error: You must be logged in.")
        return redirect("/item/")
    try:
        item = session.query(Item).filter_by(id=id).one()
    except db.NoResultFound:
        flash("Item not found")
        return redirect("/item/")
    return render_template('itemDelete.html', item=item)


@app.route('/item/new/', methods=['POST', 'GET'])
def view_item_new():
    if request.method == 'POST':
        if not isActiveSession(login_session):
            flash("Error: You must be logged in.")
            return render_template('itemNew.html')
        newItem = Item(
            name=request.form['itemName'],
            description=request.form['description'],
            category_id=request.form['category_id'])
        session.add(newItem)
        session.commit()
        flash("%s added to items." % newItem.name)
        return redirect("/item/")

    else:
        return render_template('itemNew.html')


def init_db(path):
    global engine, DBSession, session
    engine, DBSession = db.init_db(path)
    session = DBSession()

if __name__ == '__main__':
    init_db('sqlite:///catalog.db')
    app.debug = True
    app.secret_key = "something_secret"
    app.testing = False
    app.run(host='0.0.0.0', port=8008)
