#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
import sys
import os
import traceback
import cgi
import urllib
import re
import datetime
import time
import htmllib

starttime = time.time()
voteregex = re.compile("\n#(?!(?:<s>|:)).*?\(UTC\)", re.IGNORECASE) #may need to add "{{unsigned" and "<span class="autosigned"> as optional terminators to reduce errors due to idiots not signing their votes
userregex = re.compile("\[\[User.*?:(.*?)(?:\||/|(?:\]\]))", re.IGNORECASE)
timeregex = re.compile("(\d{2}:\d{2}, .*?) \(UTC\)")
timeparseregex = re.compile("\d{2}:\d{2}, (\d{1,2}) ([A-Za-z]*) (\d{4})")
timeunparseregex = re.compile("([A-Za-z]*) (\d{1,2}), (\d{4})")
timestampparseregex = re.compile("(\d{4})-(\d{2})-(\d{2})")
monthmap = {"01":"January", "02":"February", "03":"March", "04":"April", "05":"May", "06":"June", "07":"July", "08":"August", "09":"September", "10":"October", "11":"November", "12":"December"}
username = ""
maxsearch = 50
maxlimit = 250
startdate = ""
altusername = ""
showall = False
matchstats = [0,0]  #matches, non-matches
votecounts = [0,0,0,0] #supports, opposes, neutrals, comments/unparseables
tablelist = []


