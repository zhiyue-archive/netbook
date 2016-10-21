#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
import argparse
import logging
from gensim.corpora import Dictionary
from gensim.corpora import MmCorpus
from preprocessing import TxtCorpus
import os
from gensim import corpora, models, similarities
from gensim.similarities import Similarity
from sqlalchemy import create_engine
from sqlalchemy.pool import SingletonThreadPool
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from src.spider.config import DB_URI, BOOK_INFO_INDEX_PER_PAGE_NUM
from src.models import NetBook, Category, Recommend

__author__ = 'zhiyue'
__copyright__ = "Copyright 2016"
__credits__ = ["zhiyue"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "zhiyue"
__email__ = "cszhiyue@gmail.com"
__status__ = "Production"

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

engine = create_engine(DB_URI, poolclass=SingletonThreadPool, pool_size=20)
session_factory = sessionmaker(bind=engine)




class TxtSimilar(object):
    def __init__(self, save_path):
        self.corpus, self.dictionary, self.labels, self.tfidf = TxtSimilar._load(save_path)
        self.similarities_index = dict()
        self.register_models = dict()

    @staticmethod
    def build_index(index_path, corpus, num_features, model, num_best=21):
        corpus_vec = model[corpus]
        similarities_index = similarities.Similarity(index_path, corpus_vec,
                                                     num_features=num_features,
                                                     num_best=num_best)
        return similarities_index

    def register_similariti_indexs(self, model_name, indexs):
        self.similarities_index[model_name] = indexs

    def update_index_to_db(self, model_name):
        Session = scoped_session(session_factory)
        session = Session()
        for doc_index, similarities in enumerate(self.similarities_index[model_name]):

            similarities = sorted(similarities, key=lambda item: -item[1])[1:]
            file_name = self.labels[doc_index]
            book_info = session.query(NetBook).filter(NetBook.file_name == file_name).first()
            range_index = 1
            for sim_index, sim in similarities:
                similar_book_info = session.query(NetBook).filter(NetBook.file_name == self.labels[sim_index]).first()
                recommend_record = dict()
                recommend_record['name'] = book_info.name
                recommend_record['author'] = book_info.author
                recommend_record["file_name"] = book_info.file_name
                recommend_record['similar_book_name'] = similar_book_info.name
                recommend_record['similar_file_name'] = similar_book_info.file_name
                recommend_record['similar_book_author'] = similar_book_info.author
                recommend_record['similar_book_wordcount'] = similar_book_info.word_count
                recommend_record['similarity'] = sim
                recommend_record['model'] = model_name
                recommend_record['range'] = range_index
                range_index += 1

                new_recommend = Recommend(**recommend_record)
                session.merge(new_recommend)
                session.commit()
        Session.remove()

    def register_model(self, model_name, model):
        self.register_models[model_name] = model

    @staticmethod
    def init_model(model, **kwargs):
        return model(**kwargs)

    def save_model(self, model_name, path):
        self.register_models[model_name].save(path)

    def load_model(self, model_name, model_type, path):
        model = model_type.load(path)
        self.register_models[model_name] = model

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
        tfidf_module = os.path.join(save_path, 'tfidf.model')
        corpus = MmCorpus(mm_path)
        dictionary = Dictionary.load(dict_path)
        labels = TxtCorpus.load_labels(labels_path)
        if os.path.isfile(tfidf_module):
            return corpus, dictionary, labels, TxtSimilar.load_tfidf_module(tfidf_module)
        else:
            return corpus, dictionary, labels, models.TfidfModel(dictionary=dictionary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", "-s", help="The path to the tfidf corpus")
    parser.add_argument("--destination", "-d", help="The path to store the index")
    args = parser.parse_args()
    corpus_dir = args.source
    index_dir = args.destination
    if not os.path.isdir(corpus_dir):
        os.mkdir(corpus_dir)
    if not os.path.isdir(index_dir):
        os.mkdir(index_dir)
    #index_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "data", "index"))
    tfidf_index_path = os.path.join(index_dir, "tfidf_index")
    logging.info("init TxtSimilar")
    txt_similar = TxtSimilar(corpus_dir)
    logging.info("init model.")
    tfidf_model = TxtSimilar.init_model(models.TfidfModel, dictionary=txt_similar.dictionary)
    logging.info("register model to models.")
    txt_similar.register_model('tfidf', tfidf_model)
    tfidf_similar_indexs = TxtSimilar.build_index(tfidf_index_path, txt_similar.corpus, len(txt_similar.dictionary), model=tfidf_model)
    logging.info("register index to similarity indexs.")
    txt_similar.register_similariti_indexs('tfidf', tfidf_similar_indexs)
    logging.info("update index to database...")
    txt_similar.update_index_to_db('tfidf')

    # txt_similar.update_index_to_db()
