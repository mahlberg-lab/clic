import unittest

from flexiclic import errors, path_util


class TestTypesFromString(unittest.TestCase):
    def test_convert_arg(self):
        """
        Make sure we can convert strings into the appropriate type demanded by schema
        """
        def conv(val, type_spec, required=False):
            """
            convert (val) into something matching (type_spec) by building dummy algorithm and validating
            """
            out, annotations = path_util.normalize([
                dict(
                    algorithm_name="testing_algo",
                    test_param=val,
                )
            ], dict(testing_algo=dict(
                full_name="Testing algorithm",
                algorithm_type="selection",
                args_schema=dict(
                    required=["test_param"] if required else [],
                    properties=dict(test_param=type_spec),
                    
                ),
            )))
            self.assertEqual(annotations, [])
            self.assertEqual(len(out), 1)
            self.assertEqual(out[0]["algorithm_name"], "testing_algo")
            self.assertEqual(list(out[0]["args"].keys()), ["test_param"])
            return out[0]["args"]["test_param"]

        # None not allowed if required=True
        with self.assertRaises(errors.UserError):
            conv(None, dict(type="integer"), required=True)

        # Integer conversions
        self.assertEqual(conv("44", dict(type="integer")), 44)
        self.assertEqual(conv("45", dict(type=["integer"])), 45)
        self.assertEqual(conv(None, dict(type="integer")), None)
        self.assertEqual(conv(None, dict(type="integer", default=99)), 99)
        with self.assertRaisesRegex(errors.UserError, "Cannot convert.*frank.*integer"):
            conv("frank", dict(type="integer"))

        # Boolean conversions
        self.assertEqual(conv("on", dict(type="boolean")), True)
        self.assertEqual(conv("", dict(type="boolean")), False)
        self.assertEqual(conv(None, dict(type="boolean")), False)

        # Integer / number fallback
        self.assertEqual(conv("45", dict(type=["integer", "number"])), int(45))
        self.assertEqual(conv("44.9", dict(type=["integer", "number"])), float(44.9))
        self.assertEqual(conv("45", dict(type=["string", "integer"])), "45")  # String got there first

        # Arrays of type
        self.assertEqual(conv(["1", "2", "3"], dict(type=["array"])), ["1", "2", "3"])
        self.assertEqual(conv(["1", "2", "3"], dict(type=["array"], items=dict(type="integer"))), [1, 2, 3])
        with self.assertRaisesRegex(errors.UserError, "Cannot convert.*gelda.*array"):
            self.assertEqual(conv("gelda", dict(type=["array"])), ["1", "2", "3"])
