import unittest
from application import app
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
        self.app = app.test_client()
        self.app.testing = True
        # TODO initialize test db

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


paths = ['/', '/login', '/logout', '/category/']
paths.extend(build_crud_paths('item', 1))


class TestPathMeta(type):

    "metaclass to simplify path testing method generation"

    def __new__(cls, parent, bases, d):
        "override __new__ to generate multiple class methods on import"
        def buildTest(path):

            def testPath(self):
                'test that all get paths can be reached.'
                result = self.app.get(path)
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


if __name__ == '__main__':
    unittest.main()
