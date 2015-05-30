#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
import sys
import os
import traceback
import cgi
import datetime
import time
import urllib
import htmllib
import re

starttime = time.time()
maxsearch = 100     #default number of edits to return
MAXLIMIT = 500      #max number of edits to return, even if the user asks for more
nslookup = {0:"", 1:"Talk:", 2:"User:", 3:"User talk:", 4:"Wikipedia:", 5:"Wikipedia talk:", 6:"File:", 7:"File talk:", 8:"MediaWiki:", 9:"MediaWiki talk:", 10:"Template:", 11:"Template talk:", 12:"Help:", 13:"Help talk:", 14:"Category:", 15:"Category talk:", 100:"Portal:", 101:"Portal talk:", 108:"Book:", 109:"Book talk:", 446:"Education Program", 447:"Education Program talk", 710:"TimedText", 711:"TimedText talk", 828:"Module", 829:"Module talk"}
nsrevlookup = dict((v,k) for k,v in nslookup.iteritems())
del nsrevlookup['']
nsrevlookup["WP:"] = 4

def main():
    global starttime
    global maxsearch
    global MAXLIMIT
    print """<!doctype html>
<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html;charset=utf-8" >
<LINK href="menubar3.css" rel="stylesheet" type="text/css">
<TITLE>Recent changes search results</TITLE>
</HEAD>
<BODY id="yes">
<script type="text/javascript" src="/menubar.js"></script>
<br>
<div id="globalWrapper">
<a href="rcsearch.html"><small>&larr;New search</small></a>
<br><br>
"""
    try:
        if os.environ["REMOTE_ADDR"].startswith("89.151.116.5"):
            errorout("Your IP address has been flagged for potential abuse.  Please post a message to User talk:Scottywong on the English Wikipedia, or alternatively send an email to snottywong.wiki@gmail.com to prove that you are a human, and to explain why you've been consistently making so many queries on this tool.")
        form = cgi.FieldStorage()
        timestamp = form["ts"].value.strip() if "ts" in form else None
        timestampcomp = form["tscomp"].value.strip() if "tscomp" in form else None  #0=greater than  1=less than  2=equal to
        username = form["u"].value.strip() if "u" in form else None
        usernamecomp = form["ucomp"].value.strip() if "ucomp" in form else None     #0=not equal to  1=equal to
        title = form["t"].value.strip() if "t" in form else None
        titlewc = form["tw"].value.strip() if "tw" in form else None                #0=no wildcard  1=wildcard
        editsum = form["es"].value.strip() if "es" in form else None
        editsumwc = form["esw"].value.strip() if "esw" in form else None
        editsumcomp = form["escomp"].value.strip() if "escomp" in form else None    #0=contains  1=equals  2=does not contain
        #editsumsect = form["essect"].value.strip() if "essect" in form else None   #Removed, not practical
        minor = form["m"].value.strip() if "m" in form else None                    #0=flag not set  1=flag set
        bot = form["b"].value.strip() if "b" in form else None
        newpage = form["n"].value.strip() if "n" in form else None
        size = form["size"].value.strip() if "size" in form else None
        sizecomp = form["sizecomp"].value.strip() if "sizecomp" in form else None
        sizeabs = form["sizeabs"].value.strip() if "sizeabs" in form else None      #0=no abs  1=abs
        usertype = form["usertype"].value.strip() if "usertype" in form else None   #0=all users, 1=logged-in editors, 2=anonymous editors
        rev = form["rev"].value.strip() if "rev" in form else None
        if "max" in form:
            try:
                maxsearch = min(MAXLIMIT, int(form["max"].value.strip()))
            except:
                maxsearch = 100

        f = open("rcsearchlog.txt", "a")
        f.write("<log><ip>" + os.environ["REMOTE_ADDR"] + "</ip>" +
                "<timestamp>" + datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</timestamp>" +
                ("<ts>" + timestamp + "</ts>" if timestamp else "") +
                ("<tscomp>" + timestampcomp + "</tscomp>" if timestampcomp else "") +
                ("<user>" + username + "</user>" if username else "") +
                ("<usercomp>" + usernamecomp + "</usercomp>" if usernamecomp else "") +
                ("<title>" + title + "</title>" if title else "") +
                ("<titlewc>" + titlewc + "</titlewc>" if titlewc else "") +
                ("<editsum>" + editsum + "</editsum>" if editsum else "") +
                ("<editsumcomp>" + editsumcomp + "</editsumcomp>" if editsum else "") +
                ("<minor>" + minor + "</minor>" if minor else "") +
                ("<bot>" + bot + "</bot>" if bot else "") +
                ("<newpage>" + newpage + "</newpage>" if newpage else "") +
                ("<size>" + size + "</size>" if size else "") +
                ("<sizecomp>" + sizecomp + "</sizecomp>" if sizecomp else "") +
                ("<sizeabs>" + sizeabs + "</sizeabs>" if sizeabs else "") +
                ("<usertype>" + usertype + "</usertype>" if usertype else "") +
                ("<rev>" + rev + "</rev>" if rev else "") +
                ("<max>" + str(maxsearch) + "</max>" if maxsearch else "") +
                "</log>\n")
        f.close()

        #Sanitize parameters
        sanitize(timestampcomp, ["0", "1", "2"], "timestampcomp")
        sanitize(usernamecomp, ["0", "1"], "usernamecomp")
        sanitize(titlewc, ["0", "1"], "titlewc")
        sanitize(editsumwc, ["0", "1"], "editsumwc")
        sanitize(editsumcomp, ["0", "1", "2"], "editsumcomp")
        #sanitize(editsumsect, ["0", "1"], "editsumsect")   Removed, not practical
        sanitize(minor, ["0", "1"], "minor")
        sanitize(bot, ["0", "1"], "bot")
        sanitize(newpage, ["0", "1"], "newpage")
        sanitize(sizecomp, ["0", "1", "2"], "sizecomp")
        sanitize(sizeabs, ["0", "1"], "sizeabs")
        sanitize(usertype, ["0", "1", "2"], "usertype")
        sanitize(rev, ["0", "1"], "rev")

        titlewc = ("0" if titlewc==None else titlewc)
        editsumwc = ("0" if editsumwc==None else editsumwc)
        sizeabs = ("0" if sizeabs==None else sizeabs)

        rawtimestamp = timestamp    #for display purposes, we need the unmodified timestamp value
        
        if timestamp:
            if len(timestamp) > 14 or len(timestamp) < 4:
                errorout("Invalid timestamp format.  Timestamps should be formatted as YYYYMMDDHHMMSS, for example: 20130102113041.  Incomplete timestamps are ok (e.g. 20130102), but at least a year must be specified.")
            try:
                int(timestamp)
            except ValueError:
                errorout("Timestamp must be a number.")
            if timestampcomp in ["0", "1"]:
                timestamp = timestamp.ljust(14, "0")
            if timestampcomp == "2" and len(timestamp) < 14:
                timestamp += "%"    #If not a full timestamp and timestampcomp is "equals", then add a wildcard character to the end
        if username:
            if username.lower().startswith("user:"):
                username = username[5:]
        if title:
            try:
                title = urllib.unquote(title)
                title = title.replace("_", " ")
                try:
                    title = unicode(title, "utf-8")
                except UnicodeDecodeError:
                    title = unicode(title, "latin-1")
                if any(c in title for c in "#<>[]|{}_"):
                    errorout("Invalid page title.")
                title = title[0].capitalize() + title[1:]
                if title.lower().startswith("wp:"):
                    title = "Wikipedia:" + title[3:]
                title = title.replace(" ", "_").strip()
                title = title.encode("utf-8")
                namespace = extractns(title)
            except:
                errorout("Unable to parse page name.")
        else:
            namespace = None
        if size:
            try:
                size = int(size)
            except ValueError:
                errorout("Edit size must be a number.")

        #Construct query string
        querystr = "SELECT rc_timestamp, rc_user_text, rc_namespace, rc_title, rc_comment, rc_minor, rc_bot, rc_new, rc_this_oldid, rc_last_oldid, rc_old_len, rc_new_len FROM recentchanges WHERE rc_deleted=0 and rc_log_type is NULL"
        queryparams = []
        if timestamp:
            if timestampcomp == "0":    #greater than
                querystr += " AND rc_timestamp>%s"
                queryparams.append(timestamp)
            elif timestampcomp == "1":  #less than
                querystr += " AND rc_timestamp<%s"
                queryparams.append(timestamp)
            elif timestampcomp == "2":  #equal to
                if "%" in timestamp:
                    querystr += " AND rc_timestamp LIKE %s"
                else:
                    querystr += " AND rc_timestamp=%s"
                queryparams.append(timestamp)
        if username:
            if usernamecomp == "0":     #not equal to
                querystr += " AND NOT rc_user_text=%s"
                queryparams.append(username)
            elif usernamecomp == "1":   #equal to
                querystr += " AND rc_user_text=%s"
                queryparams.append(username)
        if title:
            if namespace:
                querytitle = title[title.find(":")+1:]
            else:
                querytitle = title
            if titlewc == "0":      #no wildcards
                querystr += " AND rc_namespace=%s AND rc_title=%s"
                queryparams.append(namespace)
                queryparams.append(querytitle)
            elif titlewc == "1":    #wildcards
                querystr += " AND rc_namespace=%s AND rc_title LIKE %s"
                queryparams.append(namespace)
                queryparams.append(querytitle.replace("%", "\%").replace("_", "\_").replace("*", "%"))
        if editsum:
            editsumtemp = editsum
            if editsumwc == "1" or editsumcomp == "0" or editsumcomp == "2":    #escape special characters if wildcards are in use
                editsumtemp = editsumtemp.replace("%", "\%").replace("_", "\_").replace("*", "%")
            if editsumcomp == "0" or editsumcomp == "2":  #contains
                editsumtemp = "%" + editsumtemp + "%"
            if editsumwc == "0" and editsumcomp == "1":     #if no wildcards and equals, don't use LIKE in query string
                querystr += " AND rc_comment=%s"
                queryparams.append(editsumtemp)
            elif editsumcomp == "2":    #if does not contain, use NOT LIKE
                querystr += " AND rc_comment NOT LIKE %s"
                queryparams.append(editsumtemp)
            else:   #otherwise, if wildcards are used OR contains is used, use LIKE in the query string
                querystr += " AND rc_comment LIKE %s"
                queryparams.append(editsumtemp)
        if minor:
            querystr += " AND rc_minor=%s"
            queryparams.append(int(minor))
        if bot:
            querystr += " AND rc_bot=%s"
            queryparams.append(int(bot))
        if newpage:
            querystr += " AND rc_new=%s"
            queryparams.append(int(newpage))
        if size:
            if sizecomp == "0": #greater than
                querystr += (" AND ABS" if sizeabs=="1" else " AND ") + "(rc_new_len - rc_old_len)>%s"
            if sizecomp == "1": #less than
                querystr += (" AND ABS" if sizeabs=="1" else " AND ") + "(rc_new_len - rc_old_len)<%s"
            if sizecomp == "2": #equal to
                querystr += (" AND ABS" if sizeabs=="1" else " AND ") + "(rc_new_len - rc_old_len)=%s"
            queryparams.append(size)
        if usertype:
            if usertype == "1":
                querystr += " AND rc_user>0"
            if usertype == "2":
                querystr += " AND rc_user=0"
        if rev == "1":
            querystr += " ORDER BY rc_timestamp ASC"
        else:
            querystr += " ORDER BY rc_timestamp DESC"
        querystr += " LIMIT %s;"
        queryparams.append(maxsearch)

        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()

        cursor.execute(querystr, tuple(queryparams))
        results = cursor.fetchall()


        print '<form action="cgi-bin/rcsearch.cgi" method="get">'
        print 'Only show edits that <select name="ucomp"><option value="1"' + (' selected' if usernamecomp == '1' else '') + '>were made by</option><option value="0"' + (' selected' if usernamecomp == '0' else '') + '>were not made by</option></select> User:<input type="text" name="u" size="20"' + (' value=' + username if username else '') + ' /><br />'
        print 'Only show edits to this page: <input type="text" name="t" size="40"' + (' value=' + title if title else '') + ' /> <input type="checkbox" name="tw" value="1"' + (' checked' if titlewc == '1' else '') + ' />Interpret * as a wildcard character<br />'
        print 'Only show edits whose timestamp <select name="tscomp"><option value="0"' + (' selected' if timestampcomp == '0' else '') + '>is greater than (newer than)</option><option value="1"' + (' selected' if timestampcomp == '1' else '') + '>is less than (older than)</option><option value="2"' + (' selected' if timestampcomp == '2' else '') + '>is equal to</option></select> <input type="text" name="ts" size="14"' + (' value=' + rawtimestamp if timestamp else '') + ' /> (YYYYMMDDHHMMSS)<br />'
        print 'Only show edits whose edit summaries <select name="escomp"><option value="0"' + (' selected' if editsumcomp == '0' else '') + '>contain</option><option value="1"' + (' selected' if editsumcomp == '1' else '') + '>exactly equal</option><option value="2"' + (' selected' if editsumcomp == '2' else '') + '>do not contain</option></select> the text: <input type="text" name="es" size="25"' + (' value=' + editsum if editsum else '') + ' /> <input type="checkbox" name="esw" value="1"' + (' checked' if editsumwc == '1' else '') + ' />Interpret * as a wildcard character<br />'
        print 'Only show edits which changed the page size by <select name="sizecomp"><option value="0"' + (' selected' if sizecomp == '0' else '') + '>more than</option><option value="1"' + (' selected' if sizecomp == '1' else '') + '>less than</option><option value="2"' + (' selected' if sizecomp == '2' else '') + '>exactly</option></select> <input type="text" name="size" size="8"' + (' value=' + str(size) if size else '') + ' /> bytes  <input type="checkbox" name="sizeabs" value="1"' + (' checked' if sizeabs == '1' else '') + ' />Absolute value (disregard positive/negative)<br />'
        print 'Show edits made by <select name="usertype"><option value="0"' + (' selected' if usertype == '0' else '') + '>all user types</option><option value="1"' + (' selected' if usertype == '2' else '') + '>only logged-in editors</option><option value="2"' + (' selected' if usertype == '2' else '') + '>only anonymous editors</option></select><br /><br />'
        print '<input type="checkbox" name="m" value="1"' + (' checked' if minor == '1' else '') + ' />Only show minor edits<br />'
        print '<input type="checkbox" name="b" value="1"' + (' checked' if bot == '1' else '') + ' />Only show bot edits<br />'
        print '<input type="checkbox" name="n" value="1"' + (' checked' if newpage == '1' else '') + ' />Only show edits that created a new page<br /><br />'
        print 'Show a maximum of <input type="text" name="max" maxlength="3" size="5" value="' + str(maxsearch) + '" /> edits<br />'
        print '<input type="checkbox" name="rev" value="1"' + (' checked' if rev == '1' else '') + ' />Show edits in reverse order (oldest first)<br /><br />'
        print '<input type="submit" value="Submit" />'
        print '</form>'

        
        cursor.execute("SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(MAX(rc_timestamp)) FROM recentchanges;")
        replag = int(cursor.fetchall()[0][0])
        if replag > 30:
            print "<br><b>Edits that were made in the last " + formatreplag(replag) + " may not be shown below due to replication lag.</b><br><br>"

        print "<ul>"
        for i in results:
            printedit(i)
        print "</ul>"

        elapsed = time.time() - starttime
        print "<br><br><small>Elapsed time: " + str(round(elapsed, 2)) + " seconds.<br>\n"
        print datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</small><br>"
        print '<br><small>Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Snottywong">User talk:Snottywong</a></small><br>'
        print '<a href="rcsearch.html"><small>&larr;New search</small></a>'
        print "</div>\n</BODY>\n</HTML>"

    except SystemExit:
        pass
    except:
        errorout("Unhandled exception.<br><br>" + traceback.print_exc(file=sys.stdout))


