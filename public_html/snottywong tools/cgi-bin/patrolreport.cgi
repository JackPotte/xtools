#!/usr/bin/env python
# -*- coding: utf-8 -*-

#To do: change howlongago() and parsetimedelta() so that they omit smaller time quantities if larger ones are present (i.e. if the time is days in length, then we don't need minutes and seconds)


import urllib
import re
import datetime
import time
import MySQLdb
import os
import sys
import traceback

def howlongago(t):
    global now
    delta = now - t
    agostr = ""
    levels = 0
    if delta.days > 1:
        agostr += str(delta.days) + " days, "
        levels += 1
    elif delta.days == 1:
        agostr += "1 day, "
        levels += 1
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    seconds = delta.seconds % 60
    if hours > 1:
        agostr += str(hours) + " hours, "
        levels += 1
    elif hours == 1:
        agostr += "1 hour, "
        levels += 1
    if levels == 2:
        return agostr[:-2] + " ago"
    if minutes > 1:
        agostr += str(minutes) + " minutes, "
        levels += 1
    elif minutes == 1:
        agostr += "1 minute, "
        levels += 1
    if levels == 2:
        return agostr[:-2] + " ago"
    if seconds != 1:
        agostr += str(seconds) + " seconds ago"
    else:
        agostr += "1 second ago"
    return agostr

def parsetimedelta(delta):
    agostr = ""
    levels = 0
    if delta.days > 1:
        agostr += str(delta.days) + " days, "
        levels += 1
    elif delta.days == 1:
        agostr += "1 day, "
        levels += 1
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    seconds = delta.seconds % 60
    if hours > 1:
        agostr += str(hours) + " hours, "
        levels += 1
    elif hours == 1:
        agostr += "1 hour, "
        levels += 1
    if levels == 2:
        return agostr[:-2]
    if minutes > 1:
        agostr += str(minutes) + " minutes, "
        levels += 1
    elif minutes == 1:
        agostr += "1 minute, "
        levels += 1
    if levels == 2:
        return agostr[:-2]
    if seconds != 1:
        agostr += str(seconds) + " seconds"
    else:
        agostr += "1 second"
    return agostr

def userlink(u):    #format hyperlink to user page and user patrol log
    return '<a href="http://en.wikipedia.org/wiki/User:' + u + '">' + u + '</a> <a href="http://en.wikipedia.org/w/index.php?title=Special%3ALog&type=patrol&user=' + u + '">' + '<small><sup>log</sup></small></a>'

def articlelink(a):
    if len(a) <= 64:
        return '<a href="http://en.wikipedia.org/wiki/' + a + '">' + a + '</a>'
    return '<a href="http://en.wikipedia.org/wiki/' + a + '">' + a[:61] + '...</a>'

def printtable(pp):
    print """<H2>Recently patrolled articles</H2>
<table>
<thead>
<tr>
<th scope="col">User</th>
<th scope="col">Article patrolled</th>
<th scope="col">Patrol time</th>
<th scope="col">Article creation time</th>
</tr></thead>
<tbody>
"""
    for p in pp:
        print "<tr>"
        print "<td>" + userlink(p[0]) + "</td>"
        print "<td>" + articlelink(p[1]) + "</td>"
        print "<td>" + howlongago(p[2]) + "</td>"
        print "<td>" + howlongago(p[3]) + "</td>"
        print "</tr>"
    print "</tbody>\n</table>"

def printanalysis(pp):
    uniqueusers = []
    analyzedusers = []
    frontpatrollers = 0
    backpatrollers = 0
    for i in pp:
        if i[0] not in uniqueusers:
            uniqueusers.append(i[0])
    for user in uniqueusers:
        agelist = []
        timelist = []
        patrolcount = 0
        for patrol in pp:
            if patrol[0] == user:
                if patrol[2] < patrol[3]:   #Probably the result of an article that was deleted and recreated quickly
                    #print user
                    continue
                patrolcount += 1
                agelist.append(patrol[2] - patrol[3])
                timelist.append(patrol[2])
        if patrolcount == 0:
            continue
        agesum = datetime.timedelta(0,0,0)
        for age in agelist:
            agesum += age
        averageage = agesum / patrolcount
        if averageage < datetime.timedelta(0,3600,0):
            frontpatrollers += 1
        elif averageage > datetime.timedelta(15,0,0):
            backpatrollers += 1
        averagetime = (max(timelist) - min(timelist)) / len(timelist)
        analyzedusers.append([user, patrolcount, averageage, averagetime])
    print "Number of users recently patrolling articles: " + str(len(analyzedusers)) + "<br>\n"
    print "Number of users consistently patrolling the front of the queue: " + str(frontpatrollers) + "<br>\n"
    print "Number of users consistently patrolling the back of the queue: " + str(backpatrollers) + "<br>\n"
    print """<H2>User stats</H2>
<table>
<thead>
<tr>
<th scope="col">User</th>
<th scope="col"># of recent<br>patrols</th>
<th scope="col">Average age of<br>patrolled articles</th>
<th scope="col">Average time<br>between patrols</th>
</tr></thead>
<tbody>
"""
    for u in analyzedusers:
        print "<tr>"
        print "<td>" + userlink(u[0]) + "</td>"
        print '<td class="c">' + str(u[1]) + "</td>"
        print "<td>" + parsetimedelta(u[2]) + "</td>"
        timebetween = parsetimedelta(u[3])
        if timebetween == "0 seconds":
            print "<td>N/A</td>"
        else:
            print "<td>" + timebetween + "</td>"
        print "</tr>"
    print "</tbody>\n</table><br>"
        
