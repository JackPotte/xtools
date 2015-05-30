#!/usr/bin/env python
# -*- coding: utf-8 -*-

#To add: case-sensitive search option, allow user input of wildcards, restrict search by namespace

import MySQLdb
import sys
import os
import traceback
import cgi
import urllib
import datetime
import time

starttime = time.time()
username = ""
searchstr = ""
maxsearch = 100     #default number of edits to return
maxlimit = 500      #max number of edits to return, even if the user asks for more
startdate = ""
nosect = False      #whether or not we will be ignoring comments in /* section headers */, false by default = not ignoring section headers
casesensitive = False   #if true, search will be case sensitive
ns = None           #if not None, will only return results in specified namespace

nslookup = {0:"", 1:"Talk:", 2:"User:", 3:"User talk:", 4:"Wikipedia:", 5:"Wikipedia talk:", 6:"File:", 7:"File talk:", 8:"MediaWiki:", 9:"MediaWiki talk:", 10:"Template:", 11:"Template talk:", 12:"Help:", 13:"Help talk:", 14:"Category:", 15:"Category talk:", 100:"Portal:", 101:"Portal talk:", 108:"Book:", 109:"Book talk:"}
nsrevlookup = dict((v,k) for k,v in nslookup.iteritems())
del nsrevlookup['']

