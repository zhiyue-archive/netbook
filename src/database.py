#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
import logging
from sqlalchemy import Column, String, create_engine, Integer, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.scoping import scoped_session
from .spider.config import DB_URI


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

Base = declarative_base()

engine = create_engine(DB_URI)
DB_Session = sessionmaker(bind=engine)


class NetBook(Base):
    __tablename__ = 'book'

    info_url = Column(String, primary_key=True)
    name = Column(String)
    file_name = Column(String)
    author = Column(String)
    rate = Column(Float)
    tag = Column(String)
    category = Column(String)
    download_url = Column(String)
    word_count = Column(Integer)
    download_flag = Column(Boolean)


class Category(Base):
    __tablename__ = 'category'

    name = Column(String, primary_key=True)
    count = Column(Integer)


class Recommend(Base):
    __tablename__ = 'recommend'

    name = Column(String, primary_key=True)
    author = Column(String, primary_key=True)
    file_name = Column(String)
    similar_book_name = Column(String)
    similar_file_name = Column(String)
    similar_book_author = Column(String)
    similar_book_wordcount = Column(Integer)
    similarity = Column(Float)
    model = Column(String, primary_key=True)
    range = Column(Integer, primary_key=True)


if __name__ == '__main__':
    engine = create_engine(DB_URI, echo=True)

    #Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

