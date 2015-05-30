#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
import sys
import os
import traceback
import cgi
from datetime import *
import urllib

nslookup = {0:"", 1:"Talk:", 2:"User:", 3:"User talk:", 4:"Wikipedia:", 5:"Wikipedia talk:", 6:"File:", 7:"File talk:", 8:"MediaWiki:", 9:"MediaWiki talk:", 10:"Template:", 11:"Template talk:", 12:"Help:", 13:"Help talk:", 14:"Category:", 15:"Category talk:", 100:"Portal:", 101:"Portal talk:", 108:"Book:", 109:"Book talk:", 446:"Education Program", 447:"Education Program talk", 710:"TimedText", 711:"TimedText talk", 828:"Module", 829:"Module talk"}
nsrevlookup = dict((v,k) for k,v in nslookup.iteritems())
del nsrevlookup['']
nsrevlookup["WP:"] = 4
nsrevlookup["WT:"] = 5

def main():
    global nslookup
    global nsrevlookup

    try:
        print """<!doctype html>
<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
<LINK href="greyscale.css" rel="stylesheet" type="text/css">
<LINK href="menubar3.css" rel="stylesheet" type="text/css">
<TITLE>Editor Interaction Analyzer - Timeline</TITLE>
</HEAD>
<BODY id="yes">
<script type="text/javascript" src="/menubar.js"></script>
<br>
<div id="globalWrapper">
<H1>Editor Interaction Analyzer - Timeline</H1>"""

        form = cgi.FieldStorage()

        userlist = []

        if os.environ["REMOTE_ADDR"].startswith("89.151.116.5"):
            errorout("Your IP address has been flagged for potential abuse.  Please post a message to User talk:Scottywong on the English Wikipedia, or alternatively send an email to snottywong.wiki@gmail.com to prove that you are a human, and to explain why you've been consistently making so many queries on this tool.")


        for usernum in range(1,11):
            if ("user" + str(usernum)) in form:
                u = form[("user" + str(usernum))].value.replace("_", " ").strip()
                u = u[0].capitalize() + u[1:]
                userlist.append(u)
        
        if len(userlist) < 2:
            errorout("At least two users must be specified.")

        if "page" in form:
            page = form["page"].value
            page = urllib.unquote(page.replace("_", " ")).strip()
        else:
            errorout("Missing required parameter: page.")

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

        if startdate and enddate:
            if int(startdate) >= int(enddate):
                errorout("Start date cannot be greater than end date.")



        f = open("editorinteractlog.txt", "a")
        f.write("<log><ip>" + os.environ["REMOTE_ADDR"] + "</ip><type>timeline</type>" +
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
                "<timestamp>" + datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</timestamp>" + (("<startdate>" + startdate + "</startdate>") if startdate else "") + (("<enddate>" + enddate + "</enddate>") if enddate else "") + "<page>" + page + "</page></log>\n")
        f.close()

        if startdate and not enddate:
            print "<br>Only displaying edits from " + prettydate(startdate) + " and later.<br>"
        if enddate and not startdate:
            print "<br>Only displaying edits from " + prettydate(enddate) + " and earlier.<br>"
        if startdate and enddate:
            print "<br>Only displaying edits from " + prettydate(startdate) + " to " + prettydate(enddate) + ".<br>"

        ns = extractns(page)
        if ns:
            pagewons = page[page.find(":")+1:].replace(" ", "_")
        else:
            pagewons = page.replace(" ", "_")

        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()

        querystr = "SELECT rev_user_text, rev_timestamp, rev_minor_edit, rev_id, rev_comment FROM revision JOIN page ON rev_page=page_id WHERE rev_deleted=0 AND page_title=%s AND page_namespace=%s AND ("
        queryparams = (pagewons, ns)

        for user in userlist:
            querystr += " rev_user_text=%s"
            queryparams += (user,)
            if user == userlist[-1]:
                querystr += ")"
            else:
                querystr += " OR"

        if startdate:
            querystr += " AND rev_timestamp > %s"
            queryparams += (startdate + "000000",)
        if enddate:
            querystr += " AND rev_timestamp < %s"
            queryparams += (enddate + "235959",)

        querystr += " ORDER BY rev_timestamp DESC LIMIT 1000;"

        cursor.execute(querystr, queryparams)
        revisions = cursor.fetchall()

        lasteditor = None
        lastedittime = None
        print "<br><ul>"
        for rev in revisions:
            revid = str(rev[3])
            timestamp = formatdate(rev[1])
            timestamp_dt = datetime(int(rev[1][:4]), int(rev[1][4:6]), int(rev[1][6:8]), int(rev[1][8:10]), int(rev[1][10:12]), int(rev[1][12:14]))
            minoredit = rev[2]
            comment = rev[4].replace("[[WP:AES|←]]", "←")
            urltitle = urllib.quote(page.replace(" ", "_"),":")
            user = rev[0]
            if user != lasteditor and lasteditor != None:
                print '<li style="list-style:none;color:#f33"><small>  ... ' + formatseconds((lastedittime - timestamp_dt).total_seconds()) + ' ...</small></li>'
            lasteditor = user
            lastedittime = timestamp_dt
            print '<li><b>' + user + '</b>&nbsp;&mdash;&nbsp;<a href="http://en.wikipedia.org/w/index.php?title=' + urltitle + '&oldid=' + revid + '">' + timestamp + '</a> (<a href="http://en.wikipedia.org/w/index.php?title=' + urltitle + '&diff=prev&oldid=' + revid + '">diff</a> | <a href="http://en.wikipedia.org/w/index.php?title=' + urltitle + '&action=history">hist</a>) ' + ("<b>m</b>" if minoredit else "") + ' <a href="http://en.wikipedia.org/wiki/' + urltitle + '">' + escapehtml(page) + '</a> ' + (('(<span class="comment">' + fmtcmt(escapehtml(comment)) + '</span>)') if comment else '') + '</li>'
        print "</ul>"
        
        print '<br><br><small>Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Snottywong">User talk:Snottywong</a></small><br>'
        print "</div>\n</BODY>\n</HTML>"
    except SystemExit:
        sys.exit(0)
    except:
        print sys.exc_info()[0]
        print "<br>"
        print traceback.print_exc(file=sys.stdout)
        print "<br>"

def formatdate(ts): #formats timestamp into text
    d = datetime(int(ts[:4]), int(ts[4:6]), int(ts[6:8]), int(ts[8:10]), int(ts[10:12]), int(ts[12:14]))
    return d.strftime("%H:%M, %B %d, %Y")

def prettydate(t):
    return datetime.strptime(t, "%Y%m%d").strftime("%B %d, %Y")

def extractns(p):   #returns namespace number of article
    global nsrevlookup
    for i in nsrevlookup:
        if p.startswith(i):
            return nsrevlookup[i]
            break
    return 0

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

def formatseconds(s):
    if s < 60:
        return str(int(s)) + " second" + ("" if int(s)==1 else "s")
    if s < 3600:
        return str(int(round(s/60,0))) + " minute" + ("" if int(round(s/60,0))==1 else "s")
    if s < 86400:
        return str(int(round(s/3600,0))) + " hour" + ("" if int(round(s/3600,0))==1 else "s")
    return str(int(round(s/86400,0))) + " day" + ("" if int(round(s/86400,0))==1 else "s")

def errorout(errorstr): #prints error string and exits
    print "ERROR: " + errorstr + "<br><br>Please try again.<br>"
    print "</div>\n</BODY>\n</HTML>"
    sys.exit(0)

main()
