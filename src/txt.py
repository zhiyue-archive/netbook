#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
import io
import chardet
import re
import os
import jieba
import jieba.analyse
__author__ = 'zhiyue'
__copyright__ = "Copyright 2016"
__credits__ = ["zhiyue"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "zhiyue"
__email__ = "cszhiyue@gmail.com"
__status__ = "Production"


class Txt(object):

    def __init__(self, path):
        self.file_path = path
        self.file_name = os.path.basename(path)
        self.encoding = chardet.detect(open(path, 'r').read(100))['encoding']
        with io.open(path, 'r', encoding=self.encoding, errors='ignore') as fr:
            self.content = fr.read()
        self.tags = Txt.extract_tags(self.content)
        self.word_count = Txt.get_txt_chars(self.content)

    @staticmethod
    def get_txt_chars(content):
        visible_chars = re.sub(r'\s+', '', content, flags=re.UNICODE)
        print len(visible_chars)
        return len(visible_chars)

    @staticmethod
    def extract_tags(content, topk=10):
        return jieba.analyse.extract_tags(content, topK=topk,allowPOS=('ns', 'n', 'vn', 'v'))

    def __str__(self):
        tags_str = u"/".join(self.tags)
        return u"filename:%s,encoding:%s,word_count:%s,tags:%s" % (self.file_name, self.encoding, self.word_count, tags_str)



if __name__ == '__main__':
    txt = Txt(r"E:\repos\workspace\netbook\tests\test_data\small_txt\21891.txt")
    print txt