def main():
    global username
    global maxsearch
    global maxlimit
    global startdate
    global searchstr
    global nosect
    global casesensitive
    global ns

    print """<!doctype html>
<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
<LINK href="menubar3.css" rel="stylesheet" type="text/css">
<TITLE>Edit summary search results</TITLE>
</HEAD>
<BODY id="yes">
<script type="text/javascript" src="/menubar.js"></script>
<br>
<div id="globalWrapper">
<a href="commentsearch.html"><small>&larr;New search</small></a>
<br><br>"""

    try:
        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        form = cgi.FieldStorage()
        if "name" not in form:
            errorout("No name entered.")
        if "search" not in form:
            errorout("No search string entered.")
        if "max" in form:
            try:
                maxsearch = min(maxlimit, int(form['max'].value))
            except:
                maxsearch = 100
        if "startdate" in form:
            try:
                startdate = form['startdate'].value
                startdate = startdate.ljust(14, "0")
                if len(startdate) != 14 or int(startdate) < 20000000000000 or int(startdate) > 20150000000000:
                    startdate = None
            except:
                pass
        if "search" in form:
            try:
                searchstr = form['search'].value
            except:
                errorout("Unable to parse search string.")
        if "nosect" in form:
            try:
                if form['nosect'].value == "1" or form['nosect'].value.lower() == "true":
                    nosect = True
            except:
                pass
        if "casesensitive" in form:
            try:
                if form['casesensitive'].value == "1" or form['casesensitive'].value.lower() == "true":
                    casesensitive = True
            except:
                pass
        if "ns" in form:
            try:
                ns = form['ns'].value
                if ns.lower() == "none":
                    ns = None
                else:
                    ns = int(ns)
                    if ns not in [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,100,101,108,109]:
                        raise
            except:
                errorout("Invalid namespace specified.")
        username = form['name'].value.replace("_", " ").replace("+", " ")
        if username.lower().startswith("user:"):
            username = username[5:]
        #username = username[0].capitalize() + username[1:]

        if os.environ["REMOTE_ADDR"].startswith("89.151.116.5"):
            errorout("Your IP address has been flagged for potential abuse.  Please post a message to User talk:Scottywong on the English Wikipedia, or alternatively send an email to snottywong.wiki@gmail.com to prove that you are a human, and to explain why you've been consistently making so many queries on this tool.")

        f = open("commentsearchlog.txt", "a")
        f.write("<log><ip>" + os.environ["REMOTE_ADDR"] + "</ip><username>" + username + "</username><searchstr>" + searchstr + "</searchstr><max>" + str(maxsearch) + "</max><timestamp>" + datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</timestamp>" + ("<startdate>" + startdate + "</startdate>" if startdate else "") + ("<case>true</case>" if casesensitive else "") + ("<ns>" + str(ns) + "</ns>" if ns else "") + "</log>\n")
        f.close()

        cursor = db.cursor()
        querylist = []
        querystr = "SELECT rev_id,rev_timestamp,rev_minor_edit,rev_comment,page_title,page_namespace\n"
        querystr += "FROM revision JOIN page ON rev_page=page_id\n"
        
        querystr += "WHERE rev_user_text=%s\n"
        querylist.append(username)
        
        querystr += "AND rev_deleted=0\n"
        
        if casesensitive:
            querystr += "AND rev_comment LIKE %s\n"
        else:
            querystr += "AND CAST(rev_comment AS CHAR CHARACTER SET utf8) LIKE %s\n"
        querylist.append("%" + searchstr + "%")
        
        if startdate:
            querystr += "AND rev_timestamp<=%s\n"
            querylist.append(startdate)
            
        if ns != None:
            querystr += "AND page_namespace=%s\n"
            querylist.append(int(ns))
            
        querystr += "ORDER BY rev_timestamp DESC\n"
        
        querystr += "LIMIT %s;"
        querylist.append(maxsearch)


        cursor.execute(querystr, tuple(querylist))
        
        #Old query structure, doesn't support casesensitive or ns

#        if startdate:
#            cursor.execute("""
#SELECT rev_id,rev_timestamp,rev_minor_edit,rev_comment,page_title,page_namespace
#FROM revision JOIN page ON rev_page=page_id
#WHERE rev_user_text=%s
#AND CAST(rev_comment AS CHAR CHARACTER SET utf8) LIKE %s
#AND rev_deleted=0
#AND rev_timestamp<=%s
#ORDER BY rev_timestamp DESC
#LIMIT %s;""",
#            (username, "%" + searchstr + "%", startdate, maxsearch)
#                           )
#        else:
#            cursor.execute("""
#SELECT rev_id,rev_timestamp,rev_minor_edit,rev_comment,page_title,page_namespace
#FROM revision JOIN page ON rev_page=page_id
#WHERE rev_user_text=%s
#AND CAST(rev_comment AS CHAR CHARACTER SET utf8) LIKE %s
#AND rev_deleted=0
#ORDER BY rev_timestamp DESC
#LIMIT %s;""",
#            (username, "%" + searchstr + "%", maxsearch)
#                           )
                           
        results = cursor.fetchall()
        db.close()
        
        print '<form action="cgi-bin/commentsearch.cgi" method="get">'
        print 'Username:&nbsp;<input type="text" name="name" value="' + username.replace('"', '&quot;') + '" />&nbsp;&nbsp;&nbsp;Search&nbsp;string:&nbsp;<input type="text" name="search" size="40" value="' + searchstr.replace('"', '&quot;') + '" />&nbsp;&nbsp;&nbsp;Max&nbsp;pages:&nbsp;<input type="text" name="max" maxlength="3" size="5" value="' + str(maxsearch) + '" />'
        print """<br><br><a href="javascript:;" onmousedown="if(document.getElementById('mydiv').style.display == 'none'){ document.getElementById('mydiv').style.display = 'block'; }else{ document.getElementById('mydiv').style.display = 'none'; }">Advanced options &darr;</a><br>"""
        print '<div id="mydiv" style="display:' + ('block' if (nosect == True or casesensitive == True or ns != None) else 'none') + '">'
        print '<br>\n<input type="checkbox" name="nosect" value="1"' + ("checked" if nosect else "") + ">Don't search within /* section headings */<br>"
        print '<input type="checkbox" name="casesensitive" value="1"' + ("checked" if casesensitive else "") + '/>Case sensitive search<br />'
        print 'Restrict search to namespace: <select name="ns">'

        print '<option value="none"' + (' selected' if ns == None else '') + '>All namespaces</option>'
        print '<option value="0"' + (' selected' if ns == 0 else '') + '>(Article)</option>'
        print '<option value="1"' + (' selected' if ns == 1 else '') + '>Talk</option>'
        print '<option value="2"' + (' selected' if ns == 2 else '') + '>User</option>'
        print '<option value="3"' + (' selected' if ns == 3 else '') + '>User talk</option>'
        print '<option value="4"' + (' selected' if ns == 4 else '') + '>Wikipedia</option>'
        print '<option value="5"' + (' selected' if ns == 5 else '') + '>Wikipedia talk</option>'
        print '<option value="6"' + (' selected' if ns == 6 else '') + '>File</option>'
        print '<option value="7"' + (' selected' if ns == 7 else '') + '>File talk</option>'
        print '<option value="8"' + (' selected' if ns == 8 else '') + '>MediaWiki</option>'
        print '<option value="9"' + (' selected' if ns == 9 else '') + '>MediaWiki talk</option>'
        print '<option value="10"' + (' selected' if ns == 10 else '') + '>Template</option>'
        print '<option value="11"' + (' selected' if ns == 11 else '') + '>Template talk</option>'
        print '<option value="12"' + (' selected' if ns == 12 else '') + '>Help</option>'
        print '<option value="13"' + (' selected' if ns == 13 else '') + '>Help talk</option>'
        print '<option value="14"' + (' selected' if ns == 14 else '') + '>Category</option>'
        print '<option value="15"' + (' selected' if ns == 15 else '') + '>Category talk</option>'
        print '<option value="100"' + (' selected' if ns == 100 else '') + '>Portal</option>'
        print '<option value="101"' + (' selected' if ns == 101 else '') + '>Portal talk</option>'
        print '<option value="108"' + (' selected' if ns == 108 else '') + '>Book</option>'
        print '<option value="109"' + (' selected' if ns == 109 else '') + '>Book talk</option>'
        print '</select>\n</div>'
        print """<input type="submit" value="Submit" /> 
</form>
<br>
<hr style="text-align:left;width:875px;margin-left:0">
<br>
"""

        if len(results) == maxsearch:
            print '<a href="cgi-bin/commentsearch.cgi?name=' + urllib.quote_plus(username) + '&max=' + str(maxsearch) + '&search=' + urllib.quote_plus(searchstr) + '&startdate=' + str(int(results[-1][1])-1) + '"><small>Next ' + str(maxsearch) + " results &rarr;</small></a><br>"

        print "<ul>"
        printtable(results)
        print "</ul>"
        
        if len(results) == maxsearch:
            print '<a href="cgi-bin/commentsearch.cgi?name=' + urllib.quote_plus(username) + '&max=' + str(maxsearch) + '&search=' + urllib.quote_plus(searchstr) + '&startdate=' + str(int(results[-1][1])-1) + '"><small>Next ' + str(maxsearch) + " results &rarr;</small></a><br>"

        elapsed = time.time() - starttime
        print "<br><br><small>Elapsed time: " + str(round(elapsed, 2)) + " seconds.<br>\n"
        print datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</small><br>"
    except SystemExit:
        pass
    except:
        errorout("Unhandled exception.<br><br>" + traceback.print_exc(file=sys.stdout))
        #errorout('Unhandled exception. Please try again. If this error persists, please contact me at <a href="http://en.wikipedia.org/wiki/User_talk:Snottywong">User talk:Snottywong</a><br><br>')

        
def printtable(r):  #main function for printing out all edits
    global nosect
    if nosect:
        for edit in r:
            if checksections(edit[3]):
                print formatline(edit)
    else:
        for edit in r:
            print formatline(edit)

def formatline(edit):   #returns unordered list html for an edit
    revid = str(edit[0])
    timestamp = formatdate(edit[1])
    minoredit = edit[2]
    comment = escapehtml(edit[3].replace("[[WP:AES|←]]", "←"))
    pagetitle = edit[4]
    namespace = edit[5]
    fulltitle = nslookup[namespace].replace(" ", "_") + pagetitle
    return '<li><a href="http://en.wikipedia.org/w/index.php?title=' + fulltitle + '&oldid=' + revid + '">' + timestamp + '</a> (<a href="http://en.wikipedia.org/w/index.php?title=' + fulltitle + '&diff=prev&oldid=' + revid + '">diff</a> | <a href="http://en.wikipedia.org/w/index.php?title=' + fulltitle + '&action=history">hist</a>) ' + ("<b>m</b>" if minoredit else "") + ' <a href="http://en.wikipedia.org/wiki/' + fulltitle + '">' + fulltitle.replace("_", " ") + '</a> ' + (('(<span class="comment">' + fmtcmt(comment) + '</span>)') if comment else '') + '</li>'

def formatdate(ts): #formats timestamp into text
    d = datetime.datetime(int(ts[:4]), int(ts[4:6]), int(ts[6:8]), int(ts[8:10]), int(ts[10:12]), int(ts[12:14]))
    return d.strftime("%H:%M, %B %d, %Y")        

def fmtcmt(comment):    #adds an autocomment span into the comment if section header detected
    if "/*" in comment and "*/" in comment:
        return comment.replace("/*", '<span class="autocomment">/*', 1).replace("*/", "*/</span>", 1)
    return comment

def checksections(com):     #checks if search string appears outside of /* section headings */
    global searchstr
    if "/*" in com and "*/" in com:
        com = com[com.find("*/")+2:]
        if searchstr in com:
            return True
        else:
            return False
    return True

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
print '<br><small>Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Snottywong">User talk:Snottywong</a></small><br>'
print '<a href="commentsearch.html"><small>&larr;New search</small></a>'
print '</div></BODY>\n</HTML>'
