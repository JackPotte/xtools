#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
import sys
import os
import traceback
import cgi
#import urllib
#import re
#import datetime
#import time
#import htmllib


def main():
    for i in range(1, 32):
        if i <= 8:
            starttimestamp = "2011010" + str(i) + "000000"
            endtimestamp = "2011010" + str(i+1) + "000000"
        elif i == 9:
            starttimestamp = "20110109000000"
            endtimestamp = "20110110000000"
        else:
            starttimestamp = "201101" + str(i) + "000000"
            endtimestamp = "201101" + str(i+1) + "000000"
        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        print str(i) + " Querying for " + starttimestamp + " to " + endtimestamp + "..."
        cursor.execute(u'SELECT /* SLOW OK */ page_title,rev_timestamp,rev_user,rev_user_text FROM revision JOIN page ON rev_page=page_id WHERE rev_timestamp >= "' + starttimestamp + '" AND rev_timestamp < "' + endtimestamp + '" AND rev_parent_id=0 AND page_namespace=0;')
        results = cursor.fetchall()
        f = open("acs/allarticles/" + starttimestamp[:-6] + ".txt", "w")
        for j in results:
            f.write(j[0] + " " + str(j[1]) + " " + str(j[2]) + " " + j[3] + "\n")
        f.close()
        print str(i) + " Done."
    for i in range(1, 29):
        if i <= 8:
            starttimestamp = "2011020" + str(i) + "000000"
            endtimestamp = "2011020" + str(i+1) + "000000"
        elif i == 9:
            starttimestamp = "20110209000000"
            endtimestamp = "20110210000000"
        else:
            starttimestamp = "201102" + str(i) + "000000"
            endtimestamp = "201102" + str(i+1) + "000000"
        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        print str(i) + " Querying for " + starttimestamp + " to " + endtimestamp + "..."
        cursor.execute(u'SELECT /* SLOW OK */ page_title,rev_timestamp,rev_user,rev_user_text FROM revision JOIN page ON rev_page=page_id WHERE rev_timestamp >= "' + starttimestamp + '" AND rev_timestamp < "' + endtimestamp + '" AND rev_parent_id=0 AND page_namespace=0;')
        results = cursor.fetchall()
        f = open("acs/allarticles/" + starttimestamp[:-6] + ".txt", "w")
        for j in results:
            f.write(j[0] + " " + str(j[1]) + " " + str(j[2]) + " " + j[3] + "\n")
        f.close()
        print str(i) + " Done."
    for i in range(1, 32):
        if i <= 8:
            starttimestamp = "2011030" + str(i) + "000000"
            endtimestamp = "2011030" + str(i+1) + "000000"
        elif i == 9:
            starttimestamp = "20110309000000"
            endtimestamp = "20110310000000"
        else:
            starttimestamp = "201103" + str(i) + "000000"
            endtimestamp = "201103" + str(i+1) + "000000"
        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        print str(i) + " Querying for " + starttimestamp + " to " + endtimestamp + "..."
        cursor.execute(u'SELECT /* SLOW OK */ page_title,rev_timestamp,rev_user,rev_user_text FROM revision JOIN page ON rev_page=page_id WHERE rev_timestamp >= "' + starttimestamp + '" AND rev_timestamp < "' + endtimestamp + '" AND rev_parent_id=0 AND page_namespace=0;')
        results = cursor.fetchall()
        f = open("acs/allarticles/" + starttimestamp[:-6] + ".txt", "w")
        for j in results:
            f.write(j[0] + " " + str(j[1]) + " " + str(j[2]) + " " + j[3] + "\n")
        f.close()
        print str(i) + " Done."
    for i in range(1, 31):
        if i <= 8:
            starttimestamp = "2011040" + str(i) + "000000"
            endtimestamp = "2011040" + str(i+1) + "000000"
        elif i == 9:
            starttimestamp = "20110409000000"
            endtimestamp = "20110410000000"
        else:
            starttimestamp = "201104" + str(i) + "000000"
            endtimestamp = "201104" + str(i+1) + "000000"
        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        print str(i) + " Querying for " + starttimestamp + " to " + endtimestamp + "..."
        cursor.execute(u'SELECT /* SLOW OK */ page_title,rev_timestamp,rev_user,rev_user_text FROM revision JOIN page ON rev_page=page_id WHERE rev_timestamp >= "' + starttimestamp + '" AND rev_timestamp < "' + endtimestamp + '" AND rev_parent_id=0 AND page_namespace=0;')
        results = cursor.fetchall()
        f = open("acs/allarticles/" + starttimestamp[:-6] + ".txt", "w")
        for j in results:
            f.write(j[0] + " " + str(j[1]) + " " + str(j[2]) + " " + j[3] + "\n")
        f.close()
        print str(i) + " Done."
    for i in range(1, 32):
        if i <= 8:
            starttimestamp = "2011050" + str(i) + "000000"
            endtimestamp = "2011050" + str(i+1) + "000000"
        elif i == 9:
            starttimestamp = "20110509000000"
            endtimestamp = "20110510000000"
        else:
            starttimestamp = "201105" + str(i) + "000000"
            endtimestamp = "201105" + str(i+1) + "000000"
        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        print str(i) + " Querying for " + starttimestamp + " to " + endtimestamp + "..."
        cursor.execute(u'SELECT /* SLOW OK */ page_title,rev_timestamp,rev_user,rev_user_text FROM revision JOIN page ON rev_page=page_id WHERE rev_timestamp >= "' + starttimestamp + '" AND rev_timestamp < "' + endtimestamp + '" AND rev_parent_id=0 AND page_namespace=0;')
        results = cursor.fetchall()
        f = open("acs/allarticles/" + starttimestamp[:-6] + ".txt", "w")
        for j in results:
            f.write(j[0] + " " + str(j[1]) + " " + str(j[2]) + " " + j[3] + "\n")
        f.close()
        print str(i) + " Done."

