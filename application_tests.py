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
        self.app = app.test_client()
        init_db('sqlite://')

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


paths = ['/', '/login/', '/logout/']
paths.extend(build_crud_paths('item', 1))
paths.extend(build_crud_paths('category', 1))


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

    def createItem(self, item_case):
        data = {}
        for i in catalog.Item.newFormData:
            data[i['db_name']] = item_case[i['db_name']]
        return self.app.post(
            "/%s/new/" % catalog.Item.uri_path,
            data=data,
            follow_redirects=True)

    def deleteItem(self, id):
        data = dict(requestType="delete")
        return self.app.post(
            "/%s/%s/" % (catalog.Item.uri_path, id),
            data=data,
            follow_redirects=True)

    def test_newItem(self):
        cat = catalog.Category(name="test_category")
        catalog.session.add(cat)
        item_case = {
            "name": "test_item",
            "description": "test_description",
            "category_id": str(cat.id)}
        ret = self.createItem(item_case)
        assert '%s added' % item_case['name'] in ret.data
        assert item_case['name'] in ret.data
        assert item_case['description'] in ret.data
        assert item_case['category_id'] in ret.data

    def test_delItem(self):
        '''add and then delete an item'''
        cat = catalog.Category(name="test_category")
        catalog.session.add(cat)
        item_case = {
            "name": "test_delItem",
            "description": "testdel description",
            "category_id": str(cat.id)}
        ret = self.createItem(item_case)
        assert '%s added' % item_case['name'] in ret.data
        # get item for id
        item = catalog.session.query(catalog.Item).filter_by(
            name=item_case['name']).one()
        ret = self.deleteItem(item.id)
        assert '%s deleted' % item_case['name'] in ret.data
        assert item_case['description'] not in ret.data
        assert item_case['category_id'] not in ret.data
        # check that second deletion fails
        ret = self.deleteItem(item.id)
        assert "Item not found" in ret.data

    def test_editItem(self):
        '''create and then edit a item'''
        # add two test categories
        cat = catalog.Category(name="test_category")
        catalog.session.add(cat)
        cat_two = catalog.Category(name="second")
        catalog.session.add(cat_two)
        # add a test item
        item_case = {
            "name": "test_item",
            "description": "test_description",
            "category_id": str(cat.id)}
        catalog.session.add(cat)
        ret = self.createItem(item_case)
        assert '%s added' % item_case['name'] in ret.data
        assert item_case['name'] in self.app.get('/item/').data
        # find the id for the item we added
        qret = catalog.session.query(catalog.Item).filter_by(
            name=item_case['name'])
        item = qret.one()

        item_case_two = {
            "name": "edited Item",
            "description": "edited description",
            "category_id": str(cat_two.id)}
        data = {}
        # generate form data using keys defined in model
        for i in item.asEditFormData():
            if i['editable']:
                data[i["db_name"]] = item_case_two[i["db_name"]]
            elif i['type'] == "hidden":
                data[i["name"]] = i["value"]

        # update by id
        ret = self.app.post(
            "/%s/%s/" % (item.uri_path, item.id),
            data=data,
            follow_redirects=True)
        assert '%s updated' % item_case_two['name'] in ret.data
        assert item_case_two['name'] in ret.data
        assert item_case_two['description'] in ret.data
        assert item_case_two['category_id'] in ret.data
        # check old item has been replaced
        assert item_case['name'] not in ret.data
        assert item_case['description'] not in ret.data
        assert item_case['category_id'] not in ret.data

if __name__ == '__main__':
    unittest.main()