#main stuff
try:
    starttime = time.time()
    patrolregex = re.compile('<item logid=\".*?</item>', re.DOTALL)
    patrollerregex = re.compile('user=\"(.*?)\"')
    patroltimeregex = re.compile('timestamp=\"(.*?)Z\"')
    pageidregex = re.compile('pageid=\"(.*?)\"')
    pagenameregex = re.compile('title=\"(.*?)\"')
    botlist = ["DASHBot"]

    f = open("patrolreportlog.txt", "a")
    try:
        ip = os.environ["HTTP_X_FORWARDED_FOR"]
    except KeyError:
        ip = os.environ["REMOTE_ADDR"]
    f.write("<log><ip>" + ip + "</ip><timestamp>" + datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</timestamp></log>\n")
    f.close()

    url = urllib.urlopen("http://en.wikipedia.org/w/api.php?action=query&list=logevents&letype=patrol&lelimit=500&format=xml")
    data = url.read()
    url.close()
    patrol = re.findall('<item logid=\".*?</item>', data, re.DOTALL)
    goodpatrols = []
    for i in patrol:
        if 'ns="0"' in i and 'auto="0"' in i:
            goodpatrols.append(i)
    parsedpatrols = []
    db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
    cursor = db.cursor()
    for i in goodpatrols:
        pageid = pageidregex.search(i).group(1)
        if pageid == "0":
            continue
        user = patrollerregex.search(i).group(1)
        if user in botlist:
            continue
        timestamp = patroltimeregex.search(i).group(1)
        title = pagenameregex.search(i).group(1)
        patroldate = datetime.datetime(int(timestamp[:4]), int(timestamp[5:7]), int(timestamp[8:10]), int(timestamp[11:13]), int(timestamp[14:16]), int(timestamp[17:19]))
        cursor.execute("SELECT MIN(rev_timestamp) FROM revision JOIN page ON rev_page=page_id WHERE page_id=" + pageid + ";")
        results = cursor.fetchall()
        pagebirth = results[0][0]
        if not pagebirth:
            continue
        pagebirthdate = datetime.datetime(int(pagebirth[:4]), int(pagebirth[4:6]), int(pagebirth[6:8]), int(pagebirth[8:10]), int(pagebirth[10:12]), int(pagebirth[12:14]))
        parsedpatrols.append([user, title, patroldate, pagebirthdate])

    now = datetime.datetime.today()# + datetime.timedelta(hours=7)   #get rid of timedelta when transferring to toolserver
    print """<!doctype html>
<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
<LINK href="greyscale.css" rel="stylesheet" type="text/css">
<LINK href="menubar3.css" rel="stylesheet" type="text/css">
<TITLE>New page patrol report</TITLE>
</HEAD>
<BODY id="no">
<script type="text/javascript" src="/menubar.js"></script>
<br>
<H1>New page patrol report</H1>
"""
    print '<div style="width:875px;">This report lists various information about articles which have recently been patrolled.  The first table has statistics for users who have recently patrolled an article, and the second table lists all of the (non-automatic) patrols that have happened recently.</div><br><br>\n'
    printanalysis(parsedpatrols)
    printtable(parsedpatrols)
    elapsed = time.time() - starttime
    print "<br><br><small>Elapsed time: " + str(round(elapsed, 2)) + " seconds.<br>\n"
    print datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</small><br>"
    print '<small>Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Snottywong">User talk:Snottywong</a></small><br>'

except:
    print sys.exc_info()[0]
    print "<br>"
    print traceback.print_exc(file=sys.stdout)
    print "<br>"
print "</BODY>\n</HTML>"