def main_deleted():
    for i in range(1, 32):
        if i <= 8:
            starttimestamp = "2011010" + str(i) + "000000"
            endtimestamp = "2011010" + str(i+1) + "000000"
        elif i == 9:
            starttimestamp = "20110109000000"
            endtimestamp = "20110110000000"
        else:
            starttimestamp = "201101" + str(i) + "000000"
            endtimestamp = "201101" + str(i+1) + "000000"
        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        print str(i) + " Querying for " + starttimestamp + " to " + endtimestamp + "..."
        cursor.execute(u'SELECT /* SLOW OK */ ar_title,MIN(ar_timestamp),MAX(ar_timestamp),ar_user,ar_user_text FROM archive WHERE ar_timestamp >= "' + starttimestamp + '" AND ar_timestamp < "' + endtimestamp + '" AND ar_namespace=0 GROUP BY ar_title;')
        results = cursor.fetchall()
        f = open("acs/deletedarticles/" + starttimestamp[:-6] + ".txt", "w")
        for j in results:
            f.write(j[0] + " " + str(j[1]) + " " + str(j[2]) + " " + str(j[3]) + " " + j[4] + "\n")
        f.close()
        print str(i) + " Done."
    for i in range(1, 29):
        if i <= 8:
            starttimestamp = "2011020" + str(i) + "000000"
            endtimestamp = "2011020" + str(i+1) + "000000"
        elif i == 9:
            starttimestamp = "20110209000000"
            endtimestamp = "20110210000000"
        else:
            starttimestamp = "201102" + str(i) + "000000"
            endtimestamp = "201102" + str(i+1) + "000000"
        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        print str(i) + " Querying for " + starttimestamp + " to " + endtimestamp + "..."
        cursor.execute(u'SELECT /* SLOW OK */ ar_title,MIN(ar_timestamp),MAX(ar_timestamp),ar_user,ar_user_text FROM archive WHERE ar_timestamp >= "' + starttimestamp + '" AND ar_timestamp < "' + endtimestamp + '" AND ar_namespace=0 GROUP BY ar_title;')
        results = cursor.fetchall()
        f = open("acs/deletedarticles/" + starttimestamp[:-6] + ".txt", "w")
        for j in results:
            f.write(j[0] + " " + str(j[1]) + " " + str(j[2]) + " " + str(j[3]) + " " + j[4] + "\n")
        f.close()
        print str(i) + " Done."
    for i in range(1, 32):
        if i <= 8:
            starttimestamp = "2011030" + str(i) + "000000"
            endtimestamp = "2011030" + str(i+1) + "000000"
        elif i == 9:
            starttimestamp = "20110309000000"
            endtimestamp = "20110310000000"
        else:
            starttimestamp = "201103" + str(i) + "000000"
            endtimestamp = "201103" + str(i+1) + "000000"
        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        print str(i) + " Querying for " + starttimestamp + " to " + endtimestamp + "..."
        cursor.execute(u'SELECT /* SLOW OK */ ar_title,MIN(ar_timestamp),MAX(ar_timestamp),ar_user,ar_user_text FROM archive WHERE ar_timestamp >= "' + starttimestamp + '" AND ar_timestamp < "' + endtimestamp + '" AND ar_namespace=0 GROUP BY ar_title;')
        results = cursor.fetchall()
        f = open("acs/deletedarticles/" + starttimestamp[:-6] + ".txt", "w")
        for j in results:
            f.write(j[0] + " " + str(j[1]) + " " + str(j[2]) + " " + str(j[3]) + " " + j[4] + "\n")
        f.close()
        print str(i) + " Done."
    for i in range(1, 31):
        if i <= 8:
            starttimestamp = "2011040" + str(i) + "000000"
            endtimestamp = "2011040" + str(i+1) + "000000"
        elif i == 9:
            starttimestamp = "20110409000000"
            endtimestamp = "20110410000000"
        else:
            starttimestamp = "201104" + str(i) + "000000"
            endtimestamp = "201104" + str(i+1) + "000000"
        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        print str(i) + " Querying for " + starttimestamp + " to " + endtimestamp + "..."
        cursor.execute(u'SELECT /* SLOW OK */ ar_title,MIN(ar_timestamp),MAX(ar_timestamp),ar_user,ar_user_text FROM archive WHERE ar_timestamp >= "' + starttimestamp + '" AND ar_timestamp < "' + endtimestamp + '" AND ar_namespace=0 GROUP BY ar_title;')
        results = cursor.fetchall()
        f = open("acs/deletedarticles/" + starttimestamp[:-6] + ".txt", "w")
        for j in results:
            f.write(j[0] + " " + str(j[1]) + " " + str(j[2]) + " " + str(j[3]) + " " + j[4] + "\n")
        f.close()
        print str(i) + " Done."
    for i in range(1, 32):
        if i <= 8:
            starttimestamp = "2011050" + str(i) + "000000"
            endtimestamp = "2011050" + str(i+1) + "000000"
        elif i == 9:
            starttimestamp = "20110509000000"
            endtimestamp = "20110510000000"
        else:
            starttimestamp = "201105" + str(i) + "000000"
            endtimestamp = "201105" + str(i+1) + "000000"
        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        print str(i) + " Querying for " + starttimestamp + " to " + endtimestamp + "..."
        cursor.execute(u'SELECT /* SLOW OK */ ar_title,MIN(ar_timestamp),MAX(ar_timestamp),ar_user,ar_user_text FROM archive WHERE ar_timestamp >= "' + starttimestamp + '" AND ar_timestamp < "' + endtimestamp + '" AND ar_namespace=0 GROUP BY ar_title;')
        results = cursor.fetchall()
        f = open("acs/deletedarticles/" + starttimestamp[:-6] + ".txt", "w")
        for j in results:
            f.write(j[0] + " " + str(j[1]) + " " + str(j[2]) + " " + str(j[3]) + " " + j[4] + "\n")
        f.close()
        print str(i) + " Done."

#main()
main_deleted()
