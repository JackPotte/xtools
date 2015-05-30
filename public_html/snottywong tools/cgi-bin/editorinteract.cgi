#!/usr/bin/env python
# -*- coding: utf-8 -*-

#TODO:
#Improvements:
#Cap list at certain number or time between edits
#Display edit count per page per editor
#Display average time between edits?
#Display overall edit count of each editor?  and first edit date?
#Make timeline easier to read: color-code different editors, display time between edits when editor changes in timeline

import sys
import os
import traceback
import cgi
import urllib
import htmllib
from datetime import *
import MySQLdb
import time

nslookup = {0:"", 1:"Talk:", 2:"User:", 3:"User talk:", 4:"Wikipedia:", 5:"Wikipedia talk:", 6:"File:", 7:"File talk:", 8:"MediaWiki:", 9:"MediaWiki talk:", 10:"Template:", 11:"Template talk:", 12:"Help:", 13:"Help talk:", 14:"Category:", 15:"Category talk:", 100:"Portal:", 101:"Portal talk:", 108:"Book:", 109:"Book talk:", 446:"Education Program", 447:"Education Program talk", 710:"TimedText", 711:"TimedText talk", 828:"Module", 829:"Module talk"}
#nsrevlookup = dict((v,k) for k,v in nslookup.iteritems())

