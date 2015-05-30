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
username = ""
maxsearch = 100     #default number of edits to return
maxlimit = 500      #max number of edits to return, even if the user asks for more
startdate = ""
pagetitle = ""
namespace = 0
redirect = False    #if true, don't try to resolve redirects
wildcards = False   #if true, allow wildcards in the page name
casesensitive = False   #if true, page name with wildcards should be case sensitive (only used with wildcards)

nslookup = {0:"", 1:"Talk:", 2:"User:", 3:"User talk:", 4:"Wikipedia:", 5:"Wikipedia talk:", 6:"File:", 7:"File talk:", 8:"MediaWiki:", 9:"MediaWiki talk:", 10:"Template:", 11:"Template talk:", 12:"Help:", 13:"Help talk:", 14:"Category:", 15:"Category talk:", 100:"Portal:", 101:"Portal talk:", 108:"Book:", 109:"Book talk:"}
nsrevlookup = dict((v,k) for k,v in nslookup.iteritems())
del nsrevlookup['']
nsrevlookup["WP:"] = 4

def main():
    global username
    global maxsearch
    global maxlimit
    global startdate
    global pagetitle
    global namespace
    global redirect
    global wildcards
    global casesensitive

    print """<!doctype html>
<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html;charset=utf-8" >
<LINK href="menubar3.css" rel="stylesheet" type="text/css">
<TITLE>User contibution search results</TITLE>
</HEAD>
<BODY id="yes">
<script type="text/javascript" src="/menubar.js"></script>
<br>
<div id="globalWrapper">
<a href="usersearch.html"><small>&larr;New search</small></a>
<br><br>
"""

    try:
        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        form = cgi.FieldStorage()
        if "name" not in form:
            errorout("No name entered.")
        if "page" not in form:
            errorout("No page entered.")
        if "max" in form:
            try:
                maxsearch = min(maxlimit, int(form['max'].value))
            except:
                maxsearch = 100
        if "noredirect" in form:
            try:
                retemp = form['noredirect'].value
                if retemp.lower() == "true":
                    redirect = True
            except:
                redirect = False
        if "wildcards" in form:
            try:
                wildcards = form['wildcards'].value
                if wildcards.lower() in ["true", "1"]:
                    wildcards = True
                    if "casesensitive" in form:
                        casesensitive = form['casesensitive'].value
                        if casesensitive.lower() in ["true", "1"]:
                            casesensitive = True
                        else:
                            casesensitive = False
                else:
                    wildcards = False
            except:
                wildcards = False
                casesensitive = False
        if "page" in form:
            try:
                pagetitle = form['page'].value
                if not redirect and not wildcards:  #resolve redirects unless specifically told not to, or if using wildcards
                    retest = findredirect(pagetitle)
                    if retest:
                        pagetitle = retest
                pagetitle = urllib.unquote(pagetitle)
                pagetitle = pagetitle.replace("_", " ")
                try:pagetitle = unicode(pagetitle, 'utf-8')
                except UnicodeDecodeError:pagetitle = unicode(pagetitle, 'latin-1')
                if any(c in pagetitle for c in "#<>[]|{}_"):
                    errorout("Invalid page title.")
                pagetitle = pagetitle[0].capitalize() + pagetitle[1:]
                if pagetitle.startswith("WP:") or pagetitle.startswith("Wp:"):
                    pagetitle = "Wikipedia:" + pagetitle[3:]
                pagetitle = pagetitle.replace(" ", "_").strip()
                pagetitle = pagetitle.encode('utf-8')
                #print pagetitle + "<br>"
                namespace = extractns(pagetitle)
            except:
                errorout("Unable to parse page name.")
        if "startdate" in form:
            try:
                startdate = form['startdate'].value
                startdate = startdate.ljust(14, "0")
                if len(startdate) != 14 or int(startdate) < 20000000000000 or int(startdate) > 20150000000000:
                    startdate = None
            except:
                pass
        username = form['name'].value.replace("_", " ").replace("+", " ").strip()
        username = username[0].capitalize() + username[1:]
        if username.lower().startswith("user:"):
            username = username[5:]
        #username = username[0].capitalize() + username[1:]
        f = open("usersearchlog.txt", "a")
        f.write("<log><ip>" + os.environ["REMOTE_ADDR"] + "</ip><username>" + username + "</username><pagetitle>" + pagetitle + "</pagetitle><max>" + str(maxsearch) + "</max><timestamp>" + datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</timestamp>" + ("<startdate>" + startdate + "</startdate>" if startdate else "") + ("<wildcards>true</wildcards>" if wildcards else "") + ("<cs>true</cs>" if casesensitive else "") + "</log>\n")
        f.close()
        if namespace:
            pagewons = pagetitle[pagetitle.find(":")+1:]
        else:
            pagewons = pagetitle
        cursor = db.cursor()

        querystr = "SELECT rev_id,rev_timestamp,rev_minor_edit,rev_comment,page_title\n"
        querystr += "FROM revision JOIN page ON rev_page=page_id\n"
        querystr += "WHERE rev_deleted=0\n"
        querystr += "AND rev_user_text=%s\n"
        querylist = [username]
        querystr += "AND page_namespace=%s\n"
        querylist.append(namespace)
        if wildcards:
            if casesensitive:
                querystr += "AND page_title LIKE %s\n"
                querylist.append(pagewons.replace("*", "%"))
            else:
                querystr += "AND CAST(page_title AS CHAR CHARACTER SET utf8) LIKE %s\n"
                querylist.append(pagewons.replace("*", "%"))
        else:
            querystr += "AND page_title=%s\n"
            querylist.append(pagewons)
        if startdate:
            querystr += "AND rev_timestamp<=%s\n"
            querylist.append(startdate)
        querystr += "ORDER BY rev_timestamp DESC\n"
        querystr += "LIMIT %s;"
        querylist.append(maxsearch)

        cursor.execute(querystr, tuple(querylist))
        results = cursor.fetchall()

        totalpageedits = 0
        if not wildcards:
            cursor.execute("""
SELECT COUNT(*)
FROM revision
JOIN page ON rev_page=page_id
WHERE rev_user_text=%s
AND page_title=%s
AND page_namespace=%s
AND rev_deleted=0;""",
                       (username, pagewons, namespace)
                       )
            totalcount = cursor.fetchall()[0][0]
            cursor.execute("""
SELECT COUNT(*)
FROM revision
JOIN page ON rev_page=page_id
WHERE page_title=%s
AND page_namespace=%s
AND rev_deleted=0;""",
                           (pagewons, namespace)
                           )
            totalpageedits = cursor.fetchall()[0][0]
        else:
            querystr = querystr.replace("SELECT rev_id,rev_timestamp,rev_minor_edit,rev_comment,page_title\n", "SELECT COUNT(*)\n")
            querystr = querystr.replace("ORDER BY rev_timestamp DESC\nLIMIT %s", "")
            querylist = querylist[:-1]
            cursor.execute(querystr, tuple(querylist))
            totalcount = cursor.fetchall()[0][0]
                        
        db.close()

        print '<form action="cgi-bin/usersearch.cgi" method="get">'
        print 'Username:&nbsp;<input type="text" name="name" value="' + username.replace('"', '&quot;') + '" />&nbsp;&nbsp;&nbsp;Page:&nbsp;<input type="text" name="page" size="40" value="' + pagetitle.replace('"', '&quot;').replace("_", " ") + '" />&nbsp;&nbsp;&nbsp;Max&nbsp;edits:&nbsp;<input type="text" name="max" maxlength="3" size="5" value="' + str(maxsearch) + '" />'            
        print '<br><input type="checkbox" name="noredirect" value="true" ' + ("checked" if redirect else "") + ">Don't resolve redirects<br>"
        print '<input type="checkbox" name="wildcards" value="true"' + ("checked" if wildcards else "") + '>Allow wildcards in page title (*)<br>'
        print '<input type="checkbox" name="casesensitive" value="true"' + ("checked" if casesensitive else "") + '>Page title is case sensitive (only applies when wildcards are used)<br><br>'
        print """<input type="submit" value="Submit" /> 
</form>
<br>
<hr style="text-align:left;width:875px;margin-left:0">
<br>
"""
        print "Found " + str(totalcount) + " edits by User:" + escapehtml(username) + " on " + escapehtml(pagetitle).replace("_", " ")
        if totalpageedits > 0:
            print "  (" + str(round(100.0 * totalcount / totalpageedits, 2)) + "% of the total edits made to the page)"
        print "<br><br>"
        if len(results) == maxsearch:
            print '<a href="cgi-bin/usersearch.cgi?name=' + urllib.quote_plus(username) + '&max=' + str(maxsearch) + '&page=' + urllib.quote_plus(pagetitle.replace("_", " ")) + ('&noredirect=true' if redirect else '') + ('&wildcards=true' if wildcards else '') + ('&casesensitive=true' if casesensitive else '') + '&startdate=' + str(int(results[-1][1])-1) + '"><small>Next ' + str(maxsearch) + " results &rarr;</small></a><br>"

        print "<ul>"
        printtable(results)
        print "</ul>"
        
        if len(results) == maxsearch:
            print '<a href="cgi-bin/usersearch.cgi?name=' + urllib.quote_plus(username) + '&max=' + str(maxsearch) + '&page=' + urllib.quote_plus(pagetitle.replace("_", " ")) + ('&noredirect=true' if redirect else '') + ('&wildcards=true' if wildcards else '') + ('&casesensitive=true' if casesensitive else '') + '&startdate=' + str(int(results[-1][1])-1) + '"><small>Next ' + str(maxsearch) + " results &rarr;</small></a><br>"

        elapsed = time.time() - starttime
        print "<br><br><small>Elapsed time: " + str(round(elapsed, 2)) + " seconds.<br>\n"
        print datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</small><br>"
    except SystemExit:
        pass
    except:
        #errorout("Unhandled exception.<br><br>" + traceback.print_exc(file=sys.stdout))
        errorout('Unhandled exception. Please try again. If this error persists, please contact me at <a href="http://en.wikipedia.org/wiki/User_talk:Snottywong">User talk:Snottywong</a><br><br>')

def printtable(r):  #prints each edit out in an unordered list
    global pagetitle
    global namespace
    for edit in r:
        revid = str(edit[0])
        timestamp = formatdate(edit[1])
        minoredit = edit[2]
        comment = edit[3].replace("[[WP:AES|←]]", "←")
        title = nslookup[namespace] + edit[4]
        print '<li><a href="http://en.wikipedia.org/w/index.php?title=' + title + '&oldid=' + revid + '">' + timestamp + '</a> (<a href="http://en.wikipedia.org/w/index.php?title=' + title + '&diff=prev&oldid=' + revid + '">diff</a> | <a href="http://en.wikipedia.org/w/index.php?title=' + title + '&action=history">hist</a>) ' + ("<b>m</b>" if minoredit else "") + ' <a href="http://en.wikipedia.org/wiki/' + title + '">' + escapehtml(title.replace("_", " ")) + '</a> ' + (('(<span class="comment">' + fmtcmt(escapehtml(comment)) + '</span>)') if comment else '') + '</li>'
    
def formatdate(ts): #formats timestamp into text
    d = datetime.datetime(int(ts[:4]), int(ts[4:6]), int(ts[6:8]), int(ts[8:10]), int(ts[10:12]), int(ts[12:14]))
    return d.strftime("%H:%M, %B %d, %Y")

def fmtcmt(comment):    #adds an autocomment span into the comment if section header detected
    if "/*" in comment and "*/" in comment:
        return comment.replace("/*", '<span class="autocomment">/*', 1).replace("*/", "*/</span>", 1)
    return comment

def extractns(p):   #returns namespace number of article
    global nsrevlookup
    p = p.replace("_", " ").replace("+", " ")
    for i in nsrevlookup:
        if p.startswith(i):
            return nsrevlookup[i]
            break
    return 0

def escapehtml(s):  #escapes various characters to prevent attacks
    s = s.replace("&", "&amp;") # Must be first
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', '&quot;')
    return s

def unescapehtml(s):    #unescape output from API
    p = htmllib.HTMLParser(None)
    p.save_bgn()
    p.feed(s)
    return p.save_end()

def findredirect(p):    #find out if page is a redirect, if so return the redirect target, if not return original page name
    try:
        #print "Looking for redirect...<br>"
        redirecttarget = None
        u = urllib.urlopen("http://en.wikipedia.org/w/api.php?action=query&redirects=True&format=xml&titles=" + p)
        data = u.read()
        u.close()
        if "<redirects>" in data:
            #print "Found redirect<br>"
            s = re.search("<page.*?title=\"(.*?)\".*?>", data)
            if s:
                #print "Redirect is " + unescapehtml(s.group(1)) + "<br>"
                redirecttarget = unescapehtml(s.group(1))
        return redirecttarget
    except:
        return None
            

def errorout(errorstr): #prints error string and exits
    print "ERROR: " + errorstr + "<br><br>Please try again.<br>"
    print "</div>\n</BODY>\n</HTML>"
    sys.exit(0)

def fetchnamespace(sqlcursor, dbname, nsname):
    try:
        sqlcursor.execute('SELECT ns_id FROM toolserver.namespacename WHERE dbname=%s AND ns_name=%s', (dbname, nsname))
        results = cursor.fetchall()
    except:
        return 0
    if results:
        return results[0][0]
    return 0

main()
print '<br><small>Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Snottywong">User talk:Snottywong</a></small><br>'
print '<a href="usersearch.html"><small>&larr;New search</small></a>'
print "</div>\n</BODY>\n</HTML>"
