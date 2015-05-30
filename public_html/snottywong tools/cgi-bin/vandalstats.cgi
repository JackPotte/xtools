#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Get recentchanges from the last hour, analyze them for:
#Number of reverts per user
#Number of reverts per namespace
#Number of reverts that were probably for vandalism (include the word "vandal" or "vand" or "rv v" or "rvv")
#Reverts per minute
#Vandlism reverts per minute
#Total edits per minute
#Show a collapsed list of all reverts in contribution history form

import MySQLdb
import sys
import os
import traceback
import cgi
import re
from datetime import *
import time

nslookup = {0:"(Article)", 1:"Talk", 2:"User", 3:"User talk", 4:"Wikipedia", 5:"Wikipedia talk", 6:"File", 7:"File talk", 8:"MediaWiki", 9:"MediaWiki talk", 10:"Template", 11:"Template talk", 12:"Help", 13:"Help talk", 14:"Category", 15:"Category talk", 100:"Portal", 101:"Portal talk", 108:"Book", 109:"Book talk"}
vandregex = re.compile(r"vandal|\brv v\b|\brvv\b|\bvand\b", re.IGNORECASE)

def main():
    global nslookup
    global vandregex
    
    starttime = time.time()        
    print """<!doctype html>
<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html;charset=utf-8" >
<LINK href="greyscale.css" rel="stylesheet" type="text/css">
<LINK href="menubar3.css" rel="stylesheet" type="text/css">
<TITLE>Vandalism statistics</TITLE>
</HEAD>
<BODY id="yes">
<script type="text/javascript" src="/menubar.js"></script>
<br>
<div id="globalWrapper">
<div style="width:875px;">
<h1>Vandalism statistics</h1>
"""
    try:
        f = open("vandalstatslog.txt", "a")
        f.write("<log><ip>" + os.environ["REMOTE_ADDR"] + "</ip><timestamp>" + datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</timestamp></log>\n")
        f.close()
        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        #form = cgi.FieldStorage()
        hourago = (datetime.utcnow() - timedelta(hours=1)).strftime("%Y%m%d%H%M%S")
        cursor.execute('SELECT rc_timestamp, rc_user_text, rc_namespace, rc_title, rc_comment, rc_minor, rc_bot, rc_this_oldid, rc_last_oldid, rc_old_len, rc_new_len FROM recentchanges WHERE rc_timestamp>%s AND CAST(rc_comment AS CHAR CHARACTER SET utf8) REGEXP "revert|vandal|undid|[[:>:]]rv[[:>:]]|[[:>:]]vand[[:>:]]";', (hourago))
        results = cursor.fetchall()


        users = {}
        namespaces = {}
        vandalreverts = 0
        
        for edit in results:
            
            #Find reverts per user
            if edit[1] in users:
                users[edit[1]] += 1
            else:
                users[edit[1]] = 1

            #Find reverts per namespace
            ns = nslookup[edit[2]]
            if ns in namespaces:
                namespaces[ns] += 1
            else:
                namespaces[ns] = 1
                
            #Find number of reverts that were for vandalism
            if vandregex.search(edit[4]):
                vandalreverts += 1

        #Find rates of reverts and vandalism
        rpm = len(results)/60.0     #reverts per minute
        vrpm = vandalreverts/60.0   #vandal reverts per minute
                
        cursor.execute("SELECT COUNT(*) FROM recentchanges WHERE rc_timestamp>%s;", (hourago))
        editcount = cursor.fetchall()[0][0]
        epm = int(editcount)/60.0   #edits per minute

        #Now display all stats
        print "<br>This tool analyzes editing activity over the last hour, and provides statistics on reverts and vandalism over that period of time.  The tool relies on edit summaries to identify reverts and vandalism, and therefore may not be 100% accurate.<br><br>"
        print "<h2>Overall stats</h2><br>"
        print "<ul>"
        print "<li>Number of reverts in the last hour: " + str(len(results)) + " (" + str(round(rpm,1)) + " per minute)</li>"
        print "<li>Number of vandalism reverts in the last hour: " + str(vandalreverts) + " (" + str(round(vrpm,1)) + " per minute)</li>"
        print "<li>Number of edits made in the last hour: " + str(editcount) + " (" + str(round(epm,1)) + " per minute)</li>"
        print "</ul><br>"
        print "<br>\n<h2>Reverts per namespace</h2>"
        print rpntable(namespaces)
        print "<br>\n<h2>Reverts per user (top 20)</h2>"
        print rputable(users) + "<br>"
        print "</div>\n<br>\n<h2>Individual reverts (vandalism only)</h2>"
        print reverttable(results)
        
        print "<br><br><br>"
        
        elapsed = time.time() - starttime
        print "</div>"
        print "<br><br>Elapsed time: " + str(round(elapsed, 2)) + " seconds.<br>"
        print datetime.utcnow().strftime("%m/%d/%y %H:%M:%S") + "<br>"
        print 'Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Scottywong">User talk:Scottywong</a><br>'
        print "</div>\n</BODY>\n</HTML>"
    except SystemExit:
        pass
    except:
        errorout("Unhandled exception.<br><br>" + traceback.print_exc(file=sys.stdout))

def rpntable(namespaces):   #Return "reverts per namespace" table HTML
    printstr = """
<table>
<thead>
<tr>
<th scope="col">Namespace</th>
<th scope="col">Reverts</th>
</tr>
</thead>
<tbody>
"""
    for ns in sorted(namespaces, key=namespaces.get, reverse=True):
        printstr += "<tr>\n"
        printstr += "<td>" + ns + "</td>\n"
        printstr += "<td>" + str(namespaces[ns]) + "</td>\n</tr>\n"

    printstr += "</tbody>\n</table>\n"
    return printstr

def rputable(users):    #Return "reverts per user" table HTML
    printstr = """
<table>
<thead>
<tr>
<th scope="col">User</th>
<th scope="col">Reverts</th>
</tr>
</thead>
<tbody>
"""
    
    for u in sorted(users, key=users.get, reverse=True)[:20]:
        printstr += "<tr>\n"
        printstr += "<td>" + u + "</td>\n"
        printstr += "<td>" + str(users[u]) + "</td>\n</tr>\n"

    printstr += "</tbody>\n</table>\n"
    return printstr

def reverttable(reverts):   #Return full revert table HTML
    global nslookup
    global vandregex
    #rc_timestamp, rc_user_text, rc_namespace, rc_title, rc_comment, rc_minor, rc_bot, rc_this_oldid, rc_last_oldid, rc_old_len, rc_new_len
    printstr = "<ul>\n"
    for rv in reverts:
        if vandregex.search(rv[4]) == None:
            continue
        timestamp = formatdate(rv[0])
        username = rv[1]
        namespace = rv[2]
        comment = rv[4].replace("[[WP:AES|←]]", "←")
        minoredit = rv[5]
        botedit = rv[6]
        revid = str(rv[7])
        previd = str(rv[8])
        if rv[9] and rv[10]:
            d = rv[10]-rv[9]
            if d > 500:
                lenchange = '<strong style="color:darkGreen;">(+' + str(d) + ')</strong>'
            elif d > 0:
                lenchange = '<span style="color:darkGreen;">(+' + str(d) + ')</span>'
            elif d == 0:
                lenchange = '<span style="color:#AAA;">(0)</span>'
            elif d > -500:
                lenchange = '<span style="color:darkRed;">(' + str(d) + ')</span>'
            else:
                lenchange = '<strong style="color:darkRed;">(' + str(d) + ')</strong>'
        else:
            lenchange = '<span style="color:#AAA;">(?)</span>'

        namespacename = nslookup[namespace]
        if namespacename == "(Article)":
            namespacename = ""
        title = namespacename + (":" if namespacename else "") + rv[3]

        printstr += '<li>(<a href="http://en.wikipedia.org/w/index.php?title=' + title + '&oldid=' + previd + '&diff=' + revid + '">diff</a> | <a href="http://en.wikipedia.org/w/index.php?title=' + title + '&action=history">hist</a>) . . ' + ('<b>m</b>' if minoredit else '') + ('<b>b</b>' if botedit else '') + ' <a href="http://en.wikipedia.org/wiki/' + title + '">' + title.replace("_", " ") + '</a>; ' + timestamp + ' . . ' + lenchange + ' . . <a href="http://en.wikipedia.org/wiki/User:' + username + '">' + escapehtml(username.replace("_", " ")) + '</a> (<a href="http://en.wikipedia.org/wiki/User_talk:' + username + '">talk</a> | <a href="http://en.wikipedia.org/wiki/Special:Contributions/' + username + '">contribs</a>)' + ((' (<span class="comment">' + fmtcmt(escapehtml(comment)) + '</span>)') if comment else '') + '</li>\n'
        
    printstr += "</ul>\n"
    return printstr
        
#<li>(<a href="w/index.php?title=1931_Oaxaca_earthquake&amp;curid=34213313&amp;diff=468347477&amp;oldid=468346688">diff</a> | <a href="w/index.php?title=1931_Oaxaca_earthquake&amp;curid=34213313&amp;action=history"</a>) . .   <a href="wiki/1931_Oaxaca_earthquake">1931 Oaxaca earthquake</a>‎; 22:21 . . (+10)  . . <a href="wiki/User:Dawnseeker2000">Dawnseeker2000</a>                                                                                                          (<a href="wiki/User_talk:Dawnseeker2000">talk</a> | <a href="wiki/Special:Contributions/Dawnseeker2000">contribs</a>)<span class="comment">(reword, avoid redirect)</span></li>


def formatdate(ts): #formats timestamp into text
    d = datetime(int(ts[:4]), int(ts[4:6]), int(ts[6:8]), int(ts[8:10]), int(ts[10:12]), int(ts[12:14]))
    return d.strftime("%H:%M")

def escapehtml(s):  #escapes various characters to prevent attacks
    s = s.replace("&", "&amp;") # Must be first
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', '&quot;')
    return s

def fmtcmt(comment):    #adds an autocomment span into the comment if section header detected
    if "/*" in comment and "*/" in comment:
        return comment.replace("/*", '<span class="autocomment">/*', 1).replace("*/", "*/</span>", 1)
    return comment

def errorout(errorstr): #prints error string and exits
    print "ERROR: " + errorstr + "<br><br>Please try again.<br>"
    print "</div>\n</BODY>\n</HTML>"
    sys.exit(0)

main()

