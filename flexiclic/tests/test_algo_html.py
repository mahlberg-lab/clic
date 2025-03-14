import configparser
import io
import unittest
import warnings

from flexiclic import FlexiClic


class TestAlgoHtml(unittest.TestCase):
    maxDiff = None

    def test_from_schema_all_algos(self):
        # Write all algo HTML to a configparser file
        fc = FlexiClic(api_root="https://clic.bham.ac.uk", available_spacy_models=["en_core_web_sm", "en_core_web_md", "en_core_web_lg"])
        actual = configparser.ConfigParser()
        for algo_class, algos in fc.algorithms_by_class().items():
            for a in sorted(algos, key = lambda x: x['name']):
                actual['DEFAULT'][a['name']] = "\n" + "\n".join(fc.algorithm_render_html(algo_name=a['name'], prefix="algprefix"))
        with open("tests/test_algo_html.baseline.new", "w", encoding="utf-8") as f:
            actual.write(f)

        # Read in both versions (NB: Re-reading as whitespace isn't preserved)
        actual = configparser.ConfigParser()
        actual.read("tests/test_algo_html.baseline.new")
        expected = configparser.ConfigParser()
        expected.read("tests/test_algo_html.baseline")

        self.assertEqual(
            sorted(list(actual['DEFAULT'].keys())),
            sorted(list(expected['DEFAULT'].keys())),
        )
        for k in actual['DEFAULT'].keys():
            for l in actual['DEFAULT'][k].split("\n"):
                if "border: 1px solid red" in l:
                    warnings.warn(l)
            self.assertEqual(
                actual['DEFAULT'][k],
                expected['DEFAULT'][k],
                k,
            )
