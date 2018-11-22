import json
import unittest

from clic.stream_json import stream_json
from clic.errors import UserError


class Test_stream_json(unittest.TestCase):
    def sj(self, gen, header={}):
        sj_gen = stream_json(gen, header)
        assert(next(sj_gen) is None)
        out = "\r".join(sj_gen)
        json.loads(out)  # Parse to validate
        return out

    def test_header(self):
        """The header has to be an object"""
        def fn():
            yield 1
            yield 2
            yield 3
        with self.assertRaisesRegex(ValueError, '"poot"'):
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
        self.assertEqual(
            self.sj(fn(), {"moo": "yes"}),
            '{"moo":"yes","data":[\r\n]}'
        )

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
        self.assertEqual(
            self.sj(fn(), {"a": 1, "b": 2}),
            '{"a":1,"b":2,"data":[\r\n1\r,\n2\r,\n3\r\n]}'
        )

    def test_initialerror(self):
        """Initial errors are thrown upwards to be handled"""
        def fn():
            raise ValueError("Erk")
            yield 1
            yield 2
            yield 3

        with self.assertRaisesRegex(ValueError, "Erk"):
            json.loads(self.sj(fn(), {"a": 1, "b": 2}))

    def test_intermediateerror(self):
        """Intermediate errors are caught and written out"""
        def fn():
            yield 1
            yield 2
            raise ValueError("Erk")
            yield 3

        out = json.loads(self.sj(fn(), {"a": 1, "b": 2}))
        self.assertEqual(out['data'], [1, 2])  # NB: Got some of the data
        self.assertEqual(out['error'], dict(
            message="ValueError: Erk",
            stack=out['error']['stack'],
        ))
        self.assertIn("ValueError: Erk", out['error']['stack'])

    def test_usererror(self):
        """User errors can prettify the error message"""
        def fn():
            yield 1
            yield 2
            raise UserError("Potato!", "info")

        out = json.loads(self.sj(fn(), {"a": 1, "b": 2}))
        self.assertEqual(out['data'], [1, 2])
        self.assertEqual(out['info'], dict(
            message="Potato!",
            stack=None,
        ))

    def test_footer(self):
        """We can return custom footer data"""
        def fn(max_data):
            for x in range(max_data):
                yield x
            yield ('footer', dict(bottom='yes'))

        out = json.loads(self.sj(fn(2), {"a": 1, "b": 2}))
        self.assertEqual(out, dict(
            a=1,
            b=2,
            bottom='yes',
            data=[0, 1],
        ))

        out = json.loads(self.sj(fn(1), {"a": 1, "b": 2}))
        self.assertEqual(out, dict(
            a=1,
            b=2,
            bottom='yes',
            data=[0],
        ))

        out = json.loads(self.sj(fn(0), {"a": 1, "b": 2}))
        self.assertEqual(out, dict(
            a=1,
            b=2,
            bottom='yes',
            data=[],
        ))