def main():
    global nslookup
    #global nsrevlookup

    starttime = time.time()

    epoch = datetime(2000,1,1)

    try:
        print """<!doctype html>
<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
<LINK href="greyscale.css" rel="stylesheet" type="text/css">
<LINK href="menubar3.css" rel="stylesheet" type="text/css">
<TITLE>Editor Interaction Analyzer</TITLE>
</HEAD>
<BODY id="no">
<script type="text/javascript" src="/menubar.js"></script>
<br>
<div style="width:875px;">
<a href="editorinteract.html"><small>&larr;New search</small></a>
<H1>Editor Interaction Analyzer</H1>
This tool shows the common pages that two or more editors have both edited, sorted by minimum time between edits by the users.  In other words, if the editors made an edit to the same page within a short time, that page will show up towards the top of the table.  In general, when two users edit a page within a short time, chances are high that they have interacted directly with one another on that page.  Click on the &quot;timeline&quot; link to see the edits that both users have made to the page in chronological order.<br><br>
"""

        form = cgi.FieldStorage()
        userlist = []

        for usernum in range(1,11):
            if ("user" + str(usernum)) in form:
                u = form[("user" + str(usernum))].value.replace("_", " ").strip()
                u = u[0].capitalize() + u[1:]
                userlist.append(u)
        
        if len(userlist) < 2:
            errorout("At least two users must be specified.")
        
        editlimit = int(round(100.0/len(userlist), 0)*1000)
        
        try:
            if "ns" in form:
                ns = int(form["ns"].value.strip())
            else:
                ns = -1
            if ns not in [-1,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,100,101,108,109]:
                ns = -1
        except:
            ns = -1

        try:
            if "startdate" in form:
                startdate = form["startdate"].value.strip()
                if len(startdate) != 8:
                    errorout("Invalid start date.")
                if int(startdate[:4]) < 2000 or int(startdate[:4]) > datetime.utcnow().year:
                    errorout("Invalid start date.")
                if int(startdate[4:6]) < 1 or int(startdate[4:6]) > 12:
                    errorout("Invalid start date.")
                if int(startdate[6:8]) < 1 or int(startdate[6:8]) > 31:
                    errorout("Invalid start date.")
                temp = datetime.strptime(startdate, "%Y%m%d")
            else:
                startdate = None
        except SystemExit:
            sys.exit(0)
        except:
            errorout("Invalid start date.")

        try:
            if "enddate" in form:
                enddate = form["enddate"].value.strip()
                if len(enddate) != 8:
                    errorout("Invalid end date.")
                if int(enddate[:4]) < 2000 or int(enddate[:4]) > datetime.utcnow().year:
                    errorout("Invalid end date.")
                if int(enddate[4:6]) < 1 or int(enddate[4:6]) > 12:
                    errorout("Invalid end date.")
                if int(enddate[6:8]) < 1 or int(enddate[6:8]) > 31:
                    errorout("Invalid end date.")
                temp = datetime.strptime(startdate, "%Y%m%d")
            else:
                enddate = None
        except SystemExit:
            sys.exit(0)
        except:
            errorout("Invalid end date.")

        if "allusers" in form:
            alluserscommon = form["allusers"].value.strip()
            if alluserscommon.lower() == "true" or alluserscommon == "1" or alluserscommon.lower() == "yes" or alluserscommon.lower() == "y":
                alluserscommon = True
            else:
                alluserscommon = False
        else:
            alluserscommon = False

        if startdate and enddate:
            if int(startdate) >= int(enddate):
                errorout("Start date cannot be greater than end date.")

        if os.environ["REMOTE_ADDR"].startswith("89.151.116.5"):
            errorout("Your IP address has been flagged for potential abuse.  Please post a message to User talk:Scottywong on the English Wikipedia, or alternatively send an email to snottywong.wiki@gmail.com to prove that you are a human, and to explain why you've been consistently making so many queries on this tool.")


        f = open("editorinteractlog.txt", "a")
        f.write("<log><ip>" + os.environ["REMOTE_ADDR"] + "</ip><type>editorinteract</type>" +
                (("<user1>" + userlist[0] + "</user1>") if len(userlist)>=1 else "") +
                (("<user2>" + userlist[1] + "</user2>") if len(userlist)>=2 else "") +
                (("<user3>" + userlist[2] + "</user3>") if len(userlist)>=3 else "") +
                (("<user4>" + userlist[3] + "</user4>") if len(userlist)>=4 else "") +
                (("<user5>" + userlist[4] + "</user5>") if len(userlist)>=5 else "") +
                (("<user6>" + userlist[5] + "</user6>") if len(userlist)>=6 else "") +
                (("<user7>" + userlist[6] + "</user7>") if len(userlist)>=7 else "") +
                (("<user8>" + userlist[7] + "</user8>") if len(userlist)>=8 else "") +
                (("<user9>" + userlist[8] + "</user9>") if len(userlist)>=9 else "") +
                (("<user10>" + userlist[9] + "</user10>") if len(userlist)>=10 else "") +
                "<ns>" + str(ns) + "</ns><timestamp>" + datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</timestamp>" + (("<startdate>" + startdate + "</startdate>") if startdate else "") + (("<enddate>" + enddate + "</enddate>") if enddate else "") + ("<allusers>true</allusers>" if alluserscommon else "") + "</log>\n")
        f.close()

        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()

        editcounts = {}

        for user in userlist:
            cursor.execute("SELECT COUNT(*) FROM revision WHERE rev_user_text=%s;", (user))
            editcounts[user] = cursor.fetchall()[0][0]
            print "<b>" + user + "</b> edit count: " + str(editcounts[user]) + (" (only most recent " + str(editlimit) + " edits will be analyzed)<br>" if editcounts[user] > editlimit else "<br>")

        if startdate and not enddate:
            print "<br>Only analyzing edits from " + prettydate(startdate) + " and later.<br>"
        if enddate and not startdate:
            print "<br>Only analyzing edits from " + prettydate(enddate) + " and earlier.<br>"
        if startdate and enddate:
            print "<br>Only analyzing edits from " + prettydate(startdate) + " to " + prettydate(enddate) + ".<br>"
        
        print '<br>Numbers in <span style="color:blue;">blue</span> indicate which editor first edited the page.<br><br>'
        
        querystr = "SELECT page_namespace, page_title, rev_timestamp FROM revision JOIN page ON rev_page=page_id WHERE rev_deleted=0 AND rev_user_text=%s"
        queryparams = ()

        if ns >= 0:
            querystr += " AND page_namespace=%s"
            queryparams += (ns,)

        if startdate:
            querystr += " AND rev_timestamp > %s"
            queryparams += (startdate + "000000",)

        if enddate:
            querystr += " AND rev_timestamp < %s"
            queryparams += (enddate + "235959",)

        querystr += " ORDER BY rev_timestamp DESC LIMIT %s;"
        queryparams += (editlimit,)

        useredits = {}  #{Username:[("Namespace:pagetitle",rev_timestamp),(page,timestamp)...], Username2:[(page,timestamp)...]}
        for user in userlist:
            cursor.execute(querystr, (user,) + queryparams)
            userdata = cursor.fetchall()
            editlist = []
            for edit in userdata:
                editlist.append((nslookup[edit[0]] + edit[1], formatdate(edit[2])))
            useredits[user] = sorted(editlist, key=lambda x: (x[1]-epoch).total_seconds())

        commonpages = []
        if alluserscommon:
            #Find all pages where all users have edited, simple intersection of all edit lists
            allpages = []
            for user in userlist:
                allpages.append(set([p[0] for p in useredits[user]]))
            commonpages = set.intersection(*allpages)
        else:
            #Find all pages which at least 2 different editors have edited
            #Iterate through, intersection of one user's edits with union of all remaining users' edits
            for usernum in range(len(userlist)-1):
                unionset = []
                for u in range(usernum+1, len(userlist)):
                    unionset += [e[0] for e in useredits[userlist[u]]]
                unionset = set(unionset)
                commonpages += list(set(e[0] for e in useredits[userlist[usernum]]) & unionset)
        commonpages = list(set(commonpages))

        #Find minimum time between edits by different users on each page
        pagescores = {}
        for page in commonpages:
            alledits = []   #List of tuples (editor, timestamp)
            for user in userlist:
                alledits += [(user, (edit[1]-epoch).total_seconds()) for edit in useredits[user] if edit[0]==page]
            alledits = sorted(alledits, key=lambda x: x[1])
            #print alledits
            lasteditor = None
            lastedittime = 0
            mintime = 900000000
            for edit in alledits:
                #print mintime
                if edit[0] == lasteditor:
                    continue
                if edit[1] - lastedittime < mintime:
                    mintime = edit[1] - lastedittime
                lasteditor = edit[0]
                lastedittime = edit[1]
            absmintime = min(e[1] for e in alledits)
            for e in alledits:
                if e[1]==absmintime:
                    firsteditor = e[0]
            pagescores[page] = (mintime, firsteditor)
        
        print """</div>
<table>
<thead>
<tr>
<th scope="col">Page</th>
<th scope="col">Min. Time Between Edits</th>
"""
        for user in userlist:
            print '<th scope="col"><small>%s<br>Edits</small></th>' % user
        print "</tr>\n</thead>\n<tbody>"

        rowcounter = 0
        for page in sorted(pagescores, key=pagescores.get):
            if rowcounter > 250:
                break
            if (pagescores[page][0] > 604800) and rowcounter > 10:  #If there's a few entries and min time between edits > 1 week, then just quit
                break
            timelineurl = "cgi-bin/timeline.cgi?page=" + urllib.quote(page.replace(" ", "_"), ":")
            for usernum in range(len(userlist)):
                timelineurl += "&user" + str(usernum+1) + "=" + userlist[usernum].replace(" ", "_")
            timelineurl += (("&startdate=" + startdate) if startdate else "") + (("&enddate=" + enddate) if enddate else "")
            print '<tr>'
            print '<td><a href="http://en.wikipedia.org/wiki/' + urllib.quote(page.replace(" ", "_"), ":") + '">' + page.replace("_", " ") + '</a></td>'
            print '<td>' + formatseconds(pagescores[page][0]) + ' &mdash; <small><a href="' + timelineurl + '">(timeline)</a></small></td>'
            for user in userlist:
                print ('<td style="color:blue;">' if pagescores[page][1] == user else '<td>') + str(len([p for p in useredits[user] if p[0]==page])) + '</td>'
            print '</tr>'
            rowcounter += 1

        print '</tbody></table>'
        print '<br><a href="editorinteract.html"><small>&larr;New search</small></a>'
        print '<br><small>Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Scottywong">User talk:Scottywong</a></small><br>'
        print '<br><small>Elapsed time: ' + str(round(time.time() - starttime,1)) + " seconds.<br>"
        print "</BODY>\n</HTML>"
    except SystemExit:
        sys.exit(0)
    except:
        print sys.exc_info()[0]
        print "<br>"
        print traceback.print_exc(file=sys.stdout)
        print "<br>"

def formatdate(ts): #formats timestamp into datetime object
    return datetime(int(ts[:4]), int(ts[4:6]), int(ts[6:8]), int(ts[8:10]), int(ts[10:12]), int(ts[12:14]))

def prettydate(t):
    return datetime.strptime(t, "%Y%m%d").strftime("%B %d, %Y")

def formatseconds(s):
    if s < 60:
        return str(int(s)) + " second" + ("" if int(s)==1 else "s")
    if s < 3600:
        return str(int(round(s/60,0))) + " minute" + ("" if int(round(s/60,0))==1 else "s")
    if s < 86400:
        return str(int(round(s/3600,0))) + " hour" + ("" if int(round(s/3600,0))==1 else "s")
    return str(int(round(s/86400,0))) + " day" + ("" if int(round(s/86400,0))==1 else "s")

def unescape(s):
    p = htmllib.HTMLParser(None)
    p.save_bgn()
    p.feed(s)
    return p.save_end()

def errorout(errorstr):
    print "ERROR: " + errorstr + "<br><br>Please try again.<br>"
    print '<br><small>Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Scottywong">User talk:Scottywong</a></small><br>'
    print "</div></BODY>\n</HTML>"
    sys.exit(0)

main()
