#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
import sys
import os
import cgi
import json

database = ""
db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
cursor = db.cursor()
form = cgi.FieldStorage()
if "db" in form:
    database = form['db'].value
else:
    sys.exit(0)
cursor.execute("SELECT ns_name, ns_id FROM toolserver.namespacename WHERE dbname=%s", (database))
namespaces = cursor.fetchall()
nondupns = []
nslist = []
for i in namespaces:
    if i[1] in nslist:
        continue
    if i[1] < 0:
        continue
    nslist.append(i[1])
    nondupns.append(i)
print json.dumps(sorted(nondupns, key=lambda x:x[1]))

