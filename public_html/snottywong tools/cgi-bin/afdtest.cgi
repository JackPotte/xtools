#!/usr/bin/env python

#TO DO:
#Improve voteregex to catch unsigned votes
#Add CSS classes to table, to make it look nicer, as well as to make green/red background for votes which were correct/incorrect, and for diagonals on vote matrix
#Grab articles 50 at a time instead of 1 at a time from the API

import MySQLdb
import sys
import os
import traceback
import cgi
import urllib
import re
import datetime
import time

starttime = time.time()
voteregex = re.compile("'{3}?.*?'{3}?.*?\(UTC\)", re.IGNORECASE) #may need to add "{{unsigned" and "<span class="autosigned"> as optional terminators to reduce errors due to idiots not signing their votes
userregex = re.compile("\[\[User.*?:(.*?)(?:\||(?:\]\]))", re.IGNORECASE)
resultregex = re.compile("The result was(?:\s*?)(?:'{3}?)(.*?)(?:'{3}?)", re.IGNORECASE)
timeregex = re.compile("(\d{2}:\d{2}, .*?) \(UTC\)")
timeparseregex = re.compile("\d{2}:\d{2}, (\d{1,2}) ([A-Za-z]*) (\d{4})")
timestampparseregex = re.compile("(\d{4})-(\d{2})-(\d{2})")
monthmap = {"01":"January", "02":"February", "03":"March", "04":"April", "05":"May", "06":"June", "07":"July", "08":"August", "09":"September", "10":"October", "11":"November", "12":"December"}
username = ''
maxsearch = 10

stats = {}
statsresults = ["k", "d", "sk", "sd", "m", "r", "t", "u", "nc"]
votetypes = ["Keep", "Delete", "Speedy Keep", "Speedy Delete", "Merge", "Redirect", "Transwiki"]
statsvotes = statsresults[:-1]
for v in statsvotes:
    for r in statsresults:
        stats[v+r] = 0
for v in votetypes:
    stats[v] = 0

tablelist = []

print """<!doctype html>
<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
<TITLE>AfD Stats</TITLE>
</HEAD>
<BODY>
"""


def main():
    global username
    global maxsearch
    try:
        errors = False
        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        form = cgi.FieldStorage()
        if "name" not in form:
            print "No name entered."
            errors = True
        else:
            try:
                if "max" in form:
                    maxsearch = min(100, int(form['max'].value))
                username = form['name'].value.replace("_", " ").replace("+", " ")
                cursor.execute(u'SELECT user_id FROM user WHERE user_name="' + username + '";')
                userid = cursor.fetchall()[0][0]
            except:
                print "Username not found."
                errors = True
        if not errors:
            cursor = db.cursor()
            cursor.execute(u'SELECT DISTINCT page_title FROM revision JOIN page ON rev_page=page_id WHERE rev_user=' + str(userid) + ' AND page_namespace=4 AND page_title LIKE "Articles_for_deletion%" AND NOT page_title LIKE "Articles_for_deletion/Log/%";')
            results = cursor.fetchall()
            results = tuple(reversed(results))
            db.close()
            
            print "Total number of unique AfD pages edited by " + username + ": " + str(len(results)) + "<br>Analyzing last " + str(min(maxsearch, len(results))) + " votes.<br><br>"
            analyze(results[:min(maxsearch, len(results))])
            printtable()
            elapsed = time.time() - starttime
            print "<br><br><small>Elapsed time: " + str(elapsed) + " seconds.</small><br>"
    except:
        print sys.exc_info()[0]
        print "<br>"
        print traceback.print_exc(file=sys.stdout)

def analyze(pages):
    for entry in pages:
        try:
            page = entry[0]
            data = APIget(page)
            votes = voteregex.findall(data)
            result = findresults(data)
            dupvotes = []
            for vote in votes:
                try:
                    votermatch = userregex.match(vote[vote.rfind("[[User"):])
                    if votermatch == None:
                        continue
                    else:
                        voter = votermatch.group(1).strip()
                    if voter.lower() == username.lower():
                        votetype = parsevote(vote[3:vote.find("'", 3)])
                        if votetype == None:
                            continue
                        if votetype == "UNDETERMINED":
                            continue
                        timematch = timeregex.search(vote)
                        if timematch == None:
                            votetime = ""
                        else:
                            votetime = parsetime(timematch.group(1))
                        dupvotes.append((page, votetype, votetime, result, 0))
                except:
                    print sys.exc_info()[0]
                    print "<br>"
                    print traceback.print_exc(file=sys.stdout)
                    continue
            if len(dupvotes) < 1:
                firsteditor = APIfirsteditor(page)
                if firsteditor:
                    if firsteditor[0].lower() == username.lower(): #user is nominator
                        tablelist.append((page, "Delete", firsteditor[1], result, 1))
                        updatestats("Delete", result)
            elif len(dupvotes) > 1:
                #ch = choosevote(dupvotes)  - not doing this anymore, just take the last vote found as it is probably the correct one (i.e. if someone changed their vote)
                ch = len(dupvotes) - 1
                tablelist.append(dupvotes[ch])
                updatestats(dupvotes[ch][1], dupvotes[ch][3])
            else:
                tablelist.append(dupvotes[0])
                updatestats(dupvotes[0][1], dupvotes[0][3])
        except:
            print sys.exc_info()[0]
            print "<br>"
            print traceback.print_exc(file=sys.stdout)
            continue
            
