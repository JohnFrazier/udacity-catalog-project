from flask import Flask, render_template, request, url_for
from flask import flash, get_flashed_messages
from flask import redirect, make_response
from flask import session as login_session
import database as db
from models import Category, User, Item, Base, Image
from models import desc, datetime
from oauth import generateStateString, getUserDataFB
from oauth import fb_user_info_fields
from flask import json, jsonify, send_from_directory
import os

from werkzeug import secure_filename
from appforms import ItemForm, ItemDeleteForm, LogoutForm
from werkzeug.contrib.atom import AtomFeed

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_DIR'] = './uploads/'

ALLOWED_EXTENSIONS = set(['png', 'jpeg', 'jpg'])
APP_SECRET_FILENAME = "./secrets/application_secret"
engine = None
DBSession = None
session = None


def check_active_session(login_session):
    '''check for session status and error if not'''
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
    cats = session.query(Category).all()
    recent_items = session.query(Item).order_by(desc(Item.id)).limit(10)
    return render_template(
        'main.html',
        login_session=login_session,
        categories=cats,
        recent_items=recent_items)


@app.route('/login/')
def view_login():
    '''show login page'''
    state = generateStateString()
    login_session['state'] = state
    return render_template('login.html', login_session=login_session)


def make_json_response(response, code):
    '''give json response the proper headers'''
    resp = make_response(response, code)
    resp.headers['Content-Type'] = 'application/json'
    return resp


@app.route('/fbconnect', methods=['POST'])
def fb_oauth_request():
    '''handle facebook oauth requests'''
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
    '''show logout form and handle its requests'''
    resp = dict(error=False)
    lo_form = LogoutForm()
    if lo_form.validate_on_submit():
        if login_session['state'] == lo_form.state.data:
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
                login_session=login_session, form=lo_form)
    return resp['html']


@app.route('/category/')
def view_category_list():
    '''show a list of categories'''
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
    '''show user details'''
    resp = dict(user=None, error=False)
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
    '''show category details'''
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
    '''show a list of items in the db'''
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


def pop_category(category, session):
    '''remove category from session if unused'''
    if not category or not session:
        return
    cat_n = session.query(Category).\
        filter_by(name=category.name).\
        count()
    if cat_n == 1:
        session.delete(category)


def update_category(new_cat_name, session, old_cat):
    '''add new category to session if it doesn't exist'''

    # see if category exists
    if old_cat:
        if new_cat_name == old_cat.name:
            return old_cat
        try:
            cat = session.query(Category).filter_by(name=new_cat_name).one()
        except db.NoResultFound:
            cat = Category(name=new_cat_name)
            session.add(cat)
    else:
        cat = Category(name=new_cat_name)
        session.add(cat)
    # remove unused category
    pop_category(old_cat, session)
    return cat


def allowed_file(filename):
    '''check filename is of the correct type'''
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def push_image(session, orig_filename):
    '''generate filename and add file image to db'''
    filename = str(login_session['user_info']['user_id']) + secure_filename(orig_filename)
    new_image = Image(
        original_name=orig_filename,
        user_id=login_session['user_info']['user_id'],
        filename=filename)
    session.add(new_image)
    return new_image


@app.route('/item/<int:id>/', methods=['POST'])
def view_item_post(id):
    '''handle post requests for an item'''
    if not check_active_session(login_session) and \
            'user_info' not in login_session.keys():
        flash("Error: invalid session")
        return redirect('/item/')

    item = session.query(Item).get(id)
    if not item:
        flash("Error: Item not found")
        return redirect('/item/')

    # ensure logged in user owns the item
    if not login_session['user_info']['user_id'] == item.user_id:
        flash("Error: You are not logged in")
        return redirect('/login/')

    edit_form = ItemForm()
    if edit_form.validate_on_submit():
        # update image if included
        item.image = push_image(session, edit_form.image.data.filename)
        if item.category != edit_form.category.data:
            # update category if changed
            item.category = update_category(
                edit_form.category.data, session, item.category)
        # update item
        item.name = edit_form.name.data
        item.description = edit_form.description.data
        item.updated_date = datetime.utcnow()
        session.add(item)
        # save image near commit
        edit_form.image.data.save(os.path.join(app.config['UPLOAD_DIR'], item.image.filename))
        session.commit()
        flash("%s updated." % item.name)
        return redirect("/item/%s/" % item.id)

    del_form = ItemDeleteForm()
    if del_form.validate_on_submit():
        # remove unused category
        pop_category(item.category, session)
        # remove item
        session.delete(item)
        session.commit()
        flash("%s deleted" % item.name)
        return redirect('/item/')


