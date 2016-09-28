#!/usr/bin/env python
# -*- coding: utf-8 -*-
from celery_app import app
import os
import requests
import logging
import random
from config import *
from utils import getproxy, check_repeate, set_repeate
from sqlalchemy import Column, String, create_engine, Integer, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import SingletonThreadPool
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from config import DB_URI
from database import NetBook
import redis

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup


logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

engine = create_engine(DB_URI, poolclass=SingletonThreadPool, pool_size=20)
session_factory = sessionmaker(bind=engine)

# dumplite
pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
redis_conn = redis.StrictRedis(connection_pool=pool)


@app.task(retries=10, default_retry_delay=5)
def parse_category_url(classify_index_url, proxies=None, timeout=DOWNLOAD_TIMEOUT,
                       use_proxy=USE_PROXY, retries=0, **kwargs):
    try:
        if use_proxy:
            proxies = getproxy(retries + 1)
            logging.info("Retry: %s and Proxy: %s and url: %s", retries, proxies, classify_index_url)
        r = requests.get(classify_index_url, proxies=proxies, timeout=timeout, **kwargs)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "lxml")
            classify_urls = soup.select(".tspage select option")
            for url in classify_urls:
                parse_book_url.delay(BaseUrl + url['value'], **kwargs)
            r.close()
            return "Finish parse classify_index_url: %s" % classify_index_url
        else:
            logging.error("Error: Unexpected response {}".format(r))
            raise
    except Exception as e:
        logging.error(e)
        parse_category_url.retry(args=[classify_index_url, proxies, timeout, use_proxy,
                                       parse_category_url.request.retries + 1],
                                 exc=e,
                                 countdown=int(random.uniform(2, 4) ** parse_category_url.request.retries),
                                 kwargs=kwargs)
    return True


@app.task(retries=10, default_retry_delay=5)
def parse_book_url(category_url, proxies=None, timeout=DOWNLOAD_TIMEOUT, use_proxy=USE_PROXY, retries=0, **kwargs):
    try:
        if use_proxy:
            proxies = getproxy(retries + 1)
            logging.info("Retry: %s and Proxy: %s and url: %s", retries, proxies, category_url)
        r = requests.get(category_url, proxies=proxies, timeout=timeout, **kwargs)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "lxml")
            for b in soup.select(".listBox > ul li > a"):
                tasks_schedule.delay(url=BaseUrl + b['href'], **kwargs)
                # parse_book_info.delay(BaseUrl + b['href'])
            return "Finish parse category_url: %s" % category_url
        else:
            logging.error("Error: Unexpected response {}".format(r))
            raise
    except Exception as e:
        logging.error(e)
        parse_book_url.retry(args=[category_url, proxies, timeout, use_proxy, parse_book_url.request.retries + 1],
                             exc=e, kwargs=kwargs)
    return True


@app.task(retries=10, default_retry_delay=5)
def parse_book_info(book_info_url, proxies=None, timeout=DOWNLOAD_TIMEOUT, use_proxy=USE_PROXY, retries=0, **kwargs):
    try:
        if use_proxy:
            proxies = getproxy(retries + 1)
            logging.info("Retry: %s and Proxy: %s and url: %s", retries, proxies, book_info_url)
        r = requests.get(book_info_url, proxies=proxies, timeout=timeout, **kwargs)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "lxml")
            book_info = dict()
            book_info["name"] = soup.select(".showDown ul li")[1].a["href"].split("/")[-1].split(".")[0]
            book_info["author"] = soup.select(".detail .detail_right ul li")[6].a.string
            book_info["rate"] = filter(str.isdigit, soup.select(".detail .detail_right ul li")[7].em["class"][0])
            book_info["download_url"] = soup.select(".showDown ul li")[1].a["href"]
            book_info['file_name'] = book_info["download_url"].split('/')[-1]
            book_info['info_url'] = book_info_url
            # update kwargs
            kwargs = dict(kwargs, **book_info)
            tasks_schedule.delay(task_url=book_info["download_url"], task_type="download_file", **kwargs)
            tasks_schedule.delay(task_url=book_info_url, task_type="set_repeate", **kwargs)
            # download_file.delay(book_info["download_url"])
            return book_info["download_url"]
        else:
            logging.error("Error: Unexpected response {}".format(r))
            raise
    except Exception as e:
        logging.error(e)
        parse_book_info.retry(args=[book_info_url, proxies, timeout, use_proxy, parse_book_info.request.retries + 1],
                              exc=e, kwargs=kwargs)
    return True


@app.task(retries=10, default_retry_delay=5)
def download_file(url, local_filename=None, proxies=None, timeout=DOWNLOAD_TIMEOUT, use_proxy=USE_PROXY, retries=0,
                  **kwargs):
    if not local_filename:
        local_filename = url.split('/')[-1]
        fname = os.path.join("txt", local_filename)
    else:
        fname = local_filename
    try:
        if use_proxy:
            proxies = getproxy(retries + 1)
            logging.info("Retry: %s and Proxy: %s and url: %s", retries, proxies, url)
        r = requests.get(url, proxies=proxies, stream=True, timeout=timeout, **kwargs)
        if r.status_code == 200:
            with open(fname, 'wb') as f:
                for chunk in r.iter_content(chunk_size=4096):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                logging.info("Finish download %s", url)
                tasks_schedule.delay(task_url=url, task_type="set_repeate", **kwargs)
                r.close()
                return True
        else:
            logging.error("Error: Unexpected response {}".format(r))
            raise
    except Exception as e:
        logging.error(e)
        download_file.retry(args=[url, fname, proxies, timeout,
                                  use_proxy, download_file.request.retries + 1],
                            exc=e, kwargs=kwargs)
    return True


@app.task(retries=10, default_retry_delay=5)
def tasks_schedule(task_url, task_type, **kwargs):
    """

    :param task_url:
    :param task_type:
    :param kwargs:
    :return:
    """

    Session = scoped_session(session_factory)
    session = Session()
    query = session.query(NetBook)
    r = redis.StrictRedis(connection_pool=pool)
    # 检查是否已经存在这个url，重复则not_repeat=0
    not_repeat = check_repeate(r, task_url, DUPLICATION_KEY)
    if not not_repeat:  # 重复则代表该任务已经完成, 直接返回
        return
    if task_type == 'parse_book_info':
        parse_book_info.delay(task_url, **kwargs)
        query.filter_by(info_url=task_url).update({'info_url': task_url, 'category_type': kwargs['category_type']})
    elif task_type == 'download_file':
        if not check_repeate(r, kwargs['file_name'], DUPLICATION_KEY):
            download_file.delay(task_url, **kwargs)
        else:
            set_repeate(r, kwargs['download_url'], DUPLICATION_KEY)

        query.filter_by(info_url=kwargs['info_url']).update({'name': kwargs['name'], 'info_url': kwargs['info_url'],
                                                             'file_name': kwargs['file_name'],
                                                             'author': kwargs['author'], 'rate': kwargs['rate'],
                                                             'download_url': kwargs['download_url']})
    elif task_type == 'set_repeate':
        set_repeate(r, task_url, DUPLICATION_KEY)
    session.commit()
    Session.remove()
    return False
