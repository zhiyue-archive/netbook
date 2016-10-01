# !/usr/bin/python
# -*- encoding:utf-8 -*-

import os
import io
import re
import jieba
import re
import logging
from gensim.corpora import Dictionary
from gensim.corpora import MmCorpus
import tqdm
from gensim import corpora, models, similarities

logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


def load_txt(filename, type_index=0):
    encodings = {0: 'utf8', 1: 'GBK', 2: 'gb2312'}
    if type_index > 2:
        logging.error("%s error open.", filename)
        raise UnicodeDecodeError
    encoding = encodings[type_index]
    text = ''
    try:
        with io.open(filename, 'r', encoding=encoding, errors='ignore') as f:
            # lines = [line.strip() for line in f.readlines()]
            # text = ' '.join(lines)
            text = re.sub(ur'\W+', ' ', f.read(), flags=re.U)
            # print 'utf-8'
    except UnicodeDecodeError:
        logging.warn("parse %s use %s fail", filename, encoding)
        load_txt(filename, type_index + 1)


    return ''.join(text)


def load_stop_words(filename):
    with open(filename, 'r') as f:
        stop_words = set()
        for line in f.readlines():
            stop_words.add(line.decode('utf-8').strip())
        return stop_words


def get_seg_list(cut_word_list, stop_words):
    seg_list = [w for w in cut_word_list if w not in stop_words and w != " "]
    return seg_list


# def load_txt(x):
#     with open(x) as f:
#         res = [t.decode('gbk', 'ignore') for t in f]
#         return ''.join(res)


def cut_words(content):
    return jieba.cut(content)


class TxtCorpus(object):

    stop_words = load_stop_words('dict/all_stopword.txt')

    def __init__(self, txts_path):
        self.dictionary = Dictionary()
        self.dir_path = txts_path
        self.label_names = os.listdir(self.dir_path)

    def __iter__(self):
        file_paths = [os.path.join(self.dir_path, base_name) for base_name in self.label_names]
        for txt_path in file_paths:
            logging.info(txt_path)
            yield self.dictionary.doc2bow(TxtCorpus.processed_txt(txt_path), allow_update=True)

    @staticmethod
    def processed_txt(filename):
        content = load_txt(filename)
        words = cut_words(content)
        segments = get_seg_list(words, TxtCorpus.stop_words)
        return segments

    @staticmethod
    def load_stop_words(filename):
        with open(filename, 'r') as f:
            stop_words = set()
            for line in f.readlines():
                stop_words.add(line.decode('utf-8').strip())
            return stop_words


if __name__ == '__main__':
    # visible_chars = re.sub(r'\s+', '', text, flags=re.UNICODE)
    # print len(visible_chars)

    # content = load_txt('16308.txt')
    # words = cut_words(content)
    # stop_words = load_stop_words('dict/all_stopword.txt')
    # segments = get_seg_list(words, stop_words)

    # for word in words:
    #     print word
    #
    # for word in segments:
    #     print word
    # corpus_memory_friendly = TxtCorpus('tests/txt/')
    # corpus = [v for v in tqdm.tqdm(corpus_memory_friendly)]
    # MmCorpus.serialize('tmp/test_corpus.mm', corpus, corpus_memory_friendly.label_names)
    # corpus_memory_friendly.dictionary.save('tmp/test_corpus.dict')

    dictionary = Dictionary.load('tmp/test_corpus.dict')
    corpus = MmCorpus('tmp/test_corpus.mm')
    tfidf = models.TfidfModel(dictionary=dictionary)
    corpus_tfidf = tfidf[corpus]
    for doc in corpus_tfidf:
        print doc


    similarities.Similarity
