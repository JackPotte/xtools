#!C:\Program Files (x86)\Python\python.exe
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cgitb
cgitb.enable()
#print "Content-Type: text/plain;charset=utf-8"
print "Content-type: text/html; charset=utf-8\n\n"
"""

SQL Queries:

    -Edit count
        select user_editcount from user where user_name="Colonel Warden";
        
    - Date of first edit:
            select min(rev_timestamp) from revision where rev_user_text="Snottywong";

    - Block count
            select count(*) from logging where log_type="block" and log_action="block" and log_namespace=2 and log_deleted=0 and log_title="Colonel_Warden";

    - Date of last block
            select max(log_timestamp) from logging where log_type="block" and log_action="block" and log_namespace=2 and log_deleted=0 and log_title="Colonel_Warden";

    - Get list of user rights (rollback, filemover, autopatroller, reviewer, abusefilter, sysop, etc.)
            select ug_group from user_groups join user on ug_user=user_id where user_name="Scottywong";

    - Has userpage with significant content size
            select page_len from page where page_namespace=2 and page_title="Scottywong";

    - Edits without an edit summary:
            select count(*) from revision where rev_user_text="Scottywong" and rev_comment="";

    - Active in the last x months
            SELECT COUNT(*) FROM revision JOIN user ON rev_user=user_id WHERE user_name=%s and rev_timestamp>"stuff" and rev_timestamp<"things";

    - % of edits to Wikipedia, Wikipedia talk, Article, Article talk, User talk namespaces
            select count(*) from revision join page on rev_page=page_id where rev_user_text="Scottywong" and page_namespace=1;

    - # of non-redirect articles created
            select count(distinct page_title) from page join revision on page_id=rev_page where rev_user_text="Scottywong" and rev_parent_id=0 and page_namespace=0 and page_is_redirect=0 limit 25;

    - # of articles patrolled
            select count(*) from logging where log_type="patrol" and log_action="patrol" and log_user_text="Scottywong" and log_namespace=0 and log_deleted=0 limit 10;
"""

import MySQLdb
import os
import sys
from datetime import *
import cgi
import numpy # python setup.py install
import urllib
import traceback
import time
import re
import socket
#Constants for scaling the scores of different criteria based on perceived importance:
EDITCOUNT_MULTIPLIER = 1.25
ACCOUNTAGE_MULTIPLIER = 1.25
BLOCKCOUNT_MULTIPLIER = 1.4
USERRIGHTS_MULTIPLIER = 0.75
USERPAGE_MULTIPLIER = 0.1
EDITSUMMARIES_MULTIPLIER = 0.8
ACTIVITY_MULTIPLIER = 0.9
NAMESPACES_MULTIPLIER = 1.0
ARTICLESCREATED_MULTIPLIER = 1.4
AIVRPPAFD_MULTIPLIER = 1.15
PATROL_MULTIPLIER = 1

currentrfa = False  #if True, user is currently at RfA and scores should be hidden
printtime = False   #if True, print timestamps after each score to gauge how long it took to query
start = 0           #global timer, started in main()

#TODO: Check if user page is a redirect and knock off points

