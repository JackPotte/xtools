#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
import sys
import os
import cgi
import datetime

f = open("abusequerylog.txt", "a")
f.write("<log><ip>" + os.environ["REMOTE_ADDR"] + "</ip><timestamp>" + datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</timestamp></log>\n")
f.close()


db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
cursor = db.cursor()
cursor.execute('select rc_this_oldid, rc_timestamp, rc_minor, rc_comment, rc_title, rc_user_text from recentchanges where rc_timestamp>20120530000000 and rc_namespace=0 and rc_minor=0 and rc_new=0 and (rc_comment LIKE "/* Race */%" or rc_comment LIKE "/* Race Result%*/%" or rc_comment LIKE "/* Race result%*/%" or rc_comment LIKE "/* Complete Formula One results */%" or rc_comment LIKE "/* Drivers and constructors */%" or rc_comment LIKE "/* Classification */%") and (rc_user_text LIKE "2.24.%" or rc_user_text LIKE "2.27.%" or rc_user_text LIKE "2.30.%" or rc_user_text LIKE "31.185.%" or rc_user_text LIKE "37.152.%" or rc_user_text LIKE "46.208.%" or rc_user_text LIKE "81.151.%" or rc_user_text LIKE "81.152.%" or rc_user_text LIKE "84.93.%" or rc_user_text LIKE "86.135.%" or rc_user_text LIKE "86.169.%" or rc_user_text LIKE "87.112.%" or rc_user_text LIKE "87.113.%" or rc_user_text LIKE "87.114.%" or rc_user_text LIKE "87.115.%" or rc_user_text LIKE "91.125.%" or rc_user_text LIKE "91.125.%" or rc_user_text LIKE "92.6.%") order by rc_timestamp desc;')
results = cursor.fetchall()

def formatline(edit):   #returns unordered list html for an edit
    revid = str(edit[0])
    timestamp = formatdate(edit[1])
    minoredit = edit[2]
    comment = escapehtml(edit[3].replace("[[WP:AES|←]]", "←"))
    fulltitle = edit[4]
    username = edit[5]
    return '<li><a href="http://en.wikipedia.org/w/index.php?title=' + fulltitle + '&oldid=' + revid + '">' + timestamp + '</a> (<a href="http://en.wikipedia.org/w/index.php?title=' + fulltitle + '&diff=prev&oldid=' + revid + '">diff</a> | <a href="http://en.wikipedia.org/w/index.php?title=' + fulltitle + '&action=history">hist</a>) . . ' + ("<b>m</b> " if minoredit else "") + '<a href="http://en.wikipedia.org/wiki/' + fulltitle + '">' + fulltitle.replace("_", " ") + '</a> . . <a href="http://en.wikipedia.org/wiki/User:' + username + '">' + username + '</a> . . ' + (('(<span class="comment">' + fmtcmt(comment) + '</span>)') if comment else '') + '</li>'

def formatdate(ts): #formats timestamp into text
    d = datetime.datetime(int(ts[:4]), int(ts[4:6]), int(ts[6:8]), int(ts[8:10]), int(ts[10:12]), int(ts[12:14]))
    return d.strftime("%H:%M, %B %d, %Y")        
def fmtcmt(comment):    #adds an autocomment span into the comment if section header detected
    if "/*" in comment and "*/" in comment:
        return comment.replace("/*", '<span class="autocomment">/*', 1).replace("*/", "*/</span>", 1)
    return comment

def escapehtml(s):  #escapes various characters to prevent attacks
    s = s.replace("&", "&amp;") # Must be first
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', '&quot;')
    return s

print """<!doctype html>
<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
<LINK href="menubar3.css" rel="stylesheet" type="text/css">
<TITLE>Abuse Search Query</TITLE>
</HEAD>
<BODY id="yes">
<script type="text/javascript" src="/menubar.js"></script>
<br>
<div id="globalWrapper">
<H1>Abuse Search Query</H1>
"""

print "<ul>"
for e in results:
    print formatline(e)
print "</ul>"
print "</div>"
print "</body>"
print "</html>"

