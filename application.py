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


def check_active_session(login_session):
    if 'user_info' in login_session.keys():
        return True
    else:
        flash("Error user not logged in.")
        return False


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
        print "testing enabled, adding fake fb user"
        # and request.data == 'testytesttest':
        for f in fb_user_info_fields:
            user_info[f] = 'test_%s' % f
        login_session['state'] = 'testingstate'
        login_session['user_info'] = user_info
        flash("You are now logged in as %s" %
              user_info['name'])
        user = User()
        user.fb_id = "12345"
        user.email = user_info['email']
        user.picture = user_info['picture']
        user.provider = user_info['provider']
        user.name = user_info['name']
        session.add(user)
        session.commit()
        # add id after .commit() assigns it
        user_info['user_id'] = user.id

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
        user.name = user_info['name']
        session.add(user)
        session.commit()

    user_info['user_id'] = user.id

    flash("You are now logged in as %s" %
          user_info['name'])

    # add user to session
    login_session['user_info'] = user_info
    return make_json_response(json.dumps("ok"), 200)


@app.route('/logout/', methods=['POST', 'GET'])
def view_logout():
    if request.method == 'POST':
        if login_session['state'] == request.form['state']:
            login_session.pop('state', None)
            login_session.pop('user_info', None)
            flash("You have successfully logged out")
            return redirect("/")
        else:
            flash("Error: Post contained bad state")
        return render_template(
            'logout.html',
            user_name=login_session['user_info']['name'],
            state=login_session['state'])
    else:
        check_active_session(login_session)
        return render_template(
            'logout.html',
            user_name=login_session['user_info']['name'],
            state=login_session['state'])


@app.route('/category/')
def view_category_list():
    try:
        cats = session.query(Category).all()
    except db.NoResultFound:
        flash("No categories available.")
    return render_template('categories.html', categories=cats)


@app.route('/user/<int:id>/')
def view_user(id):
    resp = dict(user=None, items=None)
    try:
        resp['user'] = session.query(User).filter_by(id=id).one()
        resp['items'] = session.query(Item).filter_by(user_id=id).all()
    except db.NoResultFound:
        resp['items'] = None
        resp['user'] = None
    return render_template('view_user.html', items=resp['items'], user=resp['user'])


@app.route('/category/<int:id>/')
def view_category(id):
    resp = dict(items=[None], cat=None)
    try:
        resp['cat'] = session.query(Category).filter_by(id=id).one()
        resp['items'] = session.query(Item).filter_by(category_id=id)
    except db.NoResultFound:
        flash("Category not found")
        return redirect("/category/")
    return render_template(
        'category.html', category=resp['cat'], items=resp['items'])


@app.route('/item/')
def view_items():
    resp = dict(items=None)
    try:
        resp['items'] = session.query(Item).all()
    except db.NoResultFound:
        flash("No items available")
    return render_template('item.html', items=resp['items'])


@app.route('/item/<int:id>/', methods=['POST', 'GET'])
def view_item(id):
    resp = dict(item=None)
    try:
        resp['item'] = session.query(Item).filter_by(
            id=id).one()
    except db.NoResultFound:
        flash("Error: Item not found")
    if resp['item'] is None:
        return redirect('/item/')
    else:
        if request.method == 'POST':
            if check_active_session(login_session):
                if not login_session['user_info']['user_id'] == resp['item'].user_id:
                    flash("Error: only the item owner can modify this item")
                else:
                    if request.form['requestType'] == "edit":
                        resp['item'].name = request.form['itemName']
                        resp['item'].category_id = request.form['category_id']
                        resp['item'].description = request.form['description']
                        session.add(resp['item'])
                        session.commit()
                        flash("%s updated." % resp['item'].name)
                    elif request.form['requestType'] == "delete":
                        session.delete(resp['item'])
                        session.commit()
                        flash("%s deleted" % resp['item'].name)
                        return redirect('/item/')
        return render_template('itemDetail.html', item=resp['item'])


@app.route('/item/<int:id>/edit/')
def view_item_edit(id):
    resp = dict(item=None)
    if check_active_session(login_session):
        try:
            resp['item'] = session.query(Item).filter_by(id=id).one()
        except db.NoResultFound:
            flash("Error: Item not found")
            return redirect("/item/")
        if not login_session['user_info']['user_id'] == resp['item'].user_id:
            flash("Error: only the item owner can edit this item")
            return redirect("/item/%s/" % id)
        return render_template('itemEdit.html', item=resp['item'])
    return redirect('/item/%s/' % id)


@app.route('/item/<int:id>/delete/')
def view_item_delete(id):
    resp = dict(item=None)
    if check_active_session(login_session):
        try:
            resp['item'] = session.query(Item).filter_by(id=id).one()
        except db.NoResultFound:
            flash("Item not found")
            return redirect("/item/")
        if not login_session['user_info']['user_id'] == resp['item'].user_id:
            flash("Error: only the item owner can delete this item")
            return redirect("/item/%s/" % id)
        return render_template('itemDelete.html', item=resp['item'])
    return redirect("/item/%s/" % id)


@app.route('/item/new/', methods=['POST', 'GET'])
def view_item_new():
    if request.method == 'POST':
        if check_active_session(login_session):
            newItem = Item(
                name=request.form['itemName'],
                description=request.form['description'],
                category_id=request.form['category_id'],
                user_id=login_session['user_info']['user_id'])
            session.add(newItem)
            session.commit()
            flash("%s added to items." % newItem.name)
            return redirect("/item/")
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
    session.add(Category(name="test"))
    session.commit()
    app.run(host='0.0.0.0', port=8008)