def main():
    global printtime
    global start
    try:
        print """<!doctype html>
    <HTML>
    <HEAD>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
    <LINK href="greyscale.css" rel="stylesheet" type="text/css">
    <LINK href="menubar3.css" rel="stylesheet" type="text/css">
    <TITLE>Admin Score</TITLE>
    </HEAD>
    <BODY id="no">
    <script type="text/javascript" src="/menubar.js"></script>
    <br>
    <div style="width:875px;">"""
        if socket.gethostname() == "PavilionDV6":
            db = MySQLdb.connect(host='localhost', db='enwiki_p', user='enwiki_p', passwd="enwiki_p")
        else:
            db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        sql = db.cursor()
        form = cgi.FieldStorage()
        if "name" not in form:
            errorout("No name entered.")
        else:
            name = form['name'].value.replace("_", " ").replace("+", " ")
            name = urllib.unquote(name)
            if name.lower().startswith("user:"):
                name = name[5:]

        if "printtime" in form:
            printtime = True

        print "<H1>Admin Score for User:" + cgi.escape(name) + "</H1>"
        
        if os.environ["REMOTE_ADDR"].startswith("89.151.116.5"):
            errorout("Your IP address has been flagged for potential abuse.  Please post a message to User talk:Scottywong on the English Wikipedia, or alternatively send an email to snottywong.wiki@gmail.com to prove that you are a human, and to explain why you've been consistently making so many queries on this tool.")

        f = open("adminscorelog.txt", "a")
        f.write("<log><ip>" + os.environ["REMOTE_ADDR"] + "</ip><name>" + name + "</name><timestamp>" + datetime.utcnow().strftime("%m/%d/%y %H:%M:%S") + "</timestamp></log>\n")
        f.close()

        score = 0
        start = time.time()
        #debug("start")
        initialchecks(sql, name)
        #debug("initialchecks")
        score += editcount(sql, name)
        #debug("editcount")
        score += accountage(sql, name)
        #debug("accountage")
        #score += blockcount2(sql, name)
        #debug("blockcount2")
        score += userrights(sql, name)
        #debug("userrights")
        score += userpage(sql, name)
        #debug("userpage")
        #score += editsummaries(sql, name)
        #debug("editsummaries")
        #score += activity(sql, name)
        #debug("activity")
        #score += namespaces(sql, name)
        #debug("namespaces")
        #score += articlescreated(sql, name)
        #debug("articlescreated")
        #score += aivrppafd(sql, name)
        #debug("aivrppafd")
        score += patrols(sql, name)
        if not currentrfa:
            print "<br><br><b><big>Total Score: " + str(score) + "</big></b>"
        print "<br><br><small>Elapsed time: " + str(round(time.time() - start, 2)) + " seconds."
        print '<br><small>Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Scottywong">User talk:Scottywong</a></small><br>'
        print "</div></BODY>\n</HTML>"
    except SystemExit:
        pass
    except:
        print "Error"
        print sys.exc_info()[0]
        print "<br>"
        print traceback.print_exc(file=sys.stdout)
        print "<br>"


def initialchecks(sql, name):
    global currentrfa
    #sql.execute("SELECT COUNT(*) FROM user_groups JOIN user ON ug_user=user_id WHERE user_name=%s AND ug_group=%s;", (name, "sysop"))
    sql.execute("SELECT COUNT(*) FROM user_groups JOIN user ON ug_user=user_id WHERE user_name='{0}' AND ug_group='{1}';".format(name, "sysop"))
    if int(sql.fetchall()[0][0]) == 1:  #User is an admin
        errorout("User is already an admin.  This tool is intended to be used on non-admin users.")
    rfapage = "Requests_for_adminship/" + name.replace(" ", "_")
    #sql.execute("SELECT page_title FROM page WHERE page_namespace=4 AND page_title=%s AND page_is_redirect=0;", (rfapage))	# TypeError: not all arguments converted during string formatting None 
    sql.execute("SELECT page_title FROM page WHERE page_namespace=4 AND page_title='{0}' AND page_is_redirect=0;".format(rfapage))	#  
    result = sql.fetchall()
    if len(result) == 0:    #RfA page doesn't exist
        return
    pagename = result[0][0]
    suffix = 1
    while len(result) == 1:
        suffix += 1
        #sql.execute("SELECT page_title FROM page WHERE page_namespace=4 AND page_title=%s AND page_is_redirect=0;", (rfapage + "_" + str(suffix)))
        sql.execute("SELECT page_title FROM page WHERE page_namespace=4 AND page_title='{0}' AND page_is_redirect=0;".format(rfapage + "_" + str(suffix)))
        result = sql.fetchall()
        if len(result) == 1:
            pagename = result[0][0]
    pagedata = APIget(pagename.replace("_", " "))
    if "The following discussion is preserved as an archive of a [[wikipedia:requests for adminship|request for adminship]] that '''did not succeed'''" in pagedata or "The following discussion is preserved as an archive of a '''successful''' [[wikipedia:requests for adminship|request for adminship]]" in pagedata:  #RfA is closed
        return
    print "<br><b>User is currently nominated for adminship and an RfA is ongoing.  Scores are not shown for current candidates.</b><br>"
    currentrfa = True
    return        