def printedit(edit):    #Print out a line for each edit
    global nslookup
    #rc_timestamp, rc_user_text, rc_namespace, rc_title, rc_comment, rc_minor, rc_bot, rc_new, rc_this_oldid, rc_last_oldid, rc_old_len, rc_new_len
    timestamp = formatdate(edit[0])
    user = edit[1]
    namespace = edit[2]
    title = edit[3]
    editsummary = edit[4]
    minor = edit[5]
    bot = edit[6]
    newpage = edit[7]
    currentrevid = edit[8]
    lastrevid = edit[9]
    sizechange = int(edit[11]) - int(edit[10])
    fulltitle = (nslookup[namespace] + title).replace(" ", "_")

    print '<li><a href="http://en.wikipedia.org/w/index.php?title=' + fulltitle + '&oldid=' + str(currentrevid) + '">' + timestamp + '</a> (<a href="http://en.wikipedia.org/w/index.php?title=' + fulltitle + '&diff=' + str(currentrevid) + '&oldid=' + str(lastrevid) + '">diff</a> | <a href="http://en.wikipedia.org/w/index.php?title=' + fulltitle + '&action=history">hist</a>) ' + ("<b>N</b>" if newpage else "") + ("<b>m</b>" if minor else "") + ("<b>b</b>" if bot else "") + ' <a href="http://en.wikipedia.org/wiki/' + fulltitle + '">' + fulltitle.replace("_", " ") + '</a> . . ' + fmtsizechange(sizechange) + ' . . ' + '<a href="http://en.wikipedia.org/wiki/User:' + user.replace(" ", "_") + '">' + user + '</a>' + ' (<a href="http://en.wikipedia.org/wiki/User_talk:' + user.replace(" ", "_") + '">talk</a> | ' + ' <a href="http://en.wikipedia.org/wiki/Special:Contributions/' + user.replace(" ", "_") + '">contribs</a>) ' + (('(<span class="comment">' + fmtcmt(editsummary) + '</span>)') if editsummary else '') + '</li>'


