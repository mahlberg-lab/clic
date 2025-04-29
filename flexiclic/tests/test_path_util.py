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
            out, requires = path_util.normalize([
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
            self.assertEqual(len(out), 1)
            self.assertEqual(out[0]["algorithm_name"], "testing_algo")
            if len(out[0]["args"]) == 0:
                return None
            self.assertEqual(list(out[0]["args"].keys()), ["test_param"])
            out = out[0]["args"]["test_param"]
            self.assertTrue(out is not None)
            return out

        # None not allowed if required=True
        with self.assertRaises(errors.UserError):
            conv(None, dict(type="integer"), required=True)

        # String conversions
        self.assertEqual(conv("44", dict(type="string")), "44")
        self.assertEqual(conv("", dict(type="string")), "")
        self.assertEqual(conv(None, dict(type="string")), None)
        self.assertEqual(conv("44", dict(type="string", default="Fred")), "44")
        self.assertEqual(conv("", dict(type="string", default="Fred")), "")
        self.assertEqual(conv(None, dict(type="string", default="Fred")), "Fred")

        # Integer conversions
        self.assertEqual(conv("44", dict(type="integer")), 44)
        self.assertEqual(conv("45", dict(type=["integer"])), 45)
        self.assertEqual(conv(None, dict(type="integer")), None)
        self.assertEqual(conv(None, dict(type="integer", default=99)), 99)
        self.assertEqual(conv("", dict(type="integer")), None)
        self.assertEqual(conv("", dict(type="integer", default=99)), 99)
        with self.assertRaisesRegex(errors.UserError, "Cannot convert.*frank.*integer"):
            conv("frank", dict(type="integer"))

        # Boolean conversions
        self.assertEqual(conv("on", dict(type="boolean")), True)
        self.assertEqual(conv("", dict(type="boolean")), False)
        self.assertEqual(conv(None, dict(type="boolean")), False)
        # NB: default=True ignored,
        self.assertEqual(conv("on", dict(type="boolean", default=True)), True)
        self.assertEqual(conv("", dict(type="boolean", default=True)), False)
        self.assertEqual(conv(None, dict(type="boolean", default=True)), False)

        # Integer / number fallback
        self.assertEqual(conv("45", dict(type=["integer", "number"])), int(45))
        self.assertEqual(conv("44.9", dict(type=["integer", "number"])), float(44.9))
        self.assertEqual(conv("", dict(type=["integer", "number"], default=123.89)), float(123.89))
        self.assertEqual(conv("45", dict(type=["string", "integer"])), "45")  # String got there first

        # Arrays of type
        self.assertEqual(conv(["1", "2", "3"], dict(type=["array"])), ["1", "2", "3"])
        # NB: Default never applied, we don't know if user provided None or []
        self.assertEqual(conv(["1", "2", "3"], dict(type=["array"], default=["4", "5"])), ["1", "2", "3"])
        self.assertEqual(conv([], dict(type=["array"], default=["4", "5"])), [])
        self.assertEqual(conv(None, dict(type=["array"], default=["4", "5"])), [])
        self.assertEqual(conv(["1", "2", "3"], dict(type=["array"], items=dict(type="integer"))), [1, 2, 3])
        self.assertEqual(conv(4, dict(type=["array"], items=dict(type="integer"))), [4])
        self.assertEqual(conv("[5,6,7]", dict(type=["array"])), ["5", "6", "7"])
        with self.assertRaisesRegex(errors.UserError, "Cannot convert.*gelda.*integer"):
            conv("gelda", dict(type=["array"], items=dict(type="integer")))
        with self.assertRaisesRegex(errors.UserError, "Cannot convert.*gelda.*integer"):
            conv("gelda", dict(type=["array"], items=dict(type="integer")))

    def test_requires(self):
        """
        Make sure we can fetch requirements from a schema
        """
        out, requires = path_util.normalize([
            dict(
                algorithm_name="testing_algo",
                test_param="arg",
            )
        ], dict(testing_algo=dict(
            full_name="Testing algorithm",
            algorithm_type="selection",
            requires=["pyicu"],
            args_schema=dict(properties={},required=[]),
        )))
        self.assertEqual(requires, ["pyicu"])

        # A spacy model is appended to requirements
        out, requires = path_util.normalize([
            dict(
                algorithm_name="testing_algo",
                test_param="arg",
                spacy_model="en_core_web_lg",
            )
        ], dict(testing_algo=dict(
            full_name="Testing algorithm",
            algorithm_type="selection",
            requires=["spacy>=99"],
            args_schema=dict(properties={
                "spacy_model": dict(type="string"),
            },required=[]),
        )))
        self.assertEqual(requires, ["spacy>=99", "en_core_web_lg"])

        out, requires = path_util.normalize([
            dict(
                algorithm_name="testing_algo",
                test_param="arg",
            )
        ], dict(testing_algo=dict(
            full_name="Testing algorithm",
            algorithm_type="selection",
            args_schema=dict(properties={},required=[]),
        )))
        self.assertEqual(requires, [])

    def test_normalise_grouping(self):
        """
        Normalisation of multiple grouping algorithms isn't allowed
        """
        with self.assertRaisesRegex(errors.UserError, "arrangement node"):
            out, requires = path_util.normalize([
                dict(
                    algorithm_name="grouping_algo",
                ),
                dict(
                    algorithm_name="grouping_algo",
                ),
            ], dict(grouping_algo=dict(
                full_name="Group",
                algorithm_type="partitioning",
                requires=[],
                args_schema=dict(properties={},required=[]),
            )))

    def test_normalise_source(self):
        opts, annotations, requires = path_util.normalize_source(dict(
            q="elbow",
        ), [
            dict(
                algorithm_name="Annotate with Sentence Transformers",
            ),
        ], {
            "Annotate with Sentence Transformers": dict(
                full_name="Annotate with Sentence Transformers",
                algorithm_type="annotation",
                requires=[],
                server_side_prefix="st_",
                args_schema=dict(properties={
                    "model_name": {"type": "string", "default": "all-MiniLM-L6-v2"},
                },required=[]),
            ),
        })
        # Annotation included onto API url
        self.assertEqual(opts, {
            'q': 'elbow',
            'st_model_name': 'all-MiniLM-L6-v2',
        })
        # No client-side annotations
        self.assertEqual(annotations, [])
        self.assertEqual(requires, [])