def editcount(sql, name):
    #sql.execute("SELECT user_editcount FROM user WHERE user_name=%s;", (name))
    sql.execute("SELECT user_editcount FROM user WHERE user_name='{0}';".format(name))
    try:
        edits = sql.fetchall()[0][0]
    except:
        errorout("User does not exist.")
        return
    if edits is None or int(edits) == 0:
        errorout("User has no edits.")
    print "<br>Edit count: " + str(edits)
    xscores = [ 0,       3000,  6000,   11000, 25000  ]
    yscores = [ -100,    -50,   0,      50,    100    ]
    score = int(round(numpy.interp(int(edits), xscores, yscores) * EDITCOUNT_MULTIPLIER, 0))
    printscore(score)
    return score

        
def accountage(sql, name):
    #sql.execute("SELECT MIN(rev_timestamp) FROM revision WHERE rev_user_text=%s;", (name))
    sql.execute("SELECT MIN(rev_timestamp) FROM revision WHERE rev_user_text='{0}';".format(name))
    ts = sql.fetchall()[0][0]
    dt = datetime(int(ts[:4]), int(ts[4:6]), int(ts[6:8]), int(ts[8:10]), int(ts[10:12]), int(ts[12:14]))
    days = (datetime.utcnow() - dt).days
    print "<br>Account age: " + str(days) + " days"
    xscores = [ 0,    227,    365,    730,    1095  ]
    yscores = [ -100, -50,    0,      50,     100   ]
    score = int(round(numpy.interp(days, xscores, yscores) * ACCOUNTAGE_MULTIPLIER, 0))
    printscore(score)
    return score

    
def blockcount(sql, name):  #Uses SQL, slower
    #sql.execute("SELECT COUNT(*) FROM logging WHERE log_type=\"block\" AND log_action=\"block\" AND log_namespace=2 AND log_deleted=0 AND log_title=%s;", (name.replace(" ", "_")))
    sql.execute("SELECT COUNT(*) FROM logging WHERE log_type=\"block\" AND log_action=\"block\" AND log_namespace=2 AND log_deleted=0 AND log_title='{0}';".format(name.replace(" ", "_")))
    blocks = sql.fetchall()[0][0]
    print "<br>Block count: " + str(blocks)
    if blocks == 0:
        score = int(round(100.0 * BLOCKCOUNT_MULTIPLIER, 0))  #Maximum points if never blocked
    else:
        #If user has been blocked, then find the last block and base the score on how long ago it was.
        #sql.execute("SELECT MAX(log_timestamp) FROM logging WHERE log_type=\"block\" AND log_action=\"block\" AND log_namespace=2 AND log_deleted=0 AND log_title=%s;", (name.replace(" ", "_")))
        sql.execute("SELECT MAX(log_timestamp) FROM logging WHERE log_type=\"block\" AND log_action=\"block\" AND log_namespace=2 AND log_deleted=0 AND log_title='{0}';".format(name.replace(" ", "_")))
        ts = sql.fetchall()[0][0]
        dt = datetime(int(ts[:4]), int(ts[4:6]), int(ts[6:8]), int(ts[8:10]), int(ts[10:12]), int(ts[12:14]))
        days = (datetime.utcnow() - dt).days
        print "  (last block " + str(days) + " days ago)"
        xscores = [ 30,   180,    400,    725,    1000 ]
        yscores = [ -100, -50,    0,      50,     100  ]
        score = int(round(numpy.interp(days, xscores, yscores) * BLOCKCOUNT_MULTIPLIER, 0))
        score -= blocks*10      #Take off 10 points for each block
        #if score < -100*BLOCKCOUNT_MULTIPLIER:
            #score = int(-100*BLOCKCOUNT_MULTIPLIER)
    printscore(score)
    return score

