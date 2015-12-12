import unittest
from application import app, db, init_db
import application as catalog
from functools import update_wrapper


def decorator(d):
    "make function d a decorator: d wraps a function fn."
    def _d(fn):
        return update_wrapper(d(fn), fn)
    update_wrapper(_d, d)
    return _d


@decorator
def debugfunction(f):
    "log method inputs and outputs"
    def _f(*args):
        print 'args: ' + str(args)
        try:
            ret = f(*args)
            print "returned: "
            print ret
            return ret
        except TypeError:
            ret = f(args)
            print "returned: "
            print ret
            return ret
    return _f


class ApplicationTestCase(unittest.TestCase):

    'base test class for app db handling'

    def setUp(self):
        app.config['testing'] = True
        app.debug = True
        app.secret_key = "something_secret"
        app.testing = True
        self.app = app.test_client()
        init_db('sqlite://')
        # login session
        query = dict(state='testingstate')
        self.app.post('/fbconnect', query_string=query, data='testytesttest')

    def tearDown(self):
        # TODO destroy test db
        pass


def build_crud_paths(item_name, id):
    ret = ['/%s/%s/%s/' % (item_name, id, c) for c in ('edit', 'delete')]
    ret.extend([
        '/%s/' % item_name,
        '/%s/new/' % item_name,
        '/%s/%s/' % (item_name, id)])
    return ret


class TestBuildPaths(unittest.TestCase):

    def test_good(self):
        s = "obj"
        result = build_crud_paths(s, 1)
        self.assertItemsEqual(result, ['/obj/', '/obj/new/', '/obj/1/', '/obj/1/edit/', '/obj/1/delete/'])


paths = ['/', '/login/', '/logout/', '/category/']
paths.extend(build_crud_paths('item', 1))


class TestPathMeta(type):

    "metaclass to simplify path testing method generation"

    def __new__(cls, parent, bases, d):
        "override __new__ to generate multiple class methods on import"
        def buildTest(path):

            def testPath(self):
                'test that all get paths can be reached.'
                result = self.app.get(path, follow_redirects=True)
                self.assertEqual(result.status_code, 200)
            return testPath

        for p in paths:
            # generate a method name
            test_name = "test_ok_path:%s" % p
            # generate a method and add it to the class dictionary
            d[test_name] = buildTest(p)

        return type.__new__(cls, parent, bases, d)


class PathTests(ApplicationTestCase):
    __metaclass__ = TestPathMeta


class PostTests(ApplicationTestCase):

    def createItem(self, data):
        return self.app.post(
            "/item/new/",
            data=data,
            follow_redirects=True)

    def deleteItem(self, id):
        data = dict(requestType="delete")
        return self.app.post(
            "/item/%s/" % id,
            data=data,
            follow_redirects=True)

    def test_newItem(self):
        cat = catalog.Category(name="test_category")
        catalog.session.add(cat)
        data = dict(
            itemName="test_item",
            category_id=str(cat.id),
            description="Just a fake post.")
        ret = self.createItem(data)
        assert 'test_item added' in ret.data
        assert 'test_item' in self.app.get('/item/').data

    def test_delItem(self):
        '''add and then delete an item'''
        cat = catalog.Category(name="test_category")
        catalog.session.add(cat)
        data = dict(
            itemName="test_delItem",
            category_id=str(cat.id),
            description="death comes quickly for me")
        ret = self.createItem(data)
        assert 'test_delItem added' in ret.data
        # get item for id
        item = catalog.session.query(catalog.Item).filter_by(
            name=data['itemName']).one()
        print type(item.id)
        print item.id
        ret = self.deleteItem(item.id)
        if "rror" in ret.data:
            print ret
            print ret.data
        assert 'test_delItem deleted' in ret.data

    def test_editItem(self):
        '''create and then edit a item'''
        cat = catalog.Category(name="test_category")
        catalog.session.add(cat)
        cat_two = catalog.Category(name="second")
        catalog.session.add(cat_two)
        catalog.session.commit()  # this populates cat.id
        dataPre = dict(
            itemName="test_editItem_pre",
            category_id=cat.id,
            description="change comes quickly for me")

        dataPost = dict(
            requestType="edit",
            itemName="test_editedItem",
            category_id=cat_two.id,
            description="changes")
        # add a test item
        ret = self.createItem(dataPre)
        # find the item id
        qret = catalog.session.query(catalog.Item).filter_by(
            name=dataPre['itemName'])
        item = qret.one()
        assert 'test_editItem_pre added' in ret.data

        # update by id
        ret = self.app.post(
            "/item/%s/" % item.id,
            data=dataPost,
            follow_redirects=True)
        assert '%s updated' % dataPost['itemName'] in ret.data

if __name__ == '__main__':
    unittest.main()
