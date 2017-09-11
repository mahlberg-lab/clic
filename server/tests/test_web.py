import json
import unittest

import clic.web

class Test_stream_json(unittest.TestCase):
    def sj(self, gen):
        out = "\r".join(clic.web.stream_json(gen))
        json.loads(out) # Parse to validate
        return out

    def test_firstobject(self):
        """The first item has to be an object"""
        def fn():
            yield "poot"
            yield 1
            yield 2
            yield 3
        with self.assertRaisesRegexp(ValueError, '"poot"'):
            self.sj(fn())

    def test_allempty(self):
        """Returning no values results in an empty array"""
        def fn():
            yield {}
        self.assertEqual(self.sj(fn()), '{"data":[\r]}')

    def test_headerandempty(self):
        """Just a header works"""
        def fn():
            yield {"moo": "yes"}
        self.assertEqual(self.sj(fn()), '{"moo":"yes","data":[\r]}')

    def test_emptyheader(self):
        """An empty header doesn't trip us up"""
        def fn():
            yield {}
            yield 1
            yield 2
            yield 3
        self.assertEqual(self.sj(fn()), '{"data":[\r\n1\r,\n2\r,\n3\r]}')

    def test_headerresults(self):
        """All header items come before the results"""
        def fn():
            yield {"a":1,"b":2}
            yield 1
            yield 2
            yield 3
        self.assertEqual(self.sj(fn()), '{"a":1,"b":2,"data":[\r\n1\r,\n2\r,\n3\r]}')