def blockcount2(sql, name):  #Uses API, faster
    u = urllib.urlopen("http://en.wikipedia.org/w/api.php?action=query&list=logevents&leprop=timestamp&leaction=block/block&format=xml&letitle=User:" + urllib.quote(name))
    xml = u.read()
    u.close()
    blocks = re.findall("<item timestamp=\"(.*?)\" />", xml)
    print "<br>Block count: " + str(len(blocks))
    if len(blocks) == 0:
        score = int(round(100.0 * BLOCKCOUNT_MULTIPLIER, 0))    #Maximum points if never blocked
    else:
        try:
            u = urllib.urlopen("http://en.wikipedia.org/w/api.php?action=query&list=logevents&leaction=block/unblock&leprop=timestamp&lelimit=1&ledir=older&format=xml&letitle=User:" + urllib.quote(name))
            xml = u.read()
            u.close()
            lastunblock = re.search("<item timestamp=\"(.*?)\" />", xml).group(1)
        except:
            try:
                u = urllib.urlopen("http://en.wikipedia.org/w/api.php?action=query&list=logevents&leaction=block/block&format=xml&ledir=older&lelimit=1&leprop=details&letitle=User:" + urllib.quote(name))
                xml = u.read()
                u.close()
                lastunblock = re.search("expiry=\"(.*?)\"", xml).group(1)
            except:
                lastunblock = blocks[0]
        dt = datetime.strptime(lastunblock, "%Y-%m-%dT%H:%M:%SZ")
        days = (datetime.utcnow() - dt).days
        print "  (last block expired " + str(days) + " days ago)"
        xscores = [ 30,   180,    400,    725,    1000 ]
        yscores = [ -100, -50,    0,      50,     100  ]
        score = int(round(numpy.interp(days, xscores, yscores) * BLOCKCOUNT_MULTIPLIER, 0))
        score -= len(blocks)*10      #Take off 10 points for each block
    printscore(score)
    return score
    
def userrights(sql, name):
    #sql.execute("SELECT ug_group FROM user_groups JOIN user ON ug_user=user_id WHERE user_name=%s;", (name))
    sql.execute("SELECT ug_group FROM user_groups JOIN user ON ug_user=user_id WHERE user_name='{0}';".format(name))
    groups = sql.fetchall()
    print "<br>User rights: "
    grouplist = []
    for g in groups:
        grouplist.append(g[0])
        print g[0] + " "
    if len(grouplist) == 0:
        print "None"
    scoretable = {"abusefilter":25, "accountcreator":10, "autoreviewer":20, "checkuser":25, "filemover":20, "rollbacker":10}
    score = 0
    for g in scoretable.keys():
        if g in grouplist:
            score += scoretable[g]
    if score > 100:
        score = 100
    score = int(round(score * USERRIGHTS_MULTIPLIER, 0))
    printscore(score)
    return score

    
def userpage(sql, name):
    #sql.execute("SELECT page_len FROM page WHERE page_namespace=2 AND page_title=%s;", (name.replace(" ", "_")))
    sql.execute("SELECT page_len FROM page WHERE page_namespace=2 AND page_title='{0}';".format(name.replace(" ", "_")))
    pagelen = sql.fetchall()
    if len(pagelen) == 0:   #User's page doesn't exist
        print "<br>User page: Doesn't exist"
        score = int(round(-100 * USERPAGE_MULTIPLIER, 0))
    else:
        print "<br>User page: Exists"
        score = int(round(100 * USERPAGE_MULTIPLIER, 0))
    printscore(score)
    return score

    
