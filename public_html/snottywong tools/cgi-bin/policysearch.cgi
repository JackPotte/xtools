#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
import os
import cgi
import sys
import traceback
import datetime
import time

def main():
    gids = [3889066, 6239047, 8829268, 447141, 8662245, 756575, 11446256, 7405923, 24336286, 195122, 286178, 25498866, 25225324, 860842, 50181, 3618089, 2633486, 3600180, 526968, 14664589, 322950, 21421849, 5058022, 434648, 14853924, 3921878, 23224195, 2159945, 1566938, 9436599, 7221398, 49698, 3458484, 351777, 3464331, 1743525, 32767432, 2589853, 24498891, 5320732, 11477522, 390228, 16237846, 800830, 30796484, 3600598, 1708590, 8085014, 286793, 6155219, 7406238, 33697, 2424016, 7104297, 1945468, 3968093, 2580427, 22686814, 2833869, 1206185, 28207901, 396764, 22755284, 3507110, 3275057, 67739, 7868574, 4389093, 6818491, 15667332, 9484449, 249495, 256889, 2856112, 403058, 13399856, 542426, 2262650, 342552, 1008161, 6888715, 24374899, 33498936, 551841, 27137897, 2271987, 502959, 50144, 20965584, 67753, 247596, 6278516, 8539050, 59549, 8220773, 681638, 20781576, 1520472, 4180195, 17054975, 986312, 192954, 1420584, 2949878, 8955233, 318931, 324033, 100854, 3767009, 143131, 1327490, 5951599, 11442989, 10371968, 28774587, 8488622, 27126470, 67730, 183692, 215453, 4337560, 21402789, 5779956, 67736, 13646211, 3119680, 13231, 1688215, 50260, 20786118, 4098581, 3785404, 18443801, 32418498, 239780, 371142, 273430, 18621644, 839347, 6994445, 890739, 16681788, 746942, 1669570, 5845681, 266143, 1830559, 4534906, 2580363, 2619226, 9385389, 7748754, 18807112, 3050699, 690931, 5710938, 317870, 284702, 345326, 4226521, 7763344, 834114, 911375, 22064449, 199863, 32369693, 5294102, 3595100, 21438123, 33548, 7861408, 6796177, 31961304, 39809, 173830, 19005456, 6947029, 959720, 1412568, 2100084, 13410706, 16089740, 13340194, 2652807, 1222510, 3778805, 408749, 21438480, 252706, 10114151, 3166178, 67748, 2144215, 856807, 180904, 13010165, 3072008, 99719, 2678315, 5778115, 1836721, 153086]
    pids = [25455885, 2747122, 326245, 15221315, 425887, 22878346, 410235, 428038, 3982570, 2491966, 216487, 140524, 5711150, 49480, 4083092, 38760, 9769, 50178, 27124694, 392393, 12856110, 641471, 450740, 19389401, 15606128, 3897792, 29192815, 30329918, 168684, 28807595, 21372545, 39805, 3452342, 242275, 433312, 22880321, 18970377, 49483, 26481328, 805445, 177606, 3961892, 64347, 456268, 39801, 20781735, 16819254, 16810391, 26445787, 469393, 17817592, 3865231, 5025820, 1252005, 3788007, 49479]

    starttime = time.time()

    #Print initial HTML crap first, in case an error occurs it will already be there and the error page will look normal.
    print """<!doctype html>
<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html;charset=utf-8" >
<LINK href="menubar3.css" rel="stylesheet" type="text/css">
<TITLE>Policy contibution search results</TITLE>
</HEAD>
<BODY id="yes">
<script type="text/javascript" src="/menubar.js"></script>
<br>
<div id="globalWrapper">
<a href="policysearch.html"><small>&larr;New search</small></a>
<br><br>
"""
    try:
        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        form = cgi.FieldStorage()
        if "name" not in form:
            errorout("No name entered.")
        username = form['name'].value.replace("_", " ").replace("+", " ").strip()
        username = username[0].capitalize() + username[1:]
        if username.lower().startswith("user:"):
            username = username[5:]

        if os.environ["REMOTE_ADDR"].startswith("89.151.116.5"):
            errorout("Your IP address has been flagged for potential abuse.  Please post a message to User talk:Scottywong on the English Wikipedia, or alternatively send an email to snottywong.wiki@gmail.com to prove that you are a human, and to explain why you've been consistently making so many queries on this tool.")

        f = open("policysearchlog.txt", "a")
        f.write("<log><ip>" + os.environ["REMOTE_ADDR"] + "</ip><username>" + username + "</username><timestamp>" + datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</timestamp></log>\n")
        f.close()
        #Query user id
        cursor.execute("SELECT /* SLOW_OK */ user_id FROM user WHERE user_name=%s", (username))
        try:
            userid = cursor.fetchall()[0][0]
            userid = int(userid)
        except (ValueError, IndexError):
            errorout("Username not found.")

        #Query policy edits
        querystr = "SELECT /* SLOW_OK */ rev_id,rev_timestamp,rev_minor_edit,rev_comment,page_title from revision join page on rev_page=page_id where page_namespace=4 and rev_deleted=0 and rev_user=" + str(userid) + " and ("
        for p in pids[:-1]:
            querystr += "page_id=" + str(p) + " OR "
        querystr += "page_id=" + str(pids[-1]) + ") order by rev_timestamp desc limit 500;"
        cursor.execute(querystr)
        policyedits = cursor.fetchall()
        
        #Query guideline edits
        querystr = "SELECT /* SLOW_OK */ rev_id,rev_timestamp,rev_minor_edit,rev_comment,page_title from revision join page on rev_page=page_id where page_namespace=4 and rev_deleted=0 and rev_user=" + str(userid) + " and ("
        for g in gids[:-1]:
            querystr += "page_id=" + str(g) + " OR "
        querystr += "page_id=" + str(gids[-1]) + ") order by rev_timestamp desc limit 500;"
        cursor.execute(querystr)
        guidelineedits = cursor.fetchall()

        #Output results
        print "Displaying all edits made by User:" + escapehtml(username) + " to English Wikipedia's policy and guideline pages:<br><br>"
        print "<H3>Policy edits</H3><br>"
        if len(policyedits) == 0:
            print "No edits found to policy pages.<br><br><br>"
        else:
            print "<ul>"
            for edit in policyedits:
                revid = str(edit[0])
                timestamp = formatdate(edit[1])
                minoredit = edit[2]
                comment = edit[3].replace("[[WP:AES|←]]", "←")
                title = "Wikipedia:" + edit[4]
                print '<li><a href="http://en.wikipedia.org/w/index.php?title=' + title + '&oldid=' + revid + '">' + timestamp + '</a> (<a href="http://en.wikipedia.org/w/index.php?title=' + title + '&diff=prev&oldid=' + revid + '">diff</a> | <a href="http://en.wikipedia.org/w/index.php?title=' + title + '&action=history">hist</a>) ' + ("<b>m</b>" if minoredit else "") + ' <a href="http://en.wikipedia.org/wiki/' + title + '">' + escapehtml(title.replace("_", " ")) + '</a> ' + (('(<span class="comment">' + fmtcmt(escapehtml(comment)) + '</span>)') if comment else '') + '</li>'
            print "</ul><br><br><br>"

        print "<H3>Guideline edits</H3><br>"
        if len(guidelineedits) == 0:
            print "No edits found to guideline pages.<br><br><br>"
        else:
            print "<ul>"
            for edit in guidelineedits:
                revid = str(edit[0])
                timestamp = formatdate(edit[1])
                minoredit = edit[2]
                comment = edit[3].replace("[[WP:AES|←]]", "←")
                title = "Wikipedia:" + edit[4]
                print '<li><a href="http://en.wikipedia.org/w/index.php?title=' + title + '&oldid=' + revid + '">' + timestamp + '</a> (<a href="http://en.wikipedia.org/w/index.php?title=' + title + '&diff=prev&oldid=' + revid + '">diff</a> | <a href="http://en.wikipedia.org/w/index.php?title=' + title + '&action=history">hist</a>) ' + ("<b>m</b>" if minoredit else "") + ' <a href="http://en.wikipedia.org/wiki/' + title + '">' + escapehtml(title.replace("_", " ")) + '</a> ' + (('(<span class="comment">' + fmtcmt(escapehtml(comment)) + '</span>)') if comment else '') + '</li>'
            print "</ul><br><br><br>"            

        print "<br><br><small>Elapsed time: " + str(round(time.time() - starttime, 2)) + " seconds.<br>\n"
        print datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</small><br>"
        print '<br><small>Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Snottywong">User talk:Snottywong</a></small><br>'
        print '<a href="policysearch.html"><small>&larr;New search</small></a>'
        print "</div>\n</BODY>\n</HTML>"
    except SystemExit:
        pass
    except:
        #errorout("Unhandled exception.<br><br>" + traceback.print_exc(file=sys.stdout))
        errorout('Unhandled exception. Please try again. If this error persists, please contact me at <a href="http://en.wikipedia.org/wiki/User_talk:Snottywong">User talk:Snottywong</a><br><br>')


def formatdate(ts): #formats timestamp into text
    d = datetime.datetime(int(ts[:4]), int(ts[4:6]), int(ts[6:8]), int(ts[8:10]), int(ts[10:12]), int(ts[12:14]))
    return d.strftime("%H:%M, %B %d, %Y")

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

def errorout(errorstr): #prints error string and exits
    print "ERROR: " + errorstr + "<br><br>Please try again.<br>"
    print "</div>\n</BODY>\n</HTML>"
    sys.exit(0)

main()
