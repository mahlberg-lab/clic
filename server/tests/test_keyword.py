import unittest
import pytest
import pandas as pd

from clic.keyword import keyword, log_likelihood, extract_keywords


class LogLikelihoodBasicTest(unittest.TestCase):
    '''
    Reference values calculated using http://ucrel.lancs.ac.uk/llwizard.html

    For the formula, cf.

    Rayson, P. and Garside, R. (2000). Comparing corpora using frequency profiling
    In proceedings of the workshop on Comparing Corpora, held in conjunction with the 38th
    annual meeting of the Association for Computational Linguistics (ACL 2000).
    1-8 October 2000, Hong Kong, pp. 1 - 6
    Available at: http://ucrel.lancs.ac.uk/people/paul/publications/rg_acl2000.pdf
    '''

    def setUp(self):
        self.data = pd.DataFrame([('hand', 540, 116000, 7525, 5451382),
                                  ('hands', 227, 116000, 3635, 5451382),
                                  ('forehead', 29, 116000, 504, 5451382),
                                  ('head', 431, 116000, 5892, 5451382),
                                  ('neck', 16, 116000, 650, 5451382),
                                  ],
                                 columns=('Type',
                                          'Count_analysis',
                                          'Total_analysis',
                                          'Count_ref',
                                          'Total_ref'))
        self.LLR = log_likelihood(self.data)

    def test_hand(self):
        hand = round(self.LLR.loc[self.LLR.Type == 'hand', 'LL'], 2)
        self.assertEqual(hand.values[0], 534.64)

    def test_hands(self):
        hands = round(self.LLR.loc[self.LLR.Type == 'hands', 'LL'], 2)
        self.assertEqual(hands.values[0], 183.53)

    def test_forehead(self):
        forehead = round(self.LLR.loc[self.LLR.Type == 'forehead', 'LL'], 2)
        self.assertEqual(forehead.values[0], 20.50)

    def test_head(self):
        head = round(self.LLR.loc[self.LLR.Type == 'head', 'LL'], 2)
        self.assertEqual(head.values[0], 437.88)

    def test_neck(self):
        neck = round(self.LLR.loc[self.LLR.Type == 'neck', 'LL'], 2)
        self.assertEqual(neck.values[0], 0.32)


class LogLikelihoodZeroes(unittest.TestCase):
    '''
    Reference values calculated using http://ucrel.lancs.ac.uk/llwizard.html
    '''

    def setUp(self):
        self.data = pd.DataFrame([('zero', 540, 116000, 0, 5451382),
                                  ('zero_two', 7, 10000, 0, 100000),
                                  ('zero_three', 0, 10000, 536, 100000),
                                  ],
                                 columns=('Type',
                                          'Count_analysis',
                                          'Total_analysis',
                                          'Count_ref',
                                          'Total_ref'))
        self.LLR = log_likelihood(self.data)

    @pytest.mark.filterwarnings('ignore:divide by zero')
    def test_zero(self):
        zero = round(self.LLR.loc[self.LLR.Type == 'zero', 'LL'], 2)
        self.assertEqual(zero.values[0], 4180.78)

    @pytest.mark.filterwarnings('ignore:divide by zero')
    def test_zero_two(self):
        zero_two = round(self.LLR.loc[self.LLR.Type == 'zero_two', 'LL'], 2)
        self.assertEqual(zero_two.values[0], 33.57)

    @pytest.mark.filterwarnings('ignore:divide by zero')
    def test_zero_three(self):
        '''
        The case where the count or expected count in the corpus of analysis is zero
        is not handled by the keywords module. NaN != 102.16
        '''
        zero_three = round(
            self.LLR.loc[self.LLR.Type == 'zero_three', 'LL'], 2)
        self.assertNotEqual(zero_three.values[0], 102.16)