@app.route('/item/<int:id>/', methods=['GET'])
def view_item(id):
    '''show item details'''
    resp = dict(item=None, error=False)
    # get item
    resp['item'] = session.query(Item).get(id)
    if not resp['item']:
        flash("Error: Item not found")
        resp['error'] = True
    # return as json if requested
    if request.headers['Content-Type'] == 'application/json':
        return jsonify(resp_to_json(resp, get_flashed_messages()))
    # build html if item was found
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
    '''show item editing form'''
    resp = dict(item=None, error=False)
    resp['error'] = False
    # ensure session is active
    if check_active_session(login_session) and \
            'user_info' in login_session.keys():
        resp['item'] = session.query(Item).get(id)
        if not resp['item']:
            flash("Error: Item not found")
            resp['error'] = True
            resp['html'] = redirect('/item/')
        else:
            form = ItemForm()
            # set default values in form
            p = resp['item'].as_dict()
            form.name.data = p['name']
            form.category.data = p['category']
            form.description.data = p['description']
            # check login status before sending template
            if login_session['user_info'] and \
                    login_session['user_info']['user_id'] == resp['item'].user_id:
                resp['html'] = render_template(
                    'itemEdit.html',
                    item=resp['item'],
                    cats=session.query(Category).all(),
                    login_session=login_session,
                    form=form)
            else:
                resp['error'] = True
                resp['html'] = redirect('/item/%s/' % id)
                flash("error: only the item owner can edit this item")
    else:
        flash("Error: you are not logged in")
        resp['html'] = redirect('/login')

    return resp['html']


@app.route('/item/<int:id>/delete/')
def view_item_delete(id):
    '''show a form for deleting an item'''
    resp = dict(item=None, error=False)
    form = ItemDeleteForm()
    # check session status and user is logged in
    if check_active_session(login_session) and \
            'user_info' in login_session.keys():
        # try to fetch the item
        resp['item'] = session.query(Item).get(id)
        if not resp['item']:
            flash("Item not found")
            resp['error'] = True
        if resp['error']:
            resp['html'] = redirect("/item/")
        else:
            # ensure user has logged in before sending template
            if login_session['user_info']['user_id'] == resp['item'].user_id:
                resp['html'] = render_template(
                    'itemDelete.html',
                    item=resp['item'],
                    form=form,
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
    '''handle new item requests'''
    # ensure user is logged in and session is active
    if not check_active_session(login_session) and \
            'user_info' not in login_session.keys():
        flash("Error: you are not logged in.")
        return redirect('/login/')

    form = ItemForm()
    if form.validate_on_submit():
        # add category if needed
        try:
            new_cat = session.query(Category).filter_by(name=form.category.data).one()
        except db.NoResultFound:
            new_cat = Category(name=form.category.data)
            session.add(new_cat)
        # create db image
        new_image = push_image(session, form.image.data.filename)
        # create item
        new_item = Item(
            name=form.name.data,
            category=new_cat,
            description=form.description.data,
            created_date=datetime.utcnow(),
            updated_date=datetime.utcnow(),
            user_id=login_session['user_info']['user_id'],
            image=new_image)
        # update db
        session.add(new_item)
        session.commit()
        # save image near commit
        form.image.data.save(os.path.join(app.config['UPLOAD_DIR'], new_image.filename))
        flash("%s added to items." % new_item.name)
        return redirect('/item/')
    else:
        flash('Error: bad form %s' % form.errors)
        return redirect('/item/new/')


@app.route('/item/new/', methods=['GET'])
def view_item_new():
    '''show new item form'''
    form = ItemForm()
    # ensure user is logged in
    if check_active_session(login_session) and \
            'user_info' in login_session.keys():
        return render_template(
            'itemNew.html',
            cats=session.query(Category).all(),
            login_session=login_session,
            form=form)
    else:
        flash("Error: you are not logged in")
        return redirect('/login/')


@app.route('/uploads/<string:filename>/')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_DIR'], filename)


@app.route('/recent_feed.xml')
def recent_feed():
    feed = AtomFeed(
        "Catalog",
        feed_url=request.host_url,
        subtitle="Recent item feed for Catalog")
    for item in session.query(Item).order_by(desc(Item.id)).limit(10).all():
        feed.add(
            item.name,
            item.description,
            content_type='html',
            owner=item.user.name,
            url=url_for('view_item', id=item.id, _external=True),
            updated=item.updated_date,
            created=item.created_date)

    return feed.get_response()


def init_db(path):
    '''initialize database and session'''
    global engine, DBSession, session
    engine, DBSession = db.init_db(path)
    session = DBSession()


def init_app():
    '''initialize debug application'''
    init_db('sqlite:///catalog.db')
    app.debug = True
    assert os.path.exists(APP_SECRET_FILENAME)
    with open(APP_SECRET_FILENAME, 'r') as f:
        app.secret_key = f.read()
        del f
    assert app.secret_key
    app.testing = False


if __name__ == '__main__':
    init_app()
    app.run(host='0.0.0.0', port=8008)