def editsummaries(sql, name):
    #sql.execute("SELECT COUNT(*) FROM revision JOIN page ON rev_page=page_id WHERE page_namespace=0 AND rev_user_text=%s AND rev_comment=\"\" AND rev_timestamp>%s;", (name, (datetime.utcnow() - timedelta(days=730)).strftime("%Y%m%d%H%M%S")))
    sql.execute("SELECT COUNT(*) FROM revision JOIN page ON rev_page=page_id WHERE page_namespace=0 AND rev_user_text='{0}' AND rev_comment=\"\" AND rev_timestamp>{1};".format(name, (datetime.utcnow() - timedelta(days=730)).strftime("%Y%m%d%H%M%S")))
    nosum = sql.fetchall()[0][0]
    #sql.execute("SELECT COUNT(*) FROM revision JOIN page ON rev_page=page_id WHERE page_namespace=0 AND rev_user_text=%s AND rev_timestamp>%s;", (name, (datetime.utcnow() - timedelta(days=730)).strftime("%Y%m%d%H%M%S")))
    sql.execute("SELECT COUNT(*) FROM revision JOIN page ON rev_page=page_id WHERE page_namespace=0 AND rev_user_text='{0}' AND rev_timestamp>{1};".format(name, (datetime.utcnow() - timedelta(days=730)).strftime("%Y%m%d%H%M%S")))
    total = sql.fetchall()[0][0]
    if total == 0:
        percent = 1.0
    else:
        percent = float(nosum)/float(total)
    print "<br>Missing edit summaries (article namespace, last 2 years): " + str(round(100.0*percent, 1)) + "%"
    xscores = [ 0.0,  0.02,  0.05,  0.2,  0.3  ]
    yscores = [ 100,  50,    0,     -50,  -100 ]
    score = int(round(numpy.interp(percent, xscores, yscores) * EDITSUMMARIES_MULTIPLIER, 0))
    printscore(score)
    return score

    
def activity(sql, name):
    year = datetime.utcnow().year
    month = datetime.utcnow().month
    monthlyedits = []
    for crap in range(12):  #Go back 12 months
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        mintimestamp = str(year) + ("0" if month<10 else "") + str(month) + "01000000"
        maxtimestamp = str(year) + ("0" if month<10 else "") + str(month) + "31235959"
        #sql.execute("SELECT COUNT(*) FROM revision WHERE rev_user_text=%s AND rev_timestamp>%s and rev_timestamp<%s;", (name, mintimestamp, maxtimestamp))
        sql.execute("SELECT COUNT(*) FROM revision WHERE rev_user_text='{0}' AND rev_timestamp>{1} and rev_timestamp<{2};".format(name, mintimestamp, maxtimestamp))
        monthcount = sql.fetchall()[0][0]
        monthlyedits.append(int(monthcount))
    avg = sum(monthlyedits)/float(len(monthlyedits))
    
    #Average monthly edit count score, max 50 points:
    xscores = [ 0,    45,   85,    220,    500  ]
    yscores = [ -50, -25,   0,     25,     50  ]
    score1 = int(round(numpy.interp(avg, xscores, yscores) * ACTIVITY_MULTIPLIER, 0))
    print "<br>Average monthly edit count (last 12 mo.): " + str(int(round(avg, 0)))
    printscore(score1)
    
    #Minimum monthly edit count score, max 50 points:
    xscores = [ 0,   30,    50,    100,    200 ]
    yscores = [ -50, -25,   0,     25,     50  ]
    score2 = int(round(numpy.interp(int(min(monthlyedits)), xscores, yscores) * ACTIVITY_MULTIPLIER, 0))
    print "<br>Minimum monthly edit count (last 12 mo.): " + str(min(monthlyedits))
    printscore(score2)
    
    return score1 + score2
    
    
