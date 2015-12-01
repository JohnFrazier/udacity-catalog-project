from flask import Flask, render_template, request
from flask import flash, redirect
import database as db
from models import Category, User, Item
from werkzeug.routing import BaseConverter
import oauth

app = Flask(__name__)
engine = None
DBSession = None
session = None


@app.route('/')
def view_main():
    return render_template('main.html')


@app.route('/login/')
def view_login():
    return render_template('login.html')


@app.route('/logout/')
def view_logout():
    return render_template('logout.html')


class objectConverter(BaseConverter):

    '''a route converter to return an object based on a path string'''

    # add models here which have a uri path
    enabled_types = (Item, Category)

    def to_python(self, value):
        '''convert a path to a object to be passed to the view method'''
        for t in self.enabled_types:
            # all enabled types must have a uri_path
            if t.uri_path == value:
                return t

# add custom convert to existing ones
app.url_map.converters['type'] = objectConverter


@app.route('/<type:metaType>/')
def view_category_list(metaType):
    '''list all items of a given type'''
    items = [None]
    try:
        items = session.query(metaType).all()
    except db.NoResultFound:
        flash("No %s available" % metaType.human_name)
    return render_template('genericList.html', objType=metaType, obj_list=items)


@app.route('/<type:metaType>/<int:obj_id>/', methods=['POST', 'GET'])
def view_generic_detail(metaType, obj_id):
    '''show item details, recieve item edit and delete posts'''
    try:
        # retreive item
        item = session.query(metaType).filter_by(
            id=obj_id).one()
    except db.NoResultFound:
        # handle bad item id
        flash("%s not found" % metaType.human_name)
        # redirect to item list on error
        return redirect("/%s/" % metaType.uri_path)
    if request.method == 'POST':
        if request.form['requestType'] == "edit":
            # model handles form data
            item.formUpdate(request.form)
            session.add(item)
            session.commit()
            flash("%s updated." % item.name)
        elif request.form['requestType'] == "delete":
            session.delete(item)
            session.commit()
            flash("%s deleted" % item.name)
            # redirect to item list on error
            return redirect("/%s/" % metaType.uri_path)
    return render_template('genericDetail.html', obj=item)


@app.route('/<type:metaType>/<int:obj_id>/edit/')
def view_generic_edit(metaType, obj_id):
    '''show edit form for model item'''

    try:
        item = session.query(metaType).filter_by(id=obj_id).one()
    except db.NoResultFound:
        flash("%s not found" % metaType.human_name)
        return redirect("/%s/" % metaType.uri_path)
    else:
        return render_template('genericEdit.html', obj=item)


@app.route('/<type:metaType>/<int:obj_id>/delete/')
def view_category_delete(metaType, obj_id):
    '''show delete form for model item'''
    try:
        item = session.query(metaType).filter_by(id=obj_id).one()
    except db.NoResultFound:
        flash("%s not found" % metaType.human_name)
        return redirect("/%s/" % metaType.uri_path)
    return render_template('genericDelete.html', obj=item)


@app.route('/<type:metaType>/new/', methods=['POST', 'GET'])
def view_category_new(metaType):
    '''show form and add new items of given type'''
    if request.method == 'POST':
        item = metaType()
        # model handles form data
        item.formUpdate(request.form)
        session.add(item)
        session.commit()
        flash("%s added to %ss." % (item.name, metaType.human_name))
        return redirect("/%s/" % metaType.uri_path)

    else:
        return render_template('genericNew.html', objType=metaType)


def init_db(path):
    global engine, DBSession, session
    engine, DBSession = db.init_db(path)
    session = DBSession()

if __name__ == '__main__':
    init_db('sqlite:///catalog.db')
    app.debug = True
    app.secret_key = "something_secret"
    app.run(host='0.0.0.0', port=8008)
