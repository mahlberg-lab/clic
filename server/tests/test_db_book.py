from clic.concordance import concordance
from clic.undefined import ClicDb


class Skip_get_book_metadata():  # TODO: Skip the lot
    def test_bookmetadata(self):
        """We can request book titles"""
        cdb = ClicDb()

        out = [x for x in concordance(
            cdb,
            corpora=['AgnesG', 'TTC'],
            subset=['quote'],
            q=[u'she was'],
            contextsize=[0],
            metadata=['book_titles'],
        )]
        self.assertEqual(out[-1], ('footer', dict(book_titles=dict(
            AgnesG=(u'Agnes Grey', u'Anne Bront\xeb'),
            TTC=(u'A Tale of Two Cities', u'Charles Dickens'),
        ))))

        # chapter_start can also be got
        out = [x for x in concordance(
            cdb,
            corpora=['AgnesG', 'TTC'],
            subset=['quote'],
            q=[u'she was'],
            contextsize=[0],
            metadata=['book_titles', 'chapter_start'],
        )]
        self.assertEqual(out[-1], ('footer', dict(book_titles=dict(
            AgnesG=(u'Agnes Grey', u'Anne Bront\xeb'),
            TTC=(u'A Tale of Two Cities', u'Charles Dickens'),
        ), chapter_start=dict(
            AgnesG={
                1: 0, 2: 4424, 3: 7130, 4: 11363, 5: 14529, 6: 16855, 7: 18933, 8: 24573, 9: 25458, 10: 26959,
                11: 28722, 12: 34349, 13: 35799, 14: 38319, 15: 43312, 16: 45815, 17: 47159, 18: 50967, 19: 54240,
                20: 55417, 21: 57388, 22: 59672, 23: 62600, 24: 64042, 25: 66188,
                '_end': 68197,
            },
            TTC={
                1: 0, 2: 1005, 3: 3023, 4: 4643, 5: 9055, 6: 13228, 7: 17372, 8: 19771, 9: 22159,
                10: 27022, 11: 29272, 12: 31407, 13: 35983, 14: 39315, 15: 41164, 16: 45238, 17: 48204, 18: 49600, 19: 52171,
                20: 54012, 21: 57905, 22: 62130, 23: 66001, 24: 67910, 25: 70325, 26: 73113, 27: 74462, 28: 78726, 29: 80762,
                30: 83390, 31: 87821, 32: 92057, 33: 94547, 34: 96274, 35: 98413, 36: 100694, 37: 103196, 38: 105044, 39: 109720,
                40: 114373, 41: 120167, 42: 121625, 43: 124833, 44: 129234, 45: 133871,
                '_end': 136100,
            }
        ))))

        # word_count
        out = [x for x in concordance(
            cdb,
            corpora=['AgnesG', 'TTC'],
            subset=['quote'],
            q=[u'she was'],
            contextsize=[0],
            metadata=['word_count_all', 'word_count_quote'],
        )]
        self.assertEqual(out[-1], ('footer', dict(
            word_count_all=dict(AgnesG=68197, TTC=136100),
            word_count_quote=dict(AgnesG=21986, TTC=48557),
        )))

    def test_querybyauthor(self):
        cdb = ClicDb()

        out = [x for x in concordance(
            cdb,
            corpora=['author:Jane Austen'],
            subset=['quote'],
            q=[u'she was', u'she said'],
            contextsize=[0],
        )]
        self.assertEqual(
            set([x[1][0] for x in out[1:]]),
            set([u'emma', u'ladysusan', u'mansfield', u'northanger', u'persuasion', u'pride', u'sense']),
        )
