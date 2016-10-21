#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from contextlib import contextmanager
import tempfile
import os
import cPickle as pickle
import shutil
import requests
import logging
import random
import functools
import redis
import hashlib
import chardet
from src.spider.config import REDIS_HOST, REDIS_PORT, REDIS_DB
from types import StringType
import re
import io

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


# Context managers for atomic writes courtesy of
# http://stackoverflow.com/questions/2333872/atomic-writing-to-file-with-python
@contextmanager
def _tempfile(*args, **kws):
    """ Context for temporary file.

    Will find a free temporary filename upon entering
    and will try to delete the file on leaving

    Parameters
    ----------
    suffix : string
        optional file suffix
    """

    fd, name = tempfile.mkstemp(*args, **kws)
    os.close(fd)
    try:
        yield name
    finally:
        try:
            os.remove(name)
        except OSError as e:
            if e.errno == 2:
                pass
            else:
                raise e


@contextmanager
def open_atomic(filepath, *args, **kwargs):
    """ Open temporary file object that atomically moves to destination upon
    exiting.

    Allows reading and writing to and from the same filename.

    Parameters
    ----------
    filepath : string
        the file path to be opened
    fsync : bool
        whether to force write the file to disk
    kwargs : mixed
        Any valid keyword arguments for :code:`open`
    """
    fsync = kwargs.pop('fsync', False)

    with _tempfile(dir=os.path.dirname(filepath)) as tmppath:
        with open(tmppath, *args, **kwargs) as f:
            yield f
            if fsync:
                f.flush()
                os.fsync(file.fileno())
                #        os.rename(tmppath, filepath)
        shutil.move(tmppath, filepath)


def safe_pickle_dump(obj, fname):
    with open_atomic(fname, 'wb') as f:
        pickle.dump(obj, f, -1)


def download_file(url, local_filename=None, proxies=None):
    if not local_filename:
        local_filename = url.split('/')[-1]
    try:
        r = requests.get(url, proxies=proxies, stream=True)
        if r.status_code == 200:
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=4096):
                    if chunk:
                        f.write(chunk)
                logging.info("Finish download %s", url)
        else:
            logging.error("Error: Unexpected response {}".format(r))
            raise Exception("Unexpected response.")

    except requests.exceptions.RequestException as e:
        logging.error("Error: {}".format(e))
        raise
    except Exception as e:
        logging.error(e)
        raise


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


def redis_init(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB):
    pool = redis.ConnectionPool(host=host, port=port, db=db)
    redis_conn = redis.StrictRedis(connection_pool=pool)
    return pool, redis_conn


def sha1(x):
    sha1obj = hashlib.sha1()
    sha1obj.update(x)
    hash_value = sha1obj.hexdigest()
    return hash_value


def check_repeate(r, check_str, set_name):
    """
    redis集合检查元素，重复则返回0，不重复则添加成功，并返回1

    :param r:redis连接
    :param check_str:被添加的字符串
    :param set_name:项目所使用的集合名称，建议如下格式：”projectname:task_remove_repeate“
    :return:
        :rtype: bool
            0: 不重复
            1: 重复
    """
    check_str = check_str.encode('utf-8', 'ignore')
    hash_value = sha1(check_str)
    # result = r.sadd(set_name, hash_value)
    result = r.sismember(set_name, hash_value)
    return result


def set_repeate(r, check_str, set_name):
    """
    向redis集合中添加元素，重复则返回0，不重复则添加成功，并返回1

    :param r:redis连接
    :param check_str:被添加的字符串
    :param set_name:项目所使用的集合名称，建议如下格式：”projectname:task_remove_repeate“
    :return:
        :rtype: bool
            0: 重复
            1: 不重复
    """
    check_str = check_str.encode('utf-8', 'ignore')
    hash_value = sha1(check_str)
    result = r.sadd(set_name, hash_value)
    return result


def del_hash_value_in_repeate_set(r, del_str, set_name):
    """
    删除redis集合中的元素
    :param r:
    :param del_str:
    :param set_name:
    :return:
    """
    del_str = del_str.encode('utf-8', 'ignore')
    hash_value = sha1(del_str)
    result = r.srem(set_name, hash_value)
    return result


def del_batch_hash_value_in_redis_repeate_set(r, del_str_list, set_name):
    # del_str_list = map(str.encode, del_str_list)
    # del_str_list = [s.encode('utf-8') for s in del_str_list]
    # sha1_list = map(sha1, del_str_list)
    # r.srem(set_name, *set(sha1_list))

    pipe = r.pipeline()
    for file_name in del_str_list:
        file_name = file_name.encode('utf-8', 'ignore')
        hash_value = sha1(file_name)
        pipe.srem(set_name, hash_value)
    pipe.execute()


def set_batch_repeate(r, check_str_list, set_name):
    # check_str_list = [s.encode('utf-8') for s in check_str_list]
    # sha1_list = map(sha1, check_str_list)
    # r.sadd(set_name, *set(sha1_list))
    pipe = r.pipeline()
    for file_name in check_str_list:
        file_name = file_name.encode('utf-8', 'ignore')
        hash_value = sha1(file_name)
        pipe.sadd(set_name, hash_value)
    pipe.execute()


def caculateWords(s, encoding='utf-8'):
    rx = re.compile(u"[a-zA-Z0-9_\u0392-\u03c9]+|[\u4E00-\u9FFF\u3400-\u4dbf\uf900-\ufaff\u3040-\u309f\uac00-\ud7af]+",
                    re.UNICODE)
    if type(s) is StringType:  # not unicode
        s = unicode(s, encoding, 'ignore')

    splitted = rx.findall(s)
    cjk_len = 0
    asc_len = 0
    for w in splitted:
        if ord(w[0]) >= 12352:  # \u3040
            cjk_len += len(w)
        else:
            asc_len += 1
    return (cjk_len, asc_len)


def get_txt_chars(file_path):
    predict = chardet.detect(open(file_path, 'r').read(100))['encoding']
    with io.open(file_path, 'r', encoding=predict, errors='ignore') as fr:
        content = fr.read()
        visible_chars = re.sub(r'\s+', '', content, flags=re.UNICODE)
        print len(visible_chars)
        return len(visible_chars)


if __name__ == '__main__':
    download_file(u"http://dzs.qisuu.com/txt/我的农场在沙漠.txt")