# !/usr/bin/python
# -*- encoding:utf-8 -*-

import argparse
import io
import logging
import os
import re

import chardet
import jieba
from gensim import similarities
from gensim.corpora import Dictionary
from gensim.corpora import MmCorpus
from gensim.models import tfidfmodel


logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


def filter_stop_words(cut_word_list, stop_words):
    """Filter stop words

    :param cut_word_list: a list of words
    :param stop_words: a list of stop_words
    :return: a list of Filtered words
    """
    seg_list = [w for w in cut_word_list if w not in stop_words and w != " "]
    return seg_list


def load_stop_words(filename):
    """ load dictionary file.

    :param filename: The path to the dictionary file
    :return: a list of stop words
    """
    with open(filename, 'r') as f:
        stop_words = set()
        for line in f.readlines():
            stop_words.add(line.decode('utf-8').strip())
        return stop_words


def iter_documents(top_directory):
    """Iterate over all documents, yielding a document (=list of utf8 tokens) at a time."""
    file_list = filter(lambda file_name: file_name.endswith('.txt'), os.listdir(top_directory))
    file_num = len(file_list)
    for index, file_name in enumerate(file_list):
            logging.info("dict init %i/%i: %s", index, file_num, file_name)
            yield TxtCorpus.processed_txt(os.path.join(top_directory, file_name))


class TxtCorpus(object):

    stop_words = load_stop_words(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                              os.pardir, "data", "dict", "all_stopword.txt")))

    def __init__(self, path, use_mm=False):
        logging.info("init dict...")
        self.dictionary = Dictionary(iter_documents(path))
        self.dictionary.filter_extremes(no_below=1, no_above=0.5, keep_n=1000000)
        self.dictionary.compactify()
        logging.info("finish init dict.")
        print self.dictionary
        self.dir_path = path
        if not use_mm:
            self.label_names = filter(lambda file_name: file_name.endswith('.txt'), os.listdir(path)) # Filter non-txt suffix files
        else:
            self.label_names = TxtCorpus.load_labels(os.path.join(path, 'corpus.labels'))
        self.use_mm = use_mm

    def __iter__(self):
        file_paths = [os.path.join(self.dir_path, base_name) for base_name in self.label_names]
        file_count = len(file_paths)
        if self.use_mm:
                corpus, self.dictionary, self.label_names = TxtCorpus.load(self.dir_path)
                for index_num, doc in enumerate(corpus):
                    logging.info("%i/%i,%s", index_num, file_count, self.label_names[index_num])
                    yield doc
        else:
            for index_num, txt_path in enumerate(file_paths):
                logging.info("%i/%i,%s", index_num, file_count, txt_path)
                doc = self.dictionary.doc2bow(TxtCorpus.processed_txt(txt_path))
                yield doc

    def save_labels(self, path):
        with open(path, 'w') as fw:
            for line in self.label_names:
                fw.write(line + '\n')

    def serialize(self, path):
        TxtCorpus.save(self, path)

    @staticmethod
    def load_txt(filename, encoding='utf8'):
        encodings = ['gbk', 'gb2312', 'utf8', 'utf-8', 'UTF-8-SIG']
        with open(filename, 'r') as f:
            predict = chardet.detect(f.read(100))
        print predict['encoding']
        if predict['encoding'] not in encodings:
            encoding = 'gbk'
        else:
            encoding = predict['encoding']
        try:
            with io.open(filename, 'r', encoding=encoding, errors='ignore') as f:
                text = re.sub(ur'\W+', ' ', f.read(), flags=re.U)
                return ''.join(text)
        except UnicodeDecodeError:
            logging.warn("parse %s use %s fail", filename, encoding)
            raise UnicodeDecodeError

    @staticmethod
    def processed_txt(filename):
        content = TxtCorpus.load_txt(filename)
        words = TxtCorpus.cut_txt_content(content)
        segments = filter_stop_words(words, TxtCorpus.stop_words)
        return segments

    @staticmethod
    def load_stop_words(filename):
        with open(filename, 'r') as f:
            stop_words = set()
            for line in f.readlines():
                stop_words.add(line.decode('utf-8').strip())
            return stop_words

    @staticmethod
    def load_labels(path):
        labels = list()
        with open(path, 'r') as f:
            for line in f.readlines():
                labels.append(line.strip())
        return labels

    @staticmethod
    def save(corpus, save_path):
        dict_path = os.path.join(save_path, 'corpus.dict')
        mm_path = os.path.join(save_path, 'corpus.mm')
        labels_path = os.path.join(save_path, 'corpus.labels')
        MmCorpus.serialize(mm_path, corpus)
        corpus.save_labels(labels_path)
        corpus.dictionary.save(dict_path)

    @staticmethod
    def load(save_path):
        dict_path = os.path.join(save_path, 'corpus.dict')
        mm_path = os.path.join(save_path, 'corpus.mm')
        labels_path = os.path.join(save_path, 'corpus.labels')
        logging.info("loading corpus")
        corpus = MmCorpus(mm_path)
        logging.info("loading dictionary")
        dictionary = Dictionary.load(dict_path)
        logging.info("loading labels")
        labels = TxtCorpus.load_labels(labels_path)
        return corpus, dictionary, labels

    @staticmethod
    def cut_txt_content(content):
        """Chinese word segmentation
        :param content:Chinese text content
        :return: a list of segments
        """
        return jieba.cut(content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", "-s", help="The path to the file")
    parser.add_argument("--destination", "-d", help="The path to store the result")
    args = parser.parse_args()
    data_dir = args.source
    save_dir = args.destination
    if not os.path.isdir(data_dir):
        os.mkdir(data_dir)
    if not os.path.isdir(save_dir):
        os.mkdir(save_dir)

    #test_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "tests", "test_data"))
    mm_corpus_path = os.path.join(save_dir)
    corpus_memory_friendly = TxtCorpus(data_dir)
    TxtCorpus.save(corpus_memory_friendly, mm_corpus_path)
    logging.info("init corpus.mm")
    corpus, dictionary, labels = TxtCorpus.load(mm_corpus_path)
    logging.info("init tfidf model")
    tfidf = tfidfmodel.TfidfModel(dictionary=dictionary)
    logging.info("trans corpus to tfidf")
    corpus_tfidf = tfidf[corpus]
    logging.info("saving tfidf corpus.")
    MmCorpus.serialize(os.path.join(mm_corpus_path, "mm_corpus.tfidf"), corpus_tfidf)



