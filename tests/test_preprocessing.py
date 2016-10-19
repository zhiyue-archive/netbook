#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
import os
from src.preprocessing import TxtCorpus
import unittest

__author__ = 'zhiyue'
__copyright__ = "Copyright 2016"
__credits__ = ["zhiyue"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "zhiyue"
__email__ = "cszhiyue@gmail.com"
__status__ = "Production"


test_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),  "test_data"))


class TestTxtCorpus(unittest.TestCase):

    def setUp(self):
        txt_dir = os.path.join(test_data_dir, "small")
        mm_dir = os.path.join(test_data_dir, "corpus_mm")
        self.txt_corpus = TxtCorpus(txt_dir, use_mm=False)
        self.mm_corpus = TxtCorpus(mm_dir, use_mm=True)


    def test_stop_words(self):
        stop_words = TxtCorpus.stop_words
        print "num of stop_words: %s" % len(stop_words)
        self.assertGreater(len(stop_words), 0)

    def test_load_stop_words(self):
        stop_word_path = os.path.join(test_data_dir, "dict", "all_stopword.txt")
        stop_words = TxtCorpus.load_stop_words(stop_word_path)
        self.assertEqual(len(stop_words), 2442)

    def test_save(self):
        pass

    def test_txtcorpus_load_from_txts(self):
        pass

    def test_txtcorpus_load_from_mmcorpus(self):
        pass

    def tearDown(self):
        self.widget.dispose()


if __name__ == '__main__':
    unittest.main()
