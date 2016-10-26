#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""

from pprint import pprint

from flask import Flask, request, jsonify

from netbook.database import db_session
from netbook.models import Recommend, NetBook

__author__ = 'zhiyue'
__copyright__ = "Copyright 2016"
__credits__ = ["zhiyue"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "zhiyue"
__email__ = "cszhiyue@gmail.com"
__status__ = "Production"

app = Flask(__name__)


@app.route('/api/netbook/recommend', methods=['GET'])
def recommend():
    book_name = request.args.get('key')
    model_name = request.args.get('model')
    records = Recommend.query.filter(Recommend.name == book_name).filter(Recommend.model == model_name).order_by(
        Recommend.range).all()
    data = dict()
    data['similarity_books'] = list()
    for record in records:
        book_info = dict()
        book_info["book_name"] = record.similar_book_name
        book_info["book_words"] = record.similar_book_wordcount
        book_info["book_author"] = record.similar_book_author
        book_info["rate"] = record.similarity
        data['similarity_books'].append(book_info)
    # data['similarity_books'] = json.dumps(data['similarity_books'])
    return jsonify(data)
    # return json.dumps(data)


@app.route('/api/netbook/suggestion', methods=['GET'])
def suggestion():
    key = request.args.get('key')
    query_string = u'%{}%'.format(key)
    result = dict()
    result['suggestions'] = [record.name for record in NetBook.query.filter(NetBook.name.like(query_string)).all()]
    pprint(result)
    # result['suggestions'] = json.dumps(result['suggestions'])
    return jsonify(result)


@app.route('/', methods=['GET'])
def index():
    return app.send_static_file('index.html')


@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == '__main__':
    app.run(debug=True)
