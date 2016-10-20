#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
import logging
from gensim.corpora import Dictionary
from gensim.corpora import MmCorpus
from preprocessing import TxtCorpus
import os
from gensim import corpora, models, similarities

__author__ = 'zhiyue'
__copyright__ = "Copyright 2016"
__credits__ = ["zhiyue"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "zhiyue"
__email__ = "cszhiyue@gmail.com"
__status__ = "Production"

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


class TxtSimilar(object):
    def __init__(self, save_path, index_path='index/netbook', num_best=20):
        self.corpus, self.dictionary, self.labels, self.tfidf = TxtSimilar._load(save_path)
        if len(os.listdir(index_path)) > 0:
            self.similarities_index = TxtSimilar.load_index(index_path)
        else:
            self.similarities_index = self.build_index(index_path, self.corpus, len(self.dictionary), num_best)

    def build_index(self, index_path, corpus, num_features, num_best):
        corpus_tfidf = self.tfidf[corpus]
        similarities_index = similarities.Similarity(index_path, corpus_tfidf,
                                                     num_features=num_features,
                                                     num_best=num_best)
        return similarities_index

    @staticmethod
    def load_index(path):
        return similarities.Similarity.load(path)

    def query(self, doc):
        pass

    def save_module(self, path):
        self.tfidf.save(path)

    @staticmethod
    def load_tfidf_module(path):
        return models.TfidfModel.load(path)

    @staticmethod
    def _load(save_path):
        dict_path = os.path.join(save_path, 'corpus.dict')
        mm_path = os.path.join(save_path, 'corpus.mm')
        labels_path = os.path.join(save_path, 'corpus.labels')
        tfidf_module = os.path.join(save_path, 'corpus.tfidf')
        corpus = MmCorpus(mm_path)
        dictionary = Dictionary.load(dict_path)
        labels = TxtCorpus.load_labels(labels_path)
        if os.path.isfile(tfidf_module):
            return corpus, dictionary, labels, TxtSimilar.load_tfidf_module(tfidf_module)
        else:
            return corpus, dictionary, labels, models.TfidfModel(dictionary=dictionary)


if __name__ == '__main__':
    similarities_index = similarities.Similarity.load('data/similarities_index.0')
    similarities_index.num_best = 20
    labels = TxtCorpus.load_labels('data/corpus.labels')
    with open("txt_index.txt", 'w') as fw:
        for doc_index, similarities in enumerate(similarities_index):
            similarities = sorted(similarities, key=lambda item: -item[1])[1:]
            # print "similar to doc: %s" % labels[doc_index]
            logging.info("%s / %s", doc_index, len(labels))
            fw.write("similar to doc: %s" % labels[doc_index] + "\n")
            for sim_index, sim in similarities:
                # print labels[sim_index], str(round(sim*100, 3))+'%'
                fw.write(labels[sim_index] + "," + str(round(sim * 100, 3)) + '% ' + "\n")
            fw.write("\n")
            fw.flush()