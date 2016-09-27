#!/usr/bin/env python
# -*- coding: utf-8 -*-
from celery_app import app
import os
import redis
import requests
import functools
import logging
import random
from config import *

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup


logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)


BaseUrl = "http://www.qisuu.com"


def proxy_config(host="127.0.0.1", port="6379", db=0):
    pool = redis.ConnectionPool(host=host, port=port, db=db)
    redis_conn = redis.StrictRedis(connection_pool=pool)
    key = "ipproxy:1"  # 暂时使用高匿名代理

    def handle_func(func):
        @functools.wraps(func)
        def handle_args(*args, **kwargs):
            return func(*args, **kwargs)

        return functools.partial(handle_args, redis_conn, key)

    return handle_func


@proxy_config(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
def getproxy(redis_conn, key, weight):
    # 根据权重随机获取代理ip, weight : [1...10]
    # 代理IP在redis中以zset存储, weight越大,ip质量越差
    total = redis_conn.zcard(key)
    ips = redis_conn.zrange(key, 0, total / 10 * weight)
    logging.info("ip numbers: %s", len(ips))
    #   获取全部代理IP
    #   ips = r.zrange(key, 0, -1)
    proxies = {
        "http": "http://%s" % ips[random.randint(0, len(ips) - 1)]
    }
    return proxies


def retry(max_retries=RETRY_TIMES, use_proxy=USE_PROXY):
    def handle_func(func):
        @functools.wraps(func)
        def handle_args(*args, **kwargs):
            try:
                retries = 0
                while True:
                    proxies = None
                    if use_proxy:
                        proxies = getproxy(retries + 1)
                        # logging.info(proxies)
                    try:
                        # kwargs['proxies'] = proxies
                        func(proxies=proxies, *args, **kwargs)
                        return True
                    except Exception as e:
                        print e
                    logging.error("fail! and %s retrying ", retries)
                    retries += 1
                    if retries > max_retries:
                        logging.error("fail too many times")
                        raise Exception
            except Exception as e:
                print e
        return handle_args

    return handle_func


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
                parse_book_url.delay(BaseUrl + url['value'])
            r.close()
            return BaseUrl + url['value']
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
                parse_book_info.delay(BaseUrl + b['href'])
            return BaseUrl + b['href']
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
            download_file.delay(book_info["download_url"])
            return book_info["download_url"]
        else:
            logging.error("Error: Unexpected response {}".format(r))
            raise
    except Exception as e:
        logging.error(e)
        parse_book_info.retry(args=[book_info_url, proxies, timeout, use_proxy, parse_book_info.request.retries + 1],
                              exc=e,kwargs=kwargs)
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
