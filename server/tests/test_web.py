import json
import unittest

import clic.web

class Test_stream_json(unittest.TestCase):
    def sj(self, gen, header={}):
        out = "\r".join(clic.web.stream_json(gen, header))
        json.loads(out) # Parse to validate
        return out

    def test_header(self):
        """The header has to be an object"""
        def fn():
            yield 1
            yield 2
            yield 3
        with self.assertRaisesRegexp(ValueError, '"poot"'):
            self.sj(fn(), "poot")

    def test_allempty(self):
        """Returning no values results in an empty array"""
        def fn():
            return iter(())
        self.assertEqual(self.sj(fn()), '{"data":[\r\n]}')

    def test_headerandempty(self):
        """Just a header works"""
        def fn():
            return iter(())
        self.assertEqual(self.sj(fn(), {"moo": "yes"}), '{"moo":"yes","data":[\r\n]}')

    def test_emptyheader(self):
        """An empty header doesn't trip us up"""
        def fn():
            yield 1
            yield 2
            yield 3
        self.assertEqual(self.sj(fn(), {}), '{"data":[\r\n1\r,\n2\r,\n3\r\n]}')

    def test_headerresults(self):
        """All header items come before the results"""
        def fn():
            yield 1
            yield 2
            yield 3
        self.assertEqual(self.sj(fn(), {"a":1,"b":2}), '{"a":1,"b":2,"data":[\r\n1\r,\n2\r,\n3\r\n]}')
