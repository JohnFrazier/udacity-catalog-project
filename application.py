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


@app.route('/login/')
def view_login():
    return render_template('login.html')


@app.route('/logout/')
def view_logout():
    return render_template('logout.html')


@app.route('/category/')
def view_category_list():
    metaType = Category
    items = [None]
    try:
        items = session.query(metaType).all()
    except db.NoResultFound:
        flash("No %s available" % metaType.human_name)
    return render_template('genericList.html', objType=metaType, obj_list=items)


@app.route('/category/<int:id>/', methods=['POST', 'GET'])
def view_category(id):
    metaType = Category
    try:
        item = session.query(metaType).filter_by(
            id=id).one()
    except db.NoResultFound:
        flash("%s not found" % metaType.human_name)
        return redirect("/%s/" % metaType.uri_path)
    if request.method == 'POST':
        if request.form['requestType'] == "edit":
            item.formUpdate(request.form)
            session.add(item)
            session.commit()
            flash("%s updated." % item.name)
        elif request.form['requestType'] == "delete":
            session.delete(item)
            session.commit()
            flash("%s deleted" % item.name)
            return redirect("/%s/" % metaType.uri_path)
    return render_template('genericDetail.html', obj=item)


@app.route('/category/<int:id>/edit/')
def view_category_edit(id):
    metaType = Category
    try:
        item = session.query(metaType).filter_by(id=id).one()
    except db.NoResultFound:
        flash("%s not found" % metaType.human_name)
        return redirect("/%s/" % metaType.uri_path)
    else:
        return render_template('genericEdit.html', obj=item)


@app.route('/category/<int:id>/delete/')
def view_category_delete(id):
    metaType = Category
    try:
        item = session.query(metaType).filter_by(id=id).one()
    except db.NoResultFound:
        flash("%s not found" % metaType.human_name)
        return redirect("/%s/" % metaType.uri_path)
    return render_template('genericDelete.html', obj=item)


@app.route('/category/new/', methods=['POST', 'GET'])
def view_category_new():
    metaType = Category
    if request.method == 'POST':
        item = metaType()
        item.formUpdate(request.form)
        session.add(item)
        session.commit()
        flash("%s added to %ss." % (item.name, metaType.human_name))
        return redirect("/%s/" % metaType.uri_path)

    else:
        return render_template('genericNew.html', objType=metaType)


# TODO merge duplicated code with above
@app.route('/item/')
def view_items():
    metaType = Item
    items = [None]
    try:
        items = session.query(metaType).all()
    except db.NoResultFound:
        flash("No items available")
    return render_template('genericList.html', objType=metaType, obj_list=items)


@app.route('/item/<int:id>/', methods=['POST', 'GET'])
def view_item(id):
    metaType = Item
    try:
        item = session.query(metaType).filter_by(
            id=id).one()
    except db.NoResultFound:
        flash("%s not found" % metaType.human_name)
        return redirect("/%s/" % metaType.uri_path)
    if request.method == 'POST':
        if request.form['requestType'] == "edit":
            item.formUpdate(request.form)
            session.add(item)
            session.commit()
            flash("%s updated." % item.name)
        elif request.form['requestType'] == "delete":
            session.delete(item)
            session.commit()
            flash("%s deleted" % item.name)
            return redirect("/%s/" % metaType.uri_path)
    return render_template('genericDetail.html', obj=item)


@app.route('/item/<int:id>/edit/')
def view_item_edit(id):
    metaType = Item
    try:
        item = session.query(metaType).filter_by(id=id).one()
    except db.NoResultFound:
        flash("%s not found" % metaType.human_name)
        return redirect("/%s/" % metaType.uri_path)
    else:
        return render_template('genericEdit.html', obj=item)


@app.route('/item/<int:id>/delete/')
def view_item_delete(id):
    metaType = Item
    try:
        item = session.query(metaType).filter_by(id=id).one()
    except db.NoResultFound:
        flash("%s not found" % metaType.human_name)
        return redirect("/%s/" % metaType.uri_path)
    return render_template('genericDelete.html', obj=item)


@app.route('/item/new/', methods=['POST', 'GET'])
def view_item_new():
    metaType = Item
    if request.method == 'POST':
        item = metaType()
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
