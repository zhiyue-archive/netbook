# !/usr/bin/python
# -*- encoding:utf-8 -*-

import io
import logging
import os
import re

import chardet
import jieba
from gensim import similarities
from gensim.corpora import Dictionary
from gensim.corpora import MmCorpus

logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


def load_txt(filename, encoding='utf8'):
    encodings = ['gbk', 'gb2312', 'utf8', 'utf-8']
    with open(filename, 'r') as f:
        predict = chardet.detect(f.read(100))

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
        # label_names = os.listdir(txts_path)
        # file_paths = [os.path.join(txts_path, base_name) for base_name in label_names]
        # self.dictionary = Dictionary(TxtCorpus.processed_txt(file_path) for file_path in file_paths)
        self.dictionary = Dictionary()
        self.dir_path = txts_path
        self.label_names = os.listdir(txts_path)

    def __iter__(self):
        file_paths = [os.path.join(self.dir_path, base_name) for base_name in self.label_names]
        file_count = len(file_paths)
        for index_num, txt_path in enumerate(file_paths):
            logging.info("%i/%i,%s", index_num, file_count, txt_path)
            doc = self.dictionary.doc2bow(TxtCorpus.processed_txt(txt_path), allow_update=True)
            yield doc

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

    def save_labels(self, path):
        with open(path, 'w') as fw:
            for line in self.label_names:
                fw.write(line + '\n')

    @staticmethod
    def load_labels(path):
        labels = list()
        with open(path, 'r') as f:
            for line in f.readlines():
                labels.append(line.strip())
        return labels


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


def save(corpus, save_path):
    dict_path = os.path.join(save_path, 'corpus.dict')
    mm_path = os.path.join(save_path, 'corpus.mm')
    labels_path = os.path.join(save_path, 'corpus.labels')
    MmCorpus.serialize(mm_path, corpus)
    corpus.save_labels(labels_path)
    corpus.dictionary.save(dict_path)

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
    # corpus_memory_friendly = TxtCorpus('txt/')
    # save(corpus_memory_friendly, 'data')

    # corpus_memory_friendly.load('tmp')
    # corpus = [v for v in tqdm.tqdm(corpus_memory_friendly)]
    # MmCorpus.serialize('tmp/test_corpus.mm', corpus)
    # corpus_memory_friendly.save_labels('tmp/test_corpus.labels')
    # corpus_memory_friendly.dictionary.save('tmp/test_corpus.dict')

    # dictionary = Dictionary.load('tmp/test_corpus.dict')
    # corpus = MmCorpus('tmp/test_corpus.mm')
    # labels = TxtCorpus.load_labels('tmp/test_corpus.labels')
    #
    # logging.info("init corpus.mm")
    # corpus, dictionary, labels = load('data')
    # logging.info("init tfidf model")
    # tfidf = models.TfidfModel(dictionary=dictionary)
    # logging.info("trans corpus to tfidf")
    # corpus_tfidf = tfidf[corpus]
    # logging.info("saving tfidf corpus.")
    # MmCorpus.serialize("data/corpus_tfidf.mm", corpus)
    # logging.info("build similarities_index")
    # similarities_index = similarities.Similarity('data/similarities_index', corpus_tfidf, num_features=len(dictionary), num_best=20)
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

            # corpus = MmCorpus('data/corpus.mm')

            # for doc in corpus_tfidf:
            #     print doc

            # txt = TxtCorpus.processed_txt('tests/txt/23080.txt')
            # print txt