def namespaces(sql, name):
    #sql.execute("SELECT count(*) FROM revision JOIN page ON rev_page=page_id WHERE rev_user_text=%s AND page_namespace=0;", (name))
    sql.execute("SELECT count(*) FROM revision JOIN page ON rev_page=page_id WHERE rev_user_text='{0}' AND page_namespace=0;".format(name))
    articlecount = sql.fetchall()[0][0]
    #sql.execute("SELECT count(*) FROM revision JOIN page ON rev_page=page_id WHERE rev_user_text=%s AND page_namespace=4;", (name))
    sql.execute("SELECT count(*) FROM revision JOIN page ON rev_page=page_id WHERE rev_user_text='{0}' AND page_namespace=4;".format(name))
    wpcount = sql.fetchall()[0][0]
    #sql.execute("SELECT count(*) FROM revision JOIN page ON rev_page=page_id WHERE rev_user_text=%s AND (page_namespace=1 OR page_namespace=3 OR page_namespace=5);", (name))
    sql.execute("SELECT count(*) FROM revision JOIN page ON rev_page=page_id WHERE rev_user_text='{0}' AND (page_namespace=1 OR page_namespace=3 OR page_namespace=5);".format(name))
    talkcount = sql.fetchall()[0][0]

    #Article space: max points = 40
    xscores = [ 500, 1000, 2000, 3000, 5000 ]
    yscores = [ -40, -20,   0,   20,   40 ]
    score1 = int(round(numpy.interp(int(articlecount), xscores, yscores) * NAMESPACES_MULTIPLIER, 0))
    print "<br># of edits to Article namespace: " + str(articlecount)
    printscore(score1)

    #WP space: max points = 40
    xscores = [ 300,  400,    500,  1000,   2000 ]
    yscores = [ -40,  -20,    0,    20,     40   ]
    score2 = int(round(numpy.interp(int(wpcount), xscores, yscores) * NAMESPACES_MULTIPLIER, 0))
    print "<br># of edits to Wikipedia namespace: " + str(wpcount)
    printscore(score2)

    #Talk spaces: max points = 20
    xscores = [ 200,  300,    400,  700,    1000 ]
    yscores = [ -20,  -10,    0,    10,     20   ]
    score3 = int(round(numpy.interp(int(talkcount), xscores, yscores) * NAMESPACES_MULTIPLIER, 0))
    print "<br># of edits to various Talk namespaces: " + str(talkcount)
    printscore(score3)

    return score1 + score2 + score3

 
def articlescreated(sql, name):
    #DEBUG starttime = time.time()
    #sql.execute("SELECT DISTINCT page_id FROM page JOIN revision ON page_id=rev_page WHERE rev_user_text=%s and page_namespace=0 AND page_is_redirect=0;", (name))
    sql.execute("SELECT DISTINCT page_id FROM page JOIN revision ON page_id=rev_page WHERE rev_user_text='{0}' and page_namespace=0 AND page_is_redirect=0;".format(name))
    allpages = sql.fetchall()
    count = 0
    for page in allpages:
        #DEBUG print time.time() - starttime
        #sql.execute("SELECT rev_user_text, rev_timestamp FROM revision WHERE rev_page=%s order by rev_id asc limit 1;", (page[0]))
        sql.execute("SELECT rev_user_text, rev_timestamp FROM revision WHERE rev_page='{0}' order by rev_id asc limit 1;".format(page[0]))
        if sql.fetchall()[0][0] == name:
            count += 1
            if count > 100:
                break
    if count > 100:
        print "<br>Non-redirect articles created: >100"
    else:
        print "<br>Non-redirect articles created: " + str(count)
    xscores = [ 0,    2,    5,   33,    100  ]
    yscores = [ -100, -50,  0,   50,    100  ]
    score = int(round(numpy.interp(int(count), xscores, yscores) * ARTICLESCREATED_MULTIPLIER, 0))
    printscore(score)
    return score


