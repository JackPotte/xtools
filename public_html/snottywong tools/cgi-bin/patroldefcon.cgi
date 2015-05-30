#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
import sys
import os
import datetime
import time

db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
cursor = db.cursor()
cursor.execute(u'SELECT /* SLOW OK */ rc_timestamp FROM recentchanges LEFT JOIN redirect ON rd_from=rc_cur_id where rd_from IS NULL AND rc_new=1 AND rc_patrolled=0 AND rc_namespace=0 AND rc_bot=0 ORDER BY rc_timestamp ASC limit 3;')
ts = cursor.fetchall()
lastts = ts[0][0]
secondtolastts = ts[1][0]
thirdtolastts = ts[2][0]
last = datetime.datetime(int(lastts[:4]), int(lastts[4:6]), int(lastts[6:8]), int(lastts[8:10]), int(lastts[10:12]), int(lastts[12:14]))
last2 = datetime.datetime(int(secondtolastts[:4]), int(secondtolastts[4:6]), int(secondtolastts[6:8]), int(secondtolastts[8:10]), int(secondtolastts[10:12]), int(secondtolastts[12:14]))
last3 = datetime.datetime(int(thirdtolastts[:4]), int(thirdtolastts[4:6]), int(thirdtolastts[6:8]), int(thirdtolastts[8:10]), int(thirdtolastts[10:12]), int(thirdtolastts[12:14]))
if (last3-last).total_seconds() > 40000:
    if (last3-last2).total_seconds() > 40000:
        lastunpatrolled = last3
    else:
        lastunpatrolled = last2
else:
    lastunpatrolled = last
today = datetime.datetime.today()
diff = today - lastunpatrolled
d = round(diff.days + (diff.seconds/86400.0), 2)
print d
