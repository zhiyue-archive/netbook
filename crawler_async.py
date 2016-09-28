#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
import os
import cPickle as pickle
from  tasks import parse_category_url, download_file
from config import REDIS_PORT, REDIS_DB, REDIS_HOST, DUPLICATION_KEY
import redis
from utils import sha1

__author__ = 'zhiyue'
__copyright__ = "Copyright 2016"
__credits__ = ["zhiyue"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "zhiyue"
__email__ = "cszhiyue@gmail.com"
__status__ = "Production"


def check_update():
    # todo check category index update ststus
    pass


def sync_redis_repeat_books(dir_path):
    # todo update already download books to redis repeat check
    have = set(os.listdir(dir_path))
    pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    r = redis.StrictRedis(connection_pool=pool)
    pipe = r.pipeline()
    for file_name in have:
        hash_value = sha1(file_name)
        pipe.sadd(DUPLICATION_KEY, hash_value)
    pipe.execute()

# download_file.delay("http://dzs.qisuu.com/txt/26.txt")

if __name__ == '__main__':
    # classify_infos = pickle.load(open("classify_infos.p", "rb"))
    #
    # for k, v in classify_infos.items():
    #     print "add %s, %s" % (k, v)
    #     parse_category_url.delay(v, category_type=k)
    sync_redis_repeat_books('txt')