def main():
    global username
    global maxsearch
    global maxlimit
    global startdate
    global altusername
    global showall
    print """<!doctype html>
<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
<LINK href="greyscale.css" rel="stylesheet" type="text/css">
<LINK href="menubar3.css" rel="stylesheet" type="text/css">
<TITLE>RfA Vote Counter</TITLE>
</HEAD>
<BODY id="no">
<script type="text/javascript" src="/menubar.js"></script>
<br>
<div style="width:875px;">
<a href="rfastats.html"><small>&larr;New search</small></a>
"""
    try:
        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        form = cgi.FieldStorage()

        if "name" not in form:
            errorout("No name entered.")
        else:
            maxoverride = False
            if "key" in form:
                if form['key'].value == "thumpz":
                    maxoverride = True
            if "max" in form:
                try:
                    if maxoverride:
                        maxsearch = int(form['max'].value)
                    else:
                        maxsearch = min(maxlimit, int(form['max'].value))
                except:
                    maxsearch = 50
            if "startdate" in form:
                try:
                    startdate = form['startdate'].value
                    startdate = startdate.ljust(14, "0")
                    if len(startdate) != 14 or int(startdate) < 20000000000000 or int(startdate) > 20150000000000:
                        startdate = None
                except:
                    pass
            if "altname" in form:
                altusername = form['altname'].value
                
            if os.environ["REMOTE_ADDR"].startswith("89.151.116.5"):
                errorout("Your IP address has been flagged for potential abuse.  Please post a message to User talk:Scottywong on the English Wikipedia, or alternatively send an email to snottywong.wiki@gmail.com to prove that you are a human, and to explain why you've been consistently making so many queries on this tool.")

            try:
                username = form['name'].value.replace("_", " ").replace("+", " ")
                username = username[0].capitalize() + username[1:]
                f = open("rfastatslog.txt", "a")
                f.write("<log><ip>" + os.environ["REMOTE_ADDR"] + "</ip><username>" + username + "</username><max>" + str(maxsearch) + "</max><timestamp>" + datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</timestamp>" + ("<startdate>" + startdate + "</startdate>" if startdate else "") + ("<altname>" + altusername + "</altname>" if altusername else "") + "</log>\n")
                f.close()
                cursor.execute(u'SELECT user_id FROM user WHERE user_name=%s;', (username))
                userid = cursor.fetchall()[0][0]
            except:
                #errorout("Username not found." + traceback.print_exc(file=sys.stdout))
                errorout("Username not found.")
            if "showall" in form:
                if form['showall'].value.lower() == "true":
                    showall = True
                
        cursor = db.cursor()
        if startdate:
            cursor.execute("""
SELECT DISTINCT page_title
FROM revision JOIN page ON rev_page=page_id
WHERE rev_user=%s
AND page_namespace=4
AND page_title LIKE "Requests_for_adminship/%%"
AND rev_timestamp<=%s
ORDER BY rev_timestamp DESC;""",
            (userid, startdate)
                           )
        else:
            cursor.execute("""
SELECT DISTINCT page_title
FROM revision JOIN page ON rev_page=page_id
WHERE rev_user=%s
AND page_namespace=4
AND page_title LIKE "Requests_for_adminship/%%"
ORDER BY rev_timestamp DESC;""",
            (userid)
                           )
            
        results = cursor.fetchall()
        db.close()

        print "<div style=\"width:875px;\"><h1>RfA voting statistics for User:" + username + "</h1>\n"
        if len(results) == 0:
            errorout("No RfA's found.  Try a different date range.  Also, note that if the user's username does not appear in the wikitext of their signature, you may need to specify an alternate name.")
        else:
            print "These statistics were compiled by an automated process, and may contain errors or omissions due to the wide variety of styles with which people cast votes at RfA.\n"
            print "<br><h2>Vote totals</h2>\n"
            datestr = ""
            if startdate:
                datestr = " from " + startdate[4:6] + "/" + startdate[6:8] + "/" + startdate[:4] + " and earlier"
            print "Total number of unique RfA pages edited by " + username + datestr + ": " + str(len(results)) + "<br>\n"
            print "Analyzed the last " + str(min(maxsearch, len(results))) + " votes by this user.<br>\n"
            analyze(results[:min(maxsearch, len(results))])
            printtable()
        elapsed = time.time() - starttime
        print "</div>\n<br><br><small>Elapsed time: " + str(round(elapsed, 2)) + " seconds.<br>\n"
        print datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</small><br>"
    except SystemExit:
        pass
    except:
        errorout("Unhandled exception.<br><br>" + traceback.print_exc(file=sys.stdout))

def analyze(pages):
    global tablelist
    global votecounts
    if len(pages) <= 50:
        alldata = APIgetlotsofpages(pages)
    else:
        alldata = {}
        for i in range(0, len(pages), 50):
            newdata = APIgetlotsofpages(pages[i:min(i+50, len(pages))])
            alldata = dict(alldata.items() + newdata.items())
    for entry in pages:
        try:
            page = entry[0]
            data = alldata["Wikipedia:" + page.replace("_", " ")]
            result = findresults(data[:data.find("==Nomination==")])
            if data.find("\n=====Support=====") >= 0:
                supportvotes = voteregex.findall(data[data.find("\n=====Support====="):data.find("\n=====Oppose=====")])
                opposevotes = voteregex.findall(data[data.find("\n=====Oppose====="):data.find("\n=====Neutral=====")])
                neutralvotes = voteregex.findall(data[data.find("\n=====Neutral====="):])
            else:
                supportvotes = voteregex.findall(data[data.find("\n'''Support'''"):data.find("\n'''Oppose'''")])    #Older style of formatting
                opposevotes = voteregex.findall(data[data.find("\n'''Oppose'''"):data.find("\n'''Neutral'''")])
                neutralvotes = voteregex.findall(data[data.find("\n'''Neutral'''"):])
                
            foundvote = False
            
            for vote in supportvotes:
                if vote.lower().rfind("[[user", 0, vote.lower().rfind("[[user")) == -1:
                    votermatch = userregex.match(vote[vote.lower().rfind("[[user"):])
                else:
                    votermatch = userregex.match(vote[vote.lower().rfind("[[user", 0, vote.lower().rfind("[[user")):])  #Most sigs have [[User:Foo|Foo]] [[User talk:Foo|(talk)]]
                if votermatch == None:
                    continue
                else:
                    voter = votermatch.group(1).strip().replace("_", " ")
                    if voter.lower() == username.lower() or voter.lower() == altusername.lower():     #found our user's vote
                        timematch = timeregex.search(vote)
                        if timematch == None:
                            votetime = ""
                        else:
                            votetime = parsetime(timematch.group(1))
                        tablelist.append((page, "Support", votetime, result, match("Support", result)))
                        votecounts[0] += 1
                        foundvote = True
                        break

            if not foundvote:
                for vote in opposevotes:
                    if vote.lower().rfind("[[user", 0, vote.lower().rfind("[[user")) == -1:
                        votermatch = userregex.match(vote[vote.lower().rfind("[[user"):])
                    else:
                        votermatch = userregex.match(vote[vote.lower().rfind("[[user", 0, vote.lower().rfind("[[user")):])  #Most sigs have [[User:Foo|Foo]] [[User talk:Foo|(talk)]]
                    if votermatch == None:
                        continue
                    else:
                        voter = votermatch.group(1).strip()
                        if voter.lower() == username.lower() or voter.lower() == altusername.lower():     #found our user's vote
                            timematch = timeregex.search(vote)
                            if timematch == None:
                                votetime = ""
                            else:
                                votetime = parsetime(timematch.group(1))
                            tablelist.append((page, "Oppose", votetime, result, match("Oppose", result)))
                            votecounts[1] += 1
                            foundvote = True
                            break

            if not foundvote:
                for vote in neutralvotes:
                    if vote.lower().rfind("[[user", 0, vote.lower().rfind("[[user")) == -1:
                        votermatch = userregex.match(vote[vote.lower().rfind("[[user"):])
                    else:
                        votermatch = userregex.match(vote[vote.lower().rfind("[[user", 0, vote.lower().rfind("[[user")):])  #Most sigs have [[User:Foo|Foo]] [[User talk:Foo|(talk)]]
                    if votermatch == None:
                        continue
                    else:
                        voter = votermatch.group(1).strip()
                        if voter.lower() == username.lower() or voter.lower() == altusername.lower():     #found our user's vote
                            timematch = timeregex.search(vote)
                            if timematch == None:
                                votetime = ""
                            else:
                                votetime = parsetime(timematch.group(1))
                            tablelist.append((page, "Neutral", votetime, result, match("Neutral", result)))
                            votecounts[2] += 1
                            foundvote = True
                            break
                        
            if not foundvote:       #The user edited this page but didn't vote, or vote wasn't parseable
                votecounts[3] += 1
                if showall:
                    tablelist.append((page, "Comments", None, result, None))

        except:
            #errorout("Fatal error while parsing votes.<br>" + traceback.print_exc(file=sys.stdout))
            continue

def findresults(thepage):
    if "The following discussion is preserved as an archive of a [[wikipedia:requests for adminship|request for adminship]] that '''did not succeed'''" in thepage:
        return "Unsuccessful"
    elif "The following discussion is preserved as an archive of a '''successful''' [[wikipedia:requests for adminship|request for adminship]]" in thepage:
        return "Successful"
    else:
        return "Not closed yet"
        

def parsetime(t):
    tm = timeparseregex.search(t)
    if tm == None:
        return ""
    else:
        return tm.group(2) + " " + tm.group(1) + ", " + tm.group(3)

def match(v, r):
    if r == "Not closed yet":
        return None
    if v == "Neutral":
        return None
    if v == "Support" and r == "Successful":
        matchstats[0] += 1
        return True
    if v == "Oppose" and r == "Unsuccessful":
        matchstats[0] += 1
        return True
    matchstats[1] += 1
    return False

def APIgetlotsofpages(rawpagelist):
    try:
        p = ''
        for page in rawpagelist:
            p += urllib.quote("Wikipedia:" + page[0].replace("_", " ") + "|")
        u = urllib.urlopen("http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=xml&titles=" + p[:-3])
        xml = u.read()
        u.close()
        pagelist = re.findall(r'<page.*?>.*?</page>', xml, re.DOTALL)
        pagedict = {}
        for i in pagelist:
            try:
                pagename = re.search(r'<page.*?title=\"(.*?)\">', i).group(1)
                text = re.search(r'<rev.*?xml:space="preserve">(.*?)</rev>', i, re.DOTALL).group(1)
                pagedict[unescape(pagename)] = text
            except:
                #print sys.exc_info()[0]
                #print "<br>"
                #print traceback.print_exc(file=sys.stdout)
                #print "<br>"
                continue
        return pagedict
    except:
        #print sys.exc_info()[0]
        #print "<br>"
        #print traceback.print_exc(file=sys.stdout)
        #print "<br>"
        errorout("Error getting RfA pages from API.  Please try again later.")

def link(p):
    text = cgi.escape(p.replace("_", " ")[23:])
    if len(text) > 64:
        text = text[:61] + "..."
    return '<a href="http://en.wikipedia.org/wiki/Wikipedia:' + urllib.quote(p) + '">' + text + '</a>'

def unescape(s):
    p = htmllib.HTMLParser(None)
    p.save_bgn()
    p.feed(s)
    return p.save_end()

def datefmt(datestr):
    tg = timeunparseregex.search(datestr)
    if tg == None:
        return
    month = [k for k,v in monthmap.items() if v==tg.group(1)][0]
    day = tg.group(2)
    year = tg.group(3)
    if len(day) == 1:
        day = "0" + day
    return year + month + day

def errorout(errorstr): #prints error string and exits
    print "<br><br>ERROR: " + errorstr + "<br><br>Please try again.<br><br>"
    print "</div></BODY>\n</HTML>"
    sys.exit(0)

def printtable():
    global votecounts
    print "<ul>\n"
    totalvotes = sum(votecounts)
    print "<li>Support votes: " + str(votecounts[0]) + " (" + ("0" if totalvotes==0 else str(round(100.0 * votecounts[0] / totalvotes, 1))) + "%)</li>"
    print "<li>Oppose votes: " + str(votecounts[1]) + " (" + ("0" if totalvotes==0 else str(round(100.0 * votecounts[1] / totalvotes, 1))) + "%)</li>"
    print "<li>Neutral votes: " + str(votecounts[2]) + " (" + ("0" if totalvotes==0 else str(round(100.0 * votecounts[2] / totalvotes, 1))) + "%)</li>"
    print "<li>Comments or unparseable votes: " + str(votecounts[3]) + " (" + ("0" if totalvotes==0 else str(round(100.0 * votecounts[3] / totalvotes, 1))) + "%)</li>"
    if sum(matchstats):
        print "<li>This user's vote matched the end result of the RfA " + str(matchstats[0]) + " times, or " + str(round(100.0 * matchstats[0] / sum(matchstats), 1)) + "% of the time.</li>"
    print "</ul><br>"

    print "<h2>Individual RfA's</h2><br>"

    if len(tablelist) > 0 and tablelist[-1][2] and sum(votecounts) == maxsearch:
        print '<a href="cgi-bin/rfastats.cgi?name=' + username.replace(" ", "_") + '&max=' + str(maxsearch) + '&startdate=' + datefmt(tablelist[-1][2]) + '&altname=' + altusername + ('&showall=true' if showall else '') + '"><small>Next ' + str(maxsearch) + " votes &rarr;</small></a><br>"
    print """</div>
<table>
<thead>
<tr>
<th scope="col">RfA</th>
<th scope="col">Date</th>
<th scope="col">Vote</th>
<th scope="col">Result</th>
</tr>
</thead>
<tbody>
"""

    for i in tablelist:
        print "<tr>\n"
        print "<td>" + link(i[0]) + "</td>"
        print "<td>" + (i[2] if i[2] else "N/A") + "</td>"
        print "<td>" + i[1] + "</td>"
        if i[4] == True:
            print '<td class="y">' + i[3] + '</td>'
        elif i[4] == False:
            print '<td class="n">' + i[3] + '</td>'
        elif i[4] == None:
            print '<td class="m">' + i[3] + '</td>'
        print "</tr>"
    print "</tbody>\n</table>\n"
    if len(tablelist) > 0 and tablelist[-1][2] and sum(votecounts) == maxsearch:
        print '<a href="cgi-bin/rfastats.cgi?name=' + username.replace(" ", "_") + '&max=' + str(maxsearch) + '&startdate=' + datefmt(tablelist[-1][2]) + '&altname=' + altusername + ('&showall=true' if showall else '') + '"><small>Next ' + str(maxsearch) + " votes &rarr;</small></a><br>"


main()
print '<small>Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Snottywong">User talk:Snottywong</a></small><br>'
print '<a href="rfastats.html"><small>&larr;New search</small></a>'
print "</div></BODY>\n</HTML>"