class LogLikelihoodSameValues(unittest.TestCase):
    '''
    Reference values calculated using http://ucrel.lancs.ac.uk/llwizard.html
    '''

    def setUp(self):
        self.data = pd.DataFrame([('zero', 10, 150, 10, 150),
                                  ],
                                 columns=('Type',
                                          'Count_analysis',
                                          'Total_analysis',
                                          'Count_ref',
                                          'Total_ref'))
        self.LLR = log_likelihood(self.data)

    def test_same_values(self):
        same_values = round(self.LLR.loc[self.LLR.Type == 'zero', 'LL'], 2)
        self.assertEqual(same_values.values[0], 0)


class KeywordExtraction(unittest.TestCase):
    '''
    Tests the filtering of the keyword results. Does not test the algorithm.
    '''

    def setUp(self):
        self.analysis = pd.DataFrame([('one', 540),
                                      ('two', 2),
                                      ('three', 29),
                                      ('four', 431),
                                      ('five', 16),
                                      ],
                                     columns=('Type',
                                              'Count'))
        self.reference = pd.DataFrame([('one', 540),
                                       ('two', 227),
                                       ('three', 29),
                                       ('four', 431),
                                       ('SIX', 16),
                                       ],
                                      columns=('Type',
                                               'Count'))

    @pytest.mark.filterwarnings('ignore:divide by zero')
    def test_wordlist_merging(self):
        keywords = extract_keywords(self.analysis,
                                    self.reference,
                                    1000,
                                    10000)
        # the default p_value is 0.0001
        self.assertEqual(len(keywords), 4)
        self.assertIn('five', keywords.Type.tolist())
        self.assertNotIn('SIX', keywords.Type.tolist())
        self.assertEqual(keywords.Count_analysis[0], 540)
        # five does not occur in ref
        self.assertEqual(keywords.Count_ref[3], 0)

    @pytest.mark.filterwarnings('ignore:divide by zero')
    def test_limit_rows(self):
        keywords2 = extract_keywords(self.analysis,
                                     self.reference,
                                     1000,
                                     10000,
                                     limit_rows=2)
        self.assertEqual(len(keywords2), 2)

    @pytest.mark.filterwarnings('ignore:divide by zero')
    def test_p_value(self):
        keywords3 = extract_keywords(self.analysis,
                                     self.reference,
                                     1000,
                                     10000,
                                     p_value=0.0001)
        # there are only 4 keywords
        self.assertEqual(len(keywords3), 4)

    @pytest.mark.filterwarnings('ignore:divide by zero')
    def test_frequency_cutoff(self):
        keywords4 = extract_keywords(self.analysis,
                                     self.reference,
                                     1000,
                                     10000,
                                     freq_cut_off=30)
        self.assertEqual(len(keywords4), 2)

    @pytest.mark.filterwarnings('ignore:divide by zero')
    def test_exclude_underused(self):
        '''
        Expected work:

        Type  Count_analysis  Total_analysis  Count_ref  Total_ref  \
        0    one             540            1000        540        100
        2   four             431            1000        431        100
        1  three              29            1000         29        100

           Expected_count_analysis  Expected_count_ref       LL Use           p
        0                   981.82               98.18  1195.46   -  p < 0.0001
        2                   783.64               78.36   954.16   -  p < 0.0001
        1                    52.73                5.27    64.20   -  p < 0.0001
        '''
        keywords5 = extract_keywords(self.analysis,
                                     self.reference,
                                     1000,
                                     100,
                                     p_value=0.05,
                                     exclude_underused=False)
        self.assertEqual(len(keywords5), 3)

    @pytest.mark.filterwarnings('ignore:divide by zero')
    def test_round_values(self):
        keywords6 = extract_keywords(self.analysis,
                                     self.reference,
                                     1000,
                                     10000,
                                     round_values=False)
        # value = 1195.463979
        value = keywords6.loc[0, 'LL']
        nr_of_decimals = len(str(value).split('.')[1])
        self.assertNotEqual(nr_of_decimals, 2)
