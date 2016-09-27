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

import cPickle as pickle
from  tasks import parse_category_url,download_file


classify_infos = pickle.load(open("classify_infos.p", "rb"))

for k, v in classify_infos.items():
    print "add %s, %s" % (k, v)
    parse_category_url.delay(v)


# download_file.delay("http://dzs.qisuu.com/txt/26.txt")
