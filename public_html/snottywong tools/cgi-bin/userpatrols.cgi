#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import *
from urllib import quote
import re
import time
import cgi
import MySQLdb
import os
import sys
import traceback

now = datetime.utcnow()

def main():
    global now
    try:
        print """<!doctype html>
<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
<LINK href="greyscale.css" rel="stylesheet" type="text/css">
<LINK href="menubar3.css" rel="stylesheet" type="text/css">
<TITLE>User NPP report</TITLE>
</HEAD>
<BODY id="no">
<script type="text/javascript" src="/menubar.js"></script>
<br>
<H1>User new page patrol report</H1>
"""
        starttime = time.time()
        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        form = cgi.FieldStorage()
        if "name" not in form:
            errorout("No name entered.")
        username = form['name'].value.replace("_", " ").replace("+", " ")
        if username.lower().startswith("user:"):
            username = username[5:]

        if os.environ["REMOTE_ADDR"].startswith("89.151.116.5"):
            errorout("Your IP address has been flagged for potential abuse.  Please post a message to User talk:Scottywong on the English Wikipedia, or alternatively send an email to snottywong.wiki@gmail.com to prove that you are a human, and to explain why you've been consistently making so many queries on this tool.")

        f = open("userpatrolslog.txt", "a")
        f.write("<log><ip>" + os.environ["REMOTE_ADDR"] + "</ip><username>" + username + "</username><timestamp>" + datetime.utcnow().strftime("%m/%d/%y %H:%M:%S") + "</timestamp>" + "</log>\n")
        f.close()

        
        cursor.execute("""SELECT COUNT(*) FROM logging JOIN user ON log_user=user_id WHERE user_name=%s AND log_type="patrol" AND log_action="patrol" AND (log_params LIKE '%%"6::auto";i:0;%%' OR log_params REGEXP "^[0-9]+\n[0-9]+\n0$");""", (username))
        patrolcount = int(cursor.fetchall()[0][0])

        if patrolcount == 0:
            errorout("No patrols found for this user.")

        cursor.execute("""SELECT log_page, log_timestamp, log_namespace, log_title, log_params FROM logging JOIN user ON log_user=user_id WHERE user_name=%s AND log_type="patrol" AND log_action="patrol" AND (log_params LIKE '%%"6::auto";i:0;%%' OR log_params REGEXP "^[0-9]+\n[0-9]+\n0$") ORDER BY log_timestamp DESC LIMIT 500;""", (username))
        patrols = cursor.fetchall()
        timediffs = {}  #dictionary with page id as key, article age at patrol time (in seconds, as a float) as value
        datetimes = []  #list of all patrol datetimes
        for patrol in patrols:
            datetimes.append(parsetimestamp(patrol[1]))
            if patrol[0]:
                cursor.execute("SELECT MIN(rev_timestamp) FROM revision JOIN page ON rev_page=page_id WHERE page_namespace=0 AND page_id=%s;", (patrol[0]))
            else:
                cursor.execute("SELECT MIN(rev_timestamp) FROM revision JOIN page ON rev_page=page_id WHERE page_namespace=0 AND page_title=%s;", (patrol[3]))
            pagebirth = cursor.fetchall()[0][0]
            if not pagebirth:
                continue
            timediffs[patrol[3]] = (parsetimestamp(patrol[1]) - parsetimestamp(pagebirth)).total_seconds()
            
        times = timediffs.values()
        times.sort()
        averagetime = float(sum(times)) / float(len(times))
        if len(times) % 2 == 0:
            mediantime = (times[(len(times)/2) - 1] + times[len(times)/2]) / 2.0
        else:
            mediantime = times[len(times)/2]

        prevdt = datetime(2200,1,1) #Dummy starting datetime
        secondsbetween = []         #List of seconds between edits (only if number of seconds < 3600)
        for dt in datetimes:
            if (prevdt-dt).total_seconds() < 3600:
                secondsbetween.append((prevdt-dt).total_seconds())
            prevdt = dt
        avgtimebetween = formattimebetween(sum(secondsbetween) / float(len(secondsbetween)))
        mintimebetween = formattimebetween(min(secondsbetween))

        print "<h3>New page patrolling statistics for User:" + escapehtml(username.replace("_", " ")) + "</h3><br>"
        print "Total number of articles patrolled: " + str(patrolcount) + "<br>"
        print "Average age of articles at patrol time" + (" (last 500 patrols): " if patrolcount>500 else ": ") + parsetimedelta(timedelta(0, averagetime)) + "<br>"
        print "Median age of articles at patrol time" + (" (last 500 patrols): " if patrolcount>500 else ": ") + parsetimedelta(timedelta(0, mediantime)) + "<br><br>"

        print "While patrolling articles one after the next, average time between patrols: " + avgtimebetween + "<br>"
        print "While patrolling articles one after the next, minimum time between patrols: " + mintimebetween + "<br><br>"

        print "<h2>Last " + str(min(500, patrolcount)) + " patrols:</h2><br>"
        print "Click on the article title to go to the current revision of that article; click on the <small><strong>(rev)</strong></small> link to go to the patrolled revision of that article.<br><br>"        
        print """<table>
<thead>
<tr>
<th scope="col">Article patrolled</th>
<th scope="col">Patrol time</th>
<th scope="col">Article age at patrol time</th>
</tr></thead>
<tbody>
"""
        for patrol in patrols:
            print "<tr>"
            print "<td>" + articlelink(patrol[3]) + "</td>"
            print "<td>" + parsetimestamp(patrol[1]).strftime("%H:%M, %d %B %Y") + "</td>"
            print "<td>" + timedifflink(patrol[3], (timediffs[patrol[3]] if patrol[3] in timediffs else None), patrol[4]) + "</td>"
            print "</tr>"
        print "</tbody>\n</table>"       
        
        elapsed = time.time() - starttime
        print "<br><br><small>Elapsed time: " + str(round(elapsed, 2)) + " seconds.<br>\n"
        print now.strftime("%m/%d/%y %H:%M:%S") + "</small><br>"
        print '<small>Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Scottywong">User talk:Scottywong</a></small><br>'
        print "</BODY>\n</HTML>"
        
    except SystemExit:
        pass
    except:
        print sys.exc_info()[0]
        print "<br>"
        print traceback.print_exc(file=sys.stdout)
        print "<br>"