def aivrppafd(sql, name):
    #sql.execute("SELECT COUNT(*) FROM revision JOIN page ON rev_page=page_id WHERE rev_user_text=%s AND page_namespace=4 AND page_title=%s;", (name, "Requests_for_page_protection"))
    sql.execute("SELECT COUNT(*) FROM revision JOIN page ON rev_page=page_id WHERE rev_user_text='{0}' AND page_namespace=4 AND page_title='{1}';".format(name, "Requests_for_page_protection"))
    rppedits = sql.fetchall()[0][0]
    #sql.execute("SELECT COUNT(*) FROM revision JOIN page ON rev_page=page_id WHERE rev_user_text=%s AND page_namespace=4 AND page_title=%s;", (name, "Administrator_intervention_against_vandalism"))
    sql.execute("SELECT COUNT(*) FROM revision JOIN page ON rev_page=page_id WHERE rev_user_text='{0}' AND page_namespace=4 AND page_title='{1}';".format(name, "Administrator_intervention_against_vandalism"))
    aivedits = sql.fetchall()[0][0]
    #sql.execute("SELECT COUNT(*) FROM revision JOIN page ON rev_page=page_id WHERE rev_user_text=%s AND page_namespace=4 AND page_title LIKE %s AND page_title NOT LIKE %s;", (name, "Articles_for_deletion/%", "Articles_for_deletion/Log/%"))
    sql.execute("SELECT COUNT(*) FROM revision JOIN page ON rev_page=page_id WHERE rev_user_text='{0}' AND page_namespace=4 AND page_title LIKE '{1}' AND page_title NOT LIKE '{2}';".format(name, "Articles_for_deletion/%", "Articles_for_deletion/Log/%"))
    afdedits = sql.fetchall()[0][0]
    edits = int(rppedits) + int(aivedits) + int(afdedits)
    print "<br>Edits to admin areas (AIV/RPP/AfD): " + str(edits)
    xscores = [ 50,    100,  200,  500,  1000 ]
    yscores = [ -100,  -50,  0,    50,   100  ]
    score = int(round(numpy.interp(edits, xscores, yscores) * AIVRPPAFD_MULTIPLIER, 0))
    printscore(score)
    return score
    
def patrols(sql, name):
    sql.execute("select count(*) from logging where log_type="patrol" and log_action="patrol" and log_user_text='{0}' and log_namespace=0 and log_deleted=0;".format(name))
	xscores = [ 50,    100,  200,  500,  1000 ]
    yscores = [ -100,  -50,  0,    50,   100  ]
    score = int(round(numpy.interp(edits, xscores, yscores) * PATROL_MULTIPLIER, 0))
    printscore(score)
    return score
	
def printscore(score):
    global start
    global printtime
    if not currentrfa:
        print "&nbsp;&nbsp;&nbsp;" + ("<span style=\"font-weight:bold;color:#3c3\">+" if score>=0 else "<span style=\"font-weight:bold;color:#f00\">") + str(score) + "</span>"
    if printtime:
        print "&nbsp;&nbsp;&nbsp;" + str(round(time.time() - start, 1))

def APIget(p):
    u = urllib.urlopen("http://en.wikipedia.org/w/api.php?action=query&prop=revisions&titles=Wikipedia:" + urllib.quote(p) + "&rvprop=content&format=xml")
    xml = u.read()
    u.close()
    text = re.search(r'<rev.*?xml:space="preserve">(.*?)</rev>', xml, re.DOTALL).group(1)
    return text

def errorout(errorstr):
    print "ERROR: " + errorstr + "<br><br>Please try again.<br>"
    print '<br><small>Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Scottywong">User talk:Scottywong</a></small><br>'
    print "</div></BODY>\n</HTML>"
    sys.exit(0)

def debug(text):
    global start
    f = open("debug.txt", "a")
    f.write(str(round(time.time() - start, 1)) + "   " + text + "\n")
    f.close()

main()
