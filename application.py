from flask import Flask, render_template, request
from flask import flash, get_flashed_messages
from flask import redirect, make_response
from flask import session as login_session
import database as db
from models import Category, User, Item, Base
from oauth import generateStateString, getUserDataFB
from oauth import fb_user_info_fields
from flask import json, jsonify
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


def resp_to_json(resp, messages):
    '''translate a dictionary including postgres models for jsonify'''
    ret = dict()
    for k, v in resp.items():
        if k == 'html':
            pass
        elif isinstance(v, Base):
            ret[k] = v.as_dict()
        elif isinstance(v, list):
            ret[k] = [i.as_dict() for i in v if i is not None]
        else:
            ret[k] = v
    ret['messages'] = messages
    return ret


@app.route('/')
def view_main():
    return render_template('main.html', login_session=login_session)


@app.route('/login/')
def view_login():
    state = generateStateString()
    login_session['state'] = state
    return render_template('login.html', login_session=login_session)


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
            flash("bad login state parameter")
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
    resp = dict(error=False)
    if request.method == 'POST':
        if login_session['state'] == request.form['state']:
            login_session.pop('state', None)
            login_session.pop('user_info', None)
            flash("You have successfully logged out")
            resp['html'] = redirect("/")
        else:
            flash("Error: Post contained bad state")
            resp['error'] = True
            resp['html'] = redirect("/")
    else:
        if not check_active_session(login_session):
            resp['error'] = True
        if resp['error']:
            resp['html'] = redirect('/')
        else:
            resp['html'] = render_template(
                'logout.html',
                user_name=login_session['user_info']['name'],
                login_session=login_session)
    return resp['html']


@app.route('/category/')
def view_category_list():
    resp = dict(error=False, categories=[None])
    try:
        resp['categories'] = session.query(Category).all()
    except db.NoResultFound:
        flash("No categories available.")
    if request.headers['Content-Type'] == 'application/json':
        return jsonify(resp_to_json(resp, get_flashed_messages()))
    else:
        return render_template(
            'categories.html',
            login_session=login_session,
            categories=resp['categories'])


@app.route('/user/<int:id>/')
def view_user(id):
    resp = dict(user=None, items=None, error=False)
    resp['user'] = session.query(User).get(id)
    if not resp['user']:
        flash("Error: User not found")
        resp['error'] = True
    if request.headers['Content-Type'] == 'application/json':
        return jsonify(resp_to_json(resp, get_flashed_messages()))
    if not resp['error']:
        resp['html'] = render_template(
            'view_user.html',
            login_session=login_session,
            user=resp['user'])
    else:
        resp['html'] = redirect('/')
    return resp['html']


@app.route('/category/<int:id>/')
def view_category(id):
    resp = dict(items=[None], category=None, error=False)
    resp['category'] = session.query(Category).get(id)
    if not resp['category']:
        flash("Error: Category not found")
        resp['error'] = True
    if request.headers['Content-Type'] == 'application/json':
        return jsonify(resp_to_json(resp, get_flashed_messages()))
    if not resp['error']:
        resp['html'] = render_template(
            'category.html',
            login_session=login_session,
            category=resp['category'])
    else:
        resp['html'] = redirect('/category/')
    return resp['html']


@app.route('/item/')
def view_items():
    resp = dict(items=None)
    try:
        resp['items'] = session.query(Item).all()
    except db.NoResultFound:
        resp['items'] = []
        flash("No items available")
    if request.headers['Content-Type'] == 'application/json':
        return jsonify(resp_to_json(resp, get_flashed_messages()))
    resp['html'] = render_template(
        'item.html',
        items=resp['items'],
        login_session=login_session)
    return resp['html']