def parsetimestamp(t):
    return datetime(int(t[:4]), int(t[4:6]), int(t[6:8]), int(t[8:10]), int(t[10:12]), int(t[12:14]))


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

def formattimebetween(sec):
    if sec < 60:
        return str(int(sec)) + " seconds"
    return str(int(sec/60)) + " minutes, " + str(int(sec%60)) + " seconds"

def articlelink(a):
    if len(a) <= 64:
        return '<a href="http://en.wikipedia.org/wiki/' + a + '">' + a.replace("_", " ") + '</a>'
    return '<a href="http://en.wikipedia.org/wiki/' + a + '">' + a[:61].replace("_", " ") + '...</a>'

def timedifflink(title, age, logparams):
    #call parsetimedelta with timedelta(0,age) to get text string
    #parse logparams to get curid, use curid in link target
    if re.match("^\d+\n\d+\n\d+$", logparams):  #old style params
        curid = re.match("^(\d+)\n\d+\n\d+$", logparams).group(1)
    else:
        curid = re.search("\"4::curid\";s:\d+:\"(\d+)\"", logparams).group(1)
    if age:
        return parsetimedelta(timedelta(0, age)) + '&nbsp;<a href="http://en.wikipedia.org/w/index.php?title=' + quote(title) + '&oldid=' + curid + '"><small>(rev)</small></a>'
    return '<small>(Page deleted)</small>'

def escapehtml(s):  #escapes various characters to prevent attacks
    s = s.replace("&", "&amp;") # Must be first
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', '&quot;')
    return s

def errorout(errorstr): #prints error string and exits
    print "ERROR: " + errorstr + "<br><br>Please try again.<br>"
    print "</div></BODY>\n</HTML>"
    sys.exit(0)

main()
