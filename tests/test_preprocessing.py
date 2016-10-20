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
        txt_dir = os.path.join(test_data_dir, "small_txt")
        mm_dir = os.path.join(test_data_dir, "corpus_mm")
        self.txt_corpus = TxtCorpus(txt_dir, use_mm=False)
        self.mm_corpus = TxtCorpus(mm_dir, use_mm=True)

    def test_load_stop_words(self):
        stop_word_path = os.path.join(test_data_dir, "dict", "all_stopword.txt")
        stop_words = TxtCorpus.load_stop_words(stop_word_path)
        self.assertEqual(len(stop_words), 2442)
        stop_words = TxtCorpus.stop_words
        self.assertEqual(len(stop_words), 2442)

    def test_save_labels(self):
        save_path = os.path.join(test_data_dir, "corpus.labels")
        self.txt_corpus.save_labels(save_path)
        file_flag = os.path.isfile(save_path)
        self.assertTrue(file_flag)
        os.remove(save_path)
        self.assertFalse(os.path.isfile(save_path))

        self.mm_corpus.save_labels(save_path)
        self.assertTrue(os.path.isfile(save_path))
        os.remove(save_path)
        self.assertFalse(os.path.isfile(save_path))

    def test_save(self):
        print "test_save"
        save_path = test_data_dir
        dict_path = os.path.join(save_path, 'corpus.dict')
        mm_path = os.path.join(save_path, 'corpus.mm')
        mm_index_path = os.path.join(save_path, 'corpus.mm.index')
        labels_path = os.path.join(save_path, 'corpus.labels')

        TxtCorpus.save(self.txt_corpus, save_path)
        self.assertTrue(os.path.isfile(dict_path))
        self.assertTrue(os.path.isfile(mm_path))
        self.assertTrue(os.path.isfile(labels_path))
        os.remove(dict_path)
        os.remove(mm_path)
        os.remove(mm_index_path)
        os.remove(labels_path)

        TxtCorpus.save(self.mm_corpus, save_path)
        self.assertTrue(os.path.isfile(dict_path))
        self.assertTrue(os.path.isfile(mm_path))
        self.assertTrue(os.path.isfile(labels_path))
        os.remove(dict_path)
        os.remove(mm_path)
        os.remove(mm_index_path)
        os.remove(labels_path)

    def test_serialize(self):
        print "test_serialize"
        save_path = test_data_dir
        dict_path = os.path.join(save_path, 'corpus.dict')
        mm_path = os.path.join(save_path, 'corpus.mm')
        mm_index_path = os.path.join(save_path, 'corpus.mm.index')
        labels_path = os.path.join(save_path, 'corpus.labels')

        self.txt_corpus.serialize(save_path)
        self.assertTrue(os.path.isfile(dict_path))
        self.assertTrue(os.path.isfile(mm_path))
        self.assertTrue(os.path.isfile(labels_path))
        os.remove(dict_path)
        os.remove(mm_path)
        os.remove(mm_index_path)
        os.remove(labels_path)

        self.mm_corpus.serialize(save_path)
        self.assertTrue(os.path.isfile(dict_path))
        self.assertTrue(os.path.isfile(mm_path))
        self.assertTrue(os.path.isfile(labels_path))
        os.remove(dict_path)
        os.remove(mm_path)
        os.remove(mm_index_path)
        os.remove(labels_path)

    def test_mm_iter(self):
        for index, doc in enumerate(self.mm_corpus):
            print doc

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