def parsevote(v):
    v = v.lower()
    if "comment" in v:
        return None
    elif "note" in v:
        return None
    elif "merge" in v:
        return "Merge"
    elif "redirect" in v:
        return "Redirect"
    elif "speedy keep" in v:
        return "Speedy Keep"
    elif "speedy delete" in v:
        return "Speedy Delete"
    elif "keep" in v:
        return "Keep"
    elif "delete" in v:
        return "Delete"
    elif "transwiki" in v:
        return "Transwiki"
    elif ("userfy" in v) or ("userfied" in v) or ("incubat" in v):
        return "Userfy"
    else:
        return "UNDETERMINED"

def findresults(thepage):
    resultsearch = resultregex.search(thepage)
    if resultsearch == None:
        if "boilerplate metadata afd vfd xfd-closed" in thepage:
            return "UNDETERMINED"
        else:
            return "Not closed yet"
    else:
        result = resultsearch.group(1).lower()
        if "no consensus" in result:
            return "No Consensus"
        elif "merge" in result:
            return "Merge"
        elif "redirect" in result:
            return "Redirect"
        elif "speedy keep" in result:
            return "Speedy Keep"
        elif "speedy delete" in result:
            return "Speedy Delete"
        elif "keep" in result:
            return "Keep"
        elif "delete" in result:
            return "Delete"
        elif "transwiki" in result:
            return "Transwiki"
        elif ("userfy" in result) or ("userfied" in result) or ("incubat" in result):
            return "Userfy"
        else:
            return "UNDETERMINED"

def parsetime(t):
    tm = timeparseregex.search(t)
    if tm == None:
        return ""
    else:
        return tm.group(2) + " " + tm.group(1) + ", " + tm.group(3)

def updatestats(v, r):
    if v == "Merge":
        vv = "m"
    elif v == "Redirect":
        vv = "r"
    elif v == "Speedy Keep":
        vv = "sk"
    elif v == "Speedy Delete":
        vv = "sd"
    elif v == "Keep":
        vv = "k"
    elif v == "Delete":
        vv = "d"
    elif v == "Transwiki":
        vv = "t"
    elif v == "Userfy":
        vv = "u"
    else:
        return
    stats[v] += 1
    if r == "Merge":
        rr = "m"
    elif r == "Redirect":
        rr = "r"
    elif r == "Speedy Keep":
        rr = "sk"
    elif r == "Speedy Delete":
        rr = "sd"
    elif r == "Keep":
        rr = "k"
    elif r == "Delete":
        rr = "d"
    elif r == "Transwiki":
        rr = "t"
    elif r == "Userfy":
        rr = "u"
    elif r == "No Consensus":
        rr = "nc"
    else:
        return
    stats[vv+rr] += 1

def APIget(p):
    try:
        u = urllib.urlopen("http://en.wikipedia.org/w/api.php?action=query&prop=revisions&titles=Wikipedia:" + urllib.quote(p) + "&rvprop=content&format=xml")
        xml = u.read()
        u.close()
        text = re.search(r'<rev xml:space="preserve">(.*?)</rev>', xml, re.DOTALL).group(1)
        return text
    except:
        print sys.exc_info()[0]
        print "<br>"
        print traceback.print_exc(file=sys.stdout)
        print "<br>"
        return None

def APIfirsteditor(p):
    try:
        u = urllib.urlopen("http://en.wikipedia.org/w/api.php?action=query&prop=revisions&titles=Wikipedia:" + urllib.quote(p) + "&rvlimit=1&rvprop=timestamp|user&rvdir=newer&format=xml")
        xml = u.read()
        u.close()
        s = re.search("<rev user=\"(?P<user>.*?)\" timestamp=\"(?P<timestamp>.*?)\" />", xml)
        user = s.group("user")
        timestamp = timestampparseregex.search(s.group("timestamp"))
        timestamptext = monthmap[timestamp.group(2)] + " " + timestamp.group(3).lstrip("0") + ", " + timestamp.group(1)
        return (user, timestamptext)
    except:
        print sys.exc_info()[0]
        print "<br>"
        print traceback.print_exc(file=sys.stdout)
        return None

def link(p):
    text = cgi.escape(p.replace("_", " ")[22:])
    if len(text) > 64:
        text = text[:61] + "..."
    return '<a href="http://en.wikipedia.org/wiki/Wikipedia:' + urllib.quote(p) + '">' + text + '</a>'

def printtable():
    print """<br><br>
<table border=1>
<tr>
<th colspan=2 rowspan=2></th>
<th colspan=9>Results</th>
</tr>
<tr>
"""
    for i in statsresults:
        print "<th>" + i.upper() + "</th>\n"
    print "</tr>\n"
    print "<tr><th rowspan=9>Votes</th></tr>\n"
    for vv in statsvotes:
        print "<tr>\n<th>" + vv.upper() + "</th>\n"
        for rr in statsresults:
            print "<td>" + str(stats[vv+rr]) + "</td>\n"
        print "</tr>\n"
    print "</table><br>"
    
    print """<br><br>
<table border=1>
<tr>
<th>Page</th>
<th>Date</th>
<th>Vote</th>
<th>Result</th>
</tr>
"""
    for i in tablelist:
        print "<tr>\n"
        print "<td>" + link(i[0]) + "</td>\n"
        print "<td>" + i[2] + "</td>\n"
        if i[4] == 1:
            print "<td>" + i[1] + " (Nom)</td>\n"
        else:
            print "<td>" + i[1] + "</td>\n"
        print "<td>" + i[3] + "</td>\n"
        print "</tr>\n"
    print "</table>\n"

#Print out accuracy table too

main()
print "</BODY>\n</HTML>"

