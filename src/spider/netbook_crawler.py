#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
import os
import cPickle as pickle
from tasks import parse_category_url, tasks_schedule, parse_book_url
from config import REDIS_PORT, REDIS_DB, REDIS_HOST, DUPLICATION_KEY
from ..utils import set_batch_repeate, del_batch_hash_value_in_redis_repeate_set
from sqlalchemy import create_engine
from sqlalchemy.pool import SingletonThreadPool
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from config import DB_URI, BOOK_INFO_INDEX_PER_PAGE_NUM
from ..database import NetBook, Category
import redis
import requests
import logging

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

__author__ = 'zhiyue'
__copyright__ = "Copyright 2016"
__credits__ = ["zhiyue"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "zhiyue"
__email__ = "cszhiyue@gmail.com"
__status__ = "Production"

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

engine = create_engine(DB_URI, poolclass=SingletonThreadPool, pool_size=20)
session_factory = sessionmaker(bind=engine)
pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)


class NetBookCrawler(object):
    def __init__(self):
        pass


def check_update():
    # todo check category index update ststus
    classify_infos = pickle.load(open("classify_infos.p", "rb"))
    category_book_count = dict()
    Session = scoped_session(session_factory)
    session = Session()
    retries = 10
    for k, v in classify_infos.items():
        print "add %s, %s" % (k, v)
        while retries < 10:
            try:
                r = requests.get(v, timeout=30)
                r.encoding = "utf-8"
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "lxml")
                    category_book_new_count = int(soup.select(".tspage")[0]
                                                  .text.split(u"首页")[0].split(u"总数")[-1].strip())
                    old_record = session.query(Category).filter(Category.name == k).first()
                    count_diff = category_book_new_count - old_record.count
                    old_record.count = category_book_count
                    session.commit()
                    Session.remove()
                    if count_diff > 0:
                        page_diff = (count_diff / BOOK_INFO_INDEX_PER_PAGE_NUM) + 1
                        increment_crawl(v, page_diff, k)
            except:
                pass
            finally:
                retries += 1


def increment_crawl(base_url, page_num, category):
    crawl_book_index_url = list()
    crawl_book_index_url.append(base_url)
    for i in xrange(1, page_num):
        crawl_book_index_url.append("%s/index_%s.html" % (base_url, i))
    for i in crawl_book_index_url:
        parse_book_url.delay(i, category_type=category)


def sync_redis_repeat_download_books(dir_path):
    """synchronization between the hash list on redis and the book list under the dir_path path

    :param dir_path: The path to the directory where the books have been downloaded
    """
    have = set(os.listdir(dir_path))
    r = redis.StrictRedis(connection_pool=pool)
    set_batch_repeate(r, have, DUPLICATION_KEY)


def sync_redis_repeat_books_info_urls():
    """
    This method implements the redis on the hash table and the database
    as been resolved in the book details page url synchronization
    """
    r = redis.StrictRedis(connection_pool=pool)
    Session = scoped_session(session_factory)
    session = Session()
    books_info_urls = [netbook.info_url for netbook in
                       session.query(NetBook).filter(NetBook.download_url != None).all()]
    session.commit()
    Session.remove()
    set_batch_repeate(r, books_info_urls, DUPLICATION_KEY)


def sync_db_book_detail():
    """
    1. Redis Synchronizes with the info_url collection of the full record of the book table in the database.
    2. update the missing data in the book table for detail information, Such as title, author, download address
    """
    pass


def sync_book_download_status(dir_path):
    have = set(os.listdir(dir_path))

    Session = scoped_session(session_factory)
    session = Session()

    # update db download status
    # todo db add a column describe the file where the machine is stored
    for record in session.query(NetBook).all():
        if record.file_name in have:
            record.download_flag = True
        else:
            record.download_flag = False
    session.flush()
    session.commit()

    r = redis.StrictRedis(connection_pool=pool)
    download_urls = [record.download_url for record in
                     session.query(NetBook).filter(NetBook.download_flag == True).all()]
    set_batch_repeate(r, download_urls, DUPLICATION_KEY)
    not_download_records = session.query(NetBook).filter(NetBook.download_flag == False).all()

    # update redis repeat set .
    not_download_record_filename_set = [record.file_name for record in not_download_records if record.file_name]
    not_download_records_download_url_set = [record.download_url for record in not_download_records if
                                             record.download_url]
    del_batch_hash_value_in_redis_repeate_set(r, not_download_record_filename_set, DUPLICATION_KEY)
    del_batch_hash_value_in_redis_repeate_set(r, not_download_records_download_url_set, DUPLICATION_KEY)

    Session.remove()

    # download_records = session.query(NetBook).filter(
    #     NetBook.file_name.in_(have)).all()  # cause error: too many SQL variables
    # not_download_records = session.query(NetBook).filter(
    #     ~NetBook.file_name.in_(have)).all()  # cause error: too many SQL variables
    # for record in download_records:
    #     record.download_flag = True
    # for record in not_download_records:
    #     record.download_flag = False


def update_db_missing_book_detail():
    """
    update the missing data in the book table for detail information, Such as title, author, download address
    """
    r = redis.StrictRedis(connection_pool=pool)
    Session = scoped_session(session_factory)
    session = Session()

    incomplete_book_info_url_list = [netbook.info_url for netbook in
                                     session.query(NetBook).filter(NetBook.download_url == None).all()]
    del_batch_hash_value_in_redis_repeate_set(r, incomplete_book_info_url_list, DUPLICATION_KEY)
    for info_url in incomplete_book_info_url_list:
        tasks_schedule.delay(task_url=info_url, task_type="parse_book_info")
    logging.info("add %s parse_book_info tasks", len(incomplete_book_info_url_list))
    session.commit()
    Session.remove()


def download_fail_download_books():
    r = redis.StrictRedis(connection_pool=pool)
    Session = scoped_session(session_factory)
    session = Session()

    not_download_records = session.query(NetBook).filter(NetBook.download_flag == False).all()

    # update redis repeat set .
    not_download_record_filename_set = [record.file_name for record in not_download_records if record.file_name]
    not_download_records_download_url_set = [record.download_url for record in not_download_records if
                                             record.download_url]
    del_batch_hash_value_in_redis_repeate_set(r, not_download_record_filename_set, DUPLICATION_KEY)
    del_batch_hash_value_in_redis_repeate_set(r, not_download_records_download_url_set, DUPLICATION_KEY)

    for record in not_download_records_download_url_set:
        tasks_schedule.delay(task_url=record, task_type="download_file", file_name=record.split('/')[-1])
    session.commit()
    Session.remove()


# download_file.delay("http://dzs.qisuu.com/txt/26.txt")

if __name__ == '__main__':
    # todo: add paramerers to run
    # sync_redis_repeat_books_info_urls()
    sync_book_download_status(u'txt')
    sync_redis_repeat_download_books(u"txt")
    download_fail_download_books()
    update_db_missing_book_detail()

    # sync_redis_repeat_download_books('txt')
    # sync_redis_repeat_books_info_urls()
    # check_update()
    # classify_infos = pickle.load(open("classify_infos.p", "rb"))
    # for k, v in classify_infos.items():
    #     print "add %s, %s" % (k, v)
    #     parse_category_url.delay(v, category_type=k)
