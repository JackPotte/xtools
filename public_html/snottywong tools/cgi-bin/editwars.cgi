#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
import sys
import os
from datetime import *
import cgi
import urllib

print """<!doctype html>
<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
<LINK href="greyscale.css" rel="stylesheet" type="text/css">
<LINK href="menubar3.css" rel="stylesheet" type="text/css">
<TITLE>Possible edit wars</TITLE>
</HEAD>
<BODY id="no">
<script type="text/javascript" src="/menubar.js"></script>
<br>
<H1>Possible Edit Wars</H1>"""

form = cgi.FieldStorage()
try:
    if "min" in form:
        edittime = int(form["min"].value)
        edittime = min(120, edittime)
        edittime = max(5, edittime)
    else:
        edittime = 30
except:
    edittime = 30

db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
cursor = db.cursor()
cursor.execute("select /*SLOW_OK*/ page_title, rev_user_text, rev_timestamp from revision join page on rev_page=page_id where rev_timestamp>%s and page_namespace=0;", (datetime.utcnow()-timedelta(minutes=edittime)).strftime("%Y%m%d%H%m%S"))
results = cursor.fetchall()
freq = {}
for edit in results:
    if edit[0] in freq:
        freq[edit[0]] += 1
    else:
        freq[edit[0]] = 1

freqs = {}
for page in freq.keys():
    pageedits = [e for e in results if e[0] == page]
    editors = {}
    for edit in pageedits:
        if edit[1] in editors:
            editors[edit[1]] += 1
        else:
            editors[edit[1]] = 1
    topeditorpct = 100.0 * (max(editors.values()) / float(sum(editors.values())))
    score = freq[page] * (-1.0 * (topeditorpct - 100.0))
    freqs[page] = (freq[page], topeditorpct, score)

print "Showing the top 50 articles with the highest chance of an edit war in the last %s minutes.<br>" % str(edittime)
print """
<table>
<thead>
<tr>
<th scope="col">Page</th>
<th scope="col">Edits</th>
<th scope="col">% of edits by top editor</th>
</tr>
</thead>
<tbody>"""
for page in sorted(freqs, key=lambda x: freqs[x][2], reverse=True)[:50]:
    print "<tr>"
    print '<td><a href="http://en.wikipedia.org/wiki/' + urllib.quote(page, ":") + '">' + page.replace("_", " ") + '</a></td>'
    print '<td>' + str(freqs[page][0]) + '</td>'
    print '<td>' + str(int(round(freqs[page][1],0))) + '%</td>'
print """</tbody>
</table>
</body>
</html>"""
