#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""

__author__ = 'zhiyue'
__copyright__ = "Copyright 2016"
__credits__ = ["zhiyue"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "zhiyue"
__email__ = "cszhiyue@gmail.com"
__status__ = "Production"

from sqlalchemy import Column, String, create_engine, Integer, Table, MetaData
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine("sqlite:///netbook.db", echo=True)
metadata = MetaData()
metadata.create_all(engine)  #在数据库中生成表
Base = declarative_base()

book_table = Table(
    'book', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('author', String),
    Column('rage', String),
    Column('tag', String),
    Column('category', String)
)

metadata.create_all(engine)


class NetBook(object):
    pass


mapper(NetBook, book_table)