def formatdate(ts): #formats timestamp into text
    d = datetime.datetime(int(ts[:4]), int(ts[4:6]), int(ts[6:8]), int(ts[8:10]), int(ts[10:12]), int(ts[12:14]))
    return d.strftime("%H:%M, %B %d, %Y")

def fmtcmt(comment):    #adds an autocomment span into the comment if section header detected
    comment = comment.replace("[[WP:AES|←]]", "←")
    if "/*" in comment and "*/" in comment:
        return comment.replace("/*", '<span class="autocomment">/*', 1).replace("*/", "*/</span>", 1)
    return escapehtml(comment)

def fmtsizechange(s):  #format edit's size change text
    if s<0:
        return ('<strong' if s<=-500 else '<span') + ' style="color:#8b0000">(' + str(s) + (')</strong>' if s<=-500 else ')</span>')
    if s==0:
        return '<span style="color:#aaa">(0)</span>'
    if s>0:
        return ('<strong' if s>=500 else '<span') + ' style="color:#006400">(+' + str(s) + (')</strong>' if s>=500 else ')</span>')

def sanitize(value, validvalues, varname):  #Check that the value is valid, if not errorout
    if value==None or value in validvalues:
        return
    errorout("Invalid value for parameter: " + varname)

def extractns(p):   #returns namespace number of article
    global nsrevlookup
    p = p.replace("_", " ").replace("+", " ")
    for i in nsrevlookup:
        if p.startswith(i):
            return nsrevlookup[i]
            break
    return 0

def formatreplag(r):    #format seconds/minutes/hours/days
    if r<120:
        return str(r) + " seconds"
    if r<7200:      #120 minutes
        return str(int(r/60)) + " minutes"
    if r<259200:    #72 hours
        return str(int(r/3600)) + " hours"
    return str(int(r/86400)) + " days"

def escapehtml(s):  #escapes various characters to prevent attacks
    s = s.replace("&", "&amp;") # Must be first
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', '&quot;')
    return s

def errorout(errorstr): #prints error string and exits
    print "ERROR: " + errorstr + "<br><br>Please try again.<br>"
    print "</div>\n</BODY>\n</HTML>"
    sys.exit(0)

main()
