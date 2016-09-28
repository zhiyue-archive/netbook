# -*- coding: utf-8 -*-
from kombu import Exchange, Queue
__author__ = 'zhiyue'

# crawler info
BaseUrl = "http://www.qisuu.com"
DUPLICATION_KEY = 'netbook:task_remove_repeate'


# dowdload proxy config
USE_PROXY = True
PROXY_KEY = "ipproxy:1"
DOWNLOAD_TIMEOUT = 20
RETRY_TIMES = 10
REDIS_HOST = "192.168.1.48"
REDIS_PORT = "6379"
REDIS_DB = 0

# db config
DB_URI = "sqlite:///netbook.db"
DB_POOL_SIZE = 20


# celery config
BROKER_URL = 'redis://192.168.1.100:6379/5'
CELERY_RESULT_BACKEND = 'redis://192.168.1.100:6379/4'
CELERY_IMPORTS = ('tasks', )
# CELERY_RESULT_PERSISTENT = True
# CELERY_TASK_RESULT_EXPIRES = None
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = (
    Queue('default', Exchange('tasks', type='topic'), routing_key='tasks.default'),
    Queue('download', Exchange('tasks', type='topic'), routing_key='tasks.download'),
    Queue('parse', Exchange('tasks', type='topic'), routing_key='tasks.parse'),
    Queue('schedule', Exchange('tasks', type='topic'), routing_key='tasks.schedule')
)
CELERY_DEFAULT_EXCHANGE = 'tasks'
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_DEFAULT_ROUTING_KEY = 'tasks.default'
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_ROUTES = {
    'tasks.parse_category_url': {
        'routing_key': 'tasks.parse',
    },
    'tasks.parse_book_url': {
        'routing_key': 'tasks.parse',
    },
    'tasks.parse_book_info': {
        'routing_key': 'tasks.parse',
    },
    'tasks.download_file': {
        'routing_key': 'tasks.download'
    },
    'tasks.tasks_schedule': {
        'routing_key': 'tasks.schedule',
    }
}