@app.route('/item/<int:id>/', methods=['POST', 'GET'])
def view_item(id):
    resp = dict(item=None, error=False)
    resp['item'] = session.query(Item).get(id)
    if not resp['item']:
        flash("Error: Item not found")
        resp['error'] = True
    if request.method == 'POST':
        if check_active_session(login_session) and \
                login_session['user_info']['user_id'] == resp['item'].user_id:
            if request.form['requestType'] == "edit":
                print request.form
                try:
                    cat = session.query(Category).filter_by(name=request.form['category']).one()
                except db.NoResultFound:
                    cat = Category(name=request.form['category'])
                    session.add(cat)
                resp['item'].category = cat
                resp['item'].name = request.form['itemName']
                resp['item'].description = request.form['description']
                session.add(resp['item'])
                session.commit()
                flash("%s updated." % resp['item'].name)
            elif request.form['requestType'] == "delete":
                session.delete(resp['item'])
                session.commit()
                flash("%s deleted" % resp['item'].name)
                resp['html'] = redirect('/item/')
        else:
            flash("Error: only the item owner can modify this item")
            resp['error'] = True
    if request.headers['Content-Type'] == 'application/json':
        return jsonify(resp_to_json(resp, get_flashed_messages()))
    if not resp['error'] and 'html' not in resp.keys():
        resp['html'] = render_template(
            'itemDetail.html',
            login_session=login_session,
            item=resp['item'])
    else:

        resp['html'] = redirect('/item/')
    return resp['html']


@app.route('/item/<int:id>/edit/')
def view_item_edit(id):
    resp = dict(item=None, error=False)
    resp['error'] = False
    if check_active_session(login_session):
        resp['item'] = session.query(Item).get(id)
        if not resp['item']:
            flash("Error: Item not found")
            resp['error'] = True
            resp['html'] = redirect('/item/')
        else:
            if login_session['user_info']['user_id'] == resp['item'].user_id:
                resp['html'] = render_template(
                    'itemEdit.html',
                    item=resp['item'],
                    cats=session.query(Category).all(),
                    login_session=login_session)
            else:
                resp['error'] = True
                resp['html'] = redirect('/item/%s/' % id)
                flash("error: only the item owner can edit this item")
    else:
        resp['html'] = redirect('/login')

    return resp['html']


@app.route('/item/<int:id>/delete/')
def view_item_delete(id):
    resp = dict(item=None, error=False)
    if check_active_session(login_session):
        resp['item'] = session.query(Item).get(id)
        if not resp['item']:
            flash("Item not found")
            resp['error'] = True
        if resp['error']:
            resp['html'] = redirect("/item/")
        else:
            if login_session['user_info']['user_id'] == resp['item'].user_id:
                resp['html'] = render_template(
                    'itemDelete.html',
                    item=resp['item'],
                    login_session=login_session)
            else:
                resp['error'] = True
                resp['html'] = redirect("/item/%s/" % id)
                flash("Error: only the item owner can delete this item")
    else:
        resp['html'] = redirect('/login')

    return resp['html']


@app.route('/item/new/', methods=['POST'])
def view_item_new_post():
    resp = dict()
    if check_active_session(login_session):
        try:
            new_cat = session.query(Category).filter_by(name=request.form['category']).one()
        except db.NoResultFound:
            new_cat = Category(name=request.form['category'])
            session.add(new_cat)
        new_item = Item(
            name=request.form['itemName'],
            category=new_cat,
            description=request.form['description'],
            user_id=login_session['user_info']['user_id'])
        session.add(new_item)
        session.commit()
        flash("%s added to items." % new_item.name)
        resp['html'] = redirect("/item/")
    else:
        resp['html'] = redirect('/login/')
    return resp['html']


@app.route('/item/new/', methods=['GET'])
def view_item_new():
    check_active_session(login_session)
    return render_template(
        'itemNew.html',
        cats=session.query(Category).all(),
        login_session=login_session)


def init_db(path):
    global engine, DBSession, session
    engine, DBSession = db.init_db(path)
    session = DBSession()


def init_app():
    init_db('sqlite:///catalog.db')
    app.debug = True
    app.secret_key = "something_secret"
    app.testing = False


if __name__ == '__main__':
    init_app()
    app.run(host='0.0.0.0', port=8008)
