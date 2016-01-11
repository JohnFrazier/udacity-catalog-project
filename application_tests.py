import unittest
from application import app, init_db
import application as catalog
from functools import update_wrapper
from StringIO import StringIO

test_image_name_1 = "placeholdit.png"
test_image_name_2 = "placeholdit2.png"


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
        app.config['WTF_CSRF_ENABLED'] = False
        app.debug = True
        app.secret_key = "something_secret"
        app.testing = True
        self.app = app.test_client()
        init_db('sqlite://')
        # login session
        query = dict(state='testingstate')
        self.app.post('/fbconnect', query_string=query, data='testytesttest')
        with open(test_image_name_1, 'r') as test_image:
            self.image_string = StringIO(test_image.read())
        with open(test_image_name_2, 'r') as test_image2:
            self.image2_string = StringIO(test_image2.read())
        del test_image
        del test_image2

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

    def createItem(self, form):
        return self.app.post(
            "/item/new/",
            data=form,
            follow_redirects=True)

    def deleteItem(self, id):
        form = dict(form_id='ItemDeleteForm')
        return self.app.post(
            "/item/%s/" % id,
            data=form,
            follow_redirects=True)

    def test_newItem(self):
        newform = dict(
            csrf="fake",
            form_id='ItemForm',
            name="test_Item",
            category="test_cat_pre_edit",
            description="test description",
            image=(self.image_string, 'test.png'))
        ret = self.createItem(newform)
        assert '%s added' % newform['name'] in ret.data
        assert '%s' % newform['image'][1] in ret.data
        assert newform['name'] in ret.data
        assert newform['category'] in ret.data
        assert newform['description'] in ret.data

        assert newform['name'] in self.app.get('/item/').data

    def test_delItem(self):
        '''add and then delete an item'''
        newform = dict(
            csrf="fake",
            form_id='ItemForm',
            name="test_delItem",
            category="test_delitem",
            description="test description",
            image=(self.image_string, 'test.png'))
        ret = self.createItem(newform)
        assert 'test_delItem added' in ret.data

        # fetch the item for the id
        item = catalog.session.query(catalog.Item).filter_by(
            name=newform['name']).one()
        assert item.name == newform['name']
        assert item.description == newform['description']
        assert item.category.name == newform['category']
        ret = self.deleteItem(item.id)
        if "rror" in ret.data:
            print ret
            print ret.data
        assert 'test_delItem deleted' in ret.data

    def test_editItem(self):
        '''create and then edit a item'''
        data_pre = dict(
            form_id='ItemForm',
            name="test_editItem_pre",
            category="test_cat_pre_edit",
            description="change comes quickly for me",
            image=(self.image_string, 'test.png'))

        data_post = dict(
            form_id='ItemEditForm',
            name="test_editedItem",
            category="test_cat_post_edit",
            description="changes",
            image=(self.image2_string, 'test2.png'))
        # add a test item
        ret = self.createItem(data_pre)
        # find the item id
        item = catalog.session.query(catalog.Item).filter_by(
            name=data_pre['name']).one()
        assert 'test_editItem_pre added' in ret.data
        assert 'test.png' in ret.data
        assert data_pre['name'] in ret.data
        assert data_pre['category'] in ret.data
        assert data_pre['description'] in ret.data

        # update by id
        ret = self.app.post(
            "/item/%s/" % item.id,
            data=data_post,
            follow_redirects=True)
        assert '%s updated' % data_post['name'] in ret.data
        assert 'test2.png' in ret.data
        assert 'test.png' not in ret.data
        assert data_post['name'] in ret.data
        assert data_post['category'] in ret.data
        assert data_post['description'] in ret.data
        assert data_pre['name'] not in ret.data
        assert data_pre['category'] not in ret.data
        assert data_pre['description'] not in ret.data


if __name__ == '__main__':
    unittest.main()
