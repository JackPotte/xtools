#!/usr/bin/env python
# -*- coding: utf-8 -*-

#TO DO:
#Improve voteregex to catch unsigned votes

#Admin stats changes:
# Check if admin, warn if not (but still allow checks for NAC's)
# Get all AfD's as normal
# Check that each AfD is actually closed, throw out ones still open
# Develop regex to determine who closed it, throw out ones not closed by user
# Determine closing result, as well as number of votes of each type
#Display stats:
##Number of AfD's closed as Keep, Delete, etc. with percentages
##Table showing each AfD, # of each type of vote, and closing result
##Green if closing result matches majority vote, red if not (with consensus explanation)
##Number of AfD's closed with/against majority vote and percentages


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
voteregex = re.compile("'{3}?.*?'{3}?.*?\(UTC\)", re.IGNORECASE) #may need to add "{{unsigned" and "<span class="autosigned"> as optional terminators to reduce errors due to idiots not signing their votes
userregex = re.compile("\[\[User.*?:(.*?)(?:\||(?:\]\]))", re.IGNORECASE)
resultregex = re.compile("The result (?:of the debate )?was(?:.*?)(?:'{3}?)(.*?)(?:'{3}?)", re.IGNORECASE)
closerregex = re.compile("\nThe result (?:of the debate )?was.*?\[\[User.*?:(.*?)(?:\||(?:\]\]))", re.IGNORECASE)  #may get confused if the closer links to a user's page in their closing statement
timeregex = re.compile("(\d{2}:\d{2}, .*?) \(UTC\)")
timeparseregex = re.compile("\d{2}:\d{2}, (\d{1,2}) ([A-Za-z]*) (\d{4})")
timeunparseregex = re.compile("([A-Za-z]*) (\d{1,2}), (\d{4})")
timestampparseregex = re.compile("(\d{4})-(\d{2})-(\d{2})")
drvregex = re.compile("(?:(?:\{\{delrev xfd)|(?:\{\{delrevafd)|(?:\{\{delrevxfd))(.*?)\}\}", re.IGNORECASE)
drvdateregex = re.compile("\|date=(\d{4} \w*? \d{1,2})", re.IGNORECASE)
drvpageregex = re.compile("\|page=(.*?)(?:\||$)", re.IGNORECASE)
monthmap = {"01":"January", "02":"February", "03":"March", "04":"April", "05":"May", "06":"June", "07":"July", "08":"August", "09":"September", "10":"October", "11":"November", "12":"December"}
username = ""
maxsearch = 50
maxlimit = 250
startdate = ""
altusername = ""
matchstats = [0,0,0]  #matches, non-matches, no consensus
closestats = [0,0,0,0,0,0,0,0,0,0]  #Keep, Delete, SK, SD, Merge, Redirect, Transwiki, Userfy, No Consensus, UNDETERMINED
drvcount = 0
tablelist = []

def main():
    global username
    global maxsearch
    global maxlimit
    global startdate
    global altusername
    tehdate = ""
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
                    try:
                        maxsearch = min(maxlimit, int(form['max'].value))
                    except:
                        maxsearch = 50
                if "startdate" in form:
                    try:
                        tehdate = str(form['startdate'].value)
                        if len(tehdate) != 8 or int(tehdate) < 20000000 or int(tehdate) > 20150000:
                            pass
                        else:
                            startdate = " AND rev_timestamp<=" + str(form['startdate'].value) + "235959"
                    except:
                        pass
                if "altname" in form:
                    altusername = urllib.unquote(form['altname'].value)
                username = form['name'].value.replace("_", " ").replace("+", " ")
                username = urllib.unquote(username)
                username = username[0].capitalize() + username[1:]

                if os.environ["REMOTE_ADDR"].startswith("89.151.116.5"):
                    sys.exit(0)
                    
                f = open("afdadminstatslog.txt", "a")
                f.write("<log><ip>" + os.environ["REMOTE_ADDR"] + "</ip><username>" + username + "</username><max>" + str(maxsearch) + "</max><timestamp>" + datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</timestamp>" + ("<startdate>" + tehdate + "</startdate>" if startdate else "") + ("<altname>" + altusername + "</altname>" if altusername else "") + "</log>\n")
                f.close()
                cursor.execute(u'SELECT user_id FROM user WHERE user_name=%s;', (username))
                userid = cursor.fetchall()[0][0]
            except:
                #print sys.exc_info()[0]
                #print "<br>"
                #print traceback.print_exc(file=sys.stdout)
                #print "<br>"
                print "Username not found."
                errors = True
        if not errors:
            cursor = db.cursor()
            cursor.execute(u'SELECT DISTINCT page_title FROM revision JOIN page ON rev_page=page_id WHERE rev_user=' + str(userid) + ' AND page_namespace=4 AND page_title LIKE "Articles_for_deletion%" AND NOT page_title LIKE "Articles_for_deletion/Log/%"' + startdate + ' ORDER BY rev_timestamp DESC;')
            results = cursor.fetchall()
            #results = tuple(reversed(results))
            db.close()
            print """<!doctype html>
<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
<LINK href="greyscale.css" rel="stylesheet" type="text/css">
<LINK href="menubar3.css" rel="stylesheet" type="text/css">
<TITLE>AfD Closure Stats</TITLE>
</HEAD>
<BODY style="background-color:#DDEEEE;">
<script type="text/javascript" src="/menubar.js"></script>
<br>
<a href="afdadminstats.html"><small>&larr;New search</small></a>
"""
            print "<div style=\"width:875px;\"><h1>AfD closure statistics for User:" + username + "</h1>\n"
            if len(results) == 0:
                print "No AfD's found.  Try a different date range.  Also, note that if the user's username does not appear in the wikitext of their signature, you may need to specify an alternate name.<br>\n"
            else:
                print "These statistics were compiled by an automated process, and may contain errors or omissions due to the wide variety of styles with which people cast votes at AfD.  Any result fields which contain \"UNDETERMINED\" were not able to be parsed, and should be examined manually.  Also note that while this tool analyzes statistics for how often an admin's closure matches the majority vote at an AfD, this is not necessarily an accurate measure of whether or not the admin is doing a good job.  An admin's job is to assess the consensus of a deletion discussion, which may or may not be in line with the majority vote.\n"
                print "<br><h2>AfD closing totals</h2>\n"
                if not APIcheckadmin(username):
                    print "<b>Warning: This user is not an administrator.  This tool will only check for non-admin closures.</b><br><br>"
                datestr = ""
                if startdate:
                    tehdate = str(form["startdate"].value)
                    datestr = " from " + tehdate[4:6] + "/" + tehdate[6:8] + "/" + tehdate[:4] + " and earlier"
                print "Total number of unique AfD pages edited by " + username + datestr + ": " + str(len(results)) + "<br>\n"
                print "Analyzed the last " + str(min(maxsearch, len(results))) + " AfD pages edited by this user.<br>\n"
                analyze(results[:min(maxsearch, len(results))])
                if len(tablelist) == 0:
                    print "<br>No AfD closures found.  Try searching for more AfD's or search through an earlier date range.<br>"
                else:
                    printtable(str(min(maxsearch, len(results))))
            elapsed = time.time() - starttime
            print "</div>\n<br><br><small>Elapsed time: " + str(round(elapsed, 2)) + " seconds.<br>\n"
            print datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</small><br>"
    except:
        print sys.exc_info()[0]
        print "<br>"
        print traceback.print_exc(file=sys.stdout)
        print "<br><br>Unspecified error.<br><br>"
        pass

def analyze(pages):
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
            try:
                data = alldata["Wikipedia:" + page.replace("_", " ")]
            except:
                continue
            if "The following discussion is an archived debate of the proposed deletion of the article below" not in data and "This page is an archive of the proposed deletion of the article below." not in data and "'''This page is no longer live.'''" not in data:
                continue  #AfD not closed yet
            thecloser = findcloser(data)
            if thecloser != username.lower() and thecloser != altusername.lower():
                continue  #AfD wasn't closed by this user 
            votes = voteregex.findall(data[data.find("=="):])
            result = findresults(data[:max(data.find("=="), data.find("(UTC)"))])
            votecounts = [0,1,0,0,0,0,0,0] #Keep, Delete, SK, SD, Merge, Redirect, Transwiki, Userfy (nom always counts as a delete)
            timematch = timeregex.search(data[:data.find("==")])
            if timematch == None:
                closuretime = ""
            else:
                closuretime = parsetime(timematch.group(1))
            for vote in votes:
                try:
                    votetype = parsevote(vote[3:vote.find("'", 3)])
                    if votetype == None:
                        continue
                    votecounts[votetype] += 1
                except:
                    print sys.exc_info()[0]
                    print "<br>"
                    print traceback.print_exc(file=sys.stdout)
                    continue
            tablelist.append((page, result, votecounts, closuretime, findDRV(data[:data.find("==")], page)))
        except:
            print sys.exc_info()[0]
            print "<br>"
            print traceback.print_exc(file=sys.stdout)
            continue


def findDRV(thepage, pagename):
    global drvcount
    try:
        drvs = ""
        drvcounter = 0
        for drv in drvregex.finditer(thepage):
            drvdate = drvdateregex.search(drv.group(1))
            if drvdate:
                drvcounter += 1
                name = drvpageregex.search(drv.group(1))
                if name:
                    nametext = urllib.quote(name.group(1))
                else:
                    nametext = urllib.quote(pagename.replace("Articles_for_deletion/", "", 1))
                drvs += '<a href="http://en.wikipedia.org/wiki/Wikipedia:Deletion_review/Log/' + drvdate.group(1).strip().replace(" ", "_") + '#' + nametext + '">[' + str(drvcounter) + ']</a> '
        if drvs:
            drvcount += 1
        return drvs
    except:
        print sys.exc_info()[0]
        print "<br>"
        print traceback.print_exc(file=sys.stdout)
        print "findDRV error"
        return ""


def parsevote(v):
    v = v.lower()
    if "comment" in v:
        return None
    elif "note" in v:
        return None
    elif "merge" in v:
        return 4
    elif "redirect" in v:
        return 5
    elif "speedy keep" in v:
        return 2
    elif "speedy delete" in v:
        return 3
    elif "keep" in v:
        return 0
    elif "delete" in v:
        return 1
    elif "transwiki" in v:
        return 6
    elif ("userfy" in v) or ("userfied" in v) or ("incubat" in v):
        return 7
    else:
        return None

def findresults(thepage):
    resultsearch = resultregex.search(thepage)
    if resultsearch == None:
        if "The following discussion is an archived debate of the proposed deletion of the article below" in thepage or "This page is an archive of the proposed deletion of the article below." in thepage or "'''This page is no longer live.'''" in thepage:
            return "UNDETERMINED"
        else:
            return "Not closed yet"
    else:
        result = resultsearch.group(1).lower()
        if "no consensus" in result:
            closestats[8] += 1
            return "No Consensus"
        elif "merge" in result:
            closestats[4] += 1
            return "Merge"
        elif "redirect" in result:
            closestats[5] += 1
            return "Redirect"
        elif "speedy keep" in result or "speedily kept" in result or "speedily keep" in result or "snow keep" in result or "snowball keep" in result or "speedy close" in result:
            closestats[2] += 1
            return "Speedy Keep"
        elif "speedy delete" in result or "speedily deleted" in result or "snow delete" in result or "snowball delete" in result:
            closestats[3] += 1
            return "Speedy Delete"
        elif "keep" in result:
            closestats[0] += 1
            return "Keep"
        elif "delete" in result:
            closestats[1] += 1
            return "Delete"
        elif "transwiki" in result:
            closestats[6] += 1
            return "Transwiki"
        elif ("userfy" in result) or ("userfied" in result) or ("incubat" in result):
            closestats[7] += 1
            return "Userfy"
        elif "withdraw" in result:
            closestats[2] += 1
            return "Speedy Keep"
        else:
            closestats[9] += 1
            return "UNDETERMINED"

def findcloser(thepage):
    closersearch = closerregex.search(thepage)
    if closersearch == None:
        return None
    else:
        return closersearch.group(1).lower()

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

def matchclose(r, votelist):
    maxvotes = maxindex(votelist)
    if r == "No Consensus":
        matchstats[2] += 1
        return ('<td class="m">' + r + '</td>', "mm")
    elif r == "UNDETERMINED":
        return ('<td class="m">' + r + '</td>', "mm")
    elif r == "Keep" and (0 in maxvotes or 2 in maxvotes):
        matchstats[0] += 1
        return ('<td class="y">' + r + '</td>', "yy")
    elif r == "Delete" and (1 in maxvotes or 3 in maxvotes or 5 in maxvotes):
        matchstats[0] += 1
        return ('<td class="y">' + r + '</td>', "yy")
    elif r == "Speedy Keep" and (0 in maxvotes or 2 in maxvotes):
        matchstats[0] += 1
        return ('<td class="y">' + r + '</td>', "yy")
    elif r == "Speedy Delete" and (1 in maxvotes or 3 in maxvotes):
        matchstats[0] += 1
        return ('<td class="y">' + r + '</td>', "yy")
    elif r == "Merge" and (4 in maxvotes or 5 in maxvotes):
        matchstats[0] += 1
        return ('<td class="y">' + r + '</td>', "yy")
    elif r == "Redirect" and (4 in maxvotes or 5 in maxvotes or 1 in maxvotes):
        matchstats[0] += 1
        return ('<td class="y">' + r + '</td>', "yy")
    elif r == "Transwiki" and (6 in maxvotes):
        matchstats[0] += 1
        return ('<td class="y">' + r + '</td>', "yy")
    elif r == "Userfy" and (7 in maxvotes):
        matchstats[0] += 1
        return ('<td class="y">' + r + '</td>', "yy")
    else:
        matchstats[1] += 1
        return ('<td class="n">' + r + '</td>', "nn")


def APIget(p):
    try:
        u = urllib.urlopen("http://en.wikipedia.org/w/api.php?action=query&prop=revisions&titles=Wikipedia:" + urllib.quote(p) + "&rvprop=content&format=xml")
        xml = u.read()
        u.close()
        text = re.search(r'<rev.*?xml:space="preserve">(.*?)</rev>', xml, re.DOTALL).group(1)
        return text
    except:
        #print sys.exc_info()[0]
        #print "<br>"
        #print traceback.print_exc(file=sys.stdout)
        #print "<br>"
        return None

def APIgetlotsofpages(rawpagelist):
    try:
        p = ''
        for page in rawpagelist:
            p += urllib.quote("Wikipedia:" + page[0].replace("_", " ") + "|", ":|")
        u = urllib.urlopen("http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=xml&titles=" + p[:-3])
        #print "http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=xml&titles=" + p[:-3] + "<br>"
        xml = u.read()
        u.close()
        pagelist = re.findall('<page.*?(?:(?:</page>)|(?:/>))', xml, re.DOTALL)
        pagedict = {}
        for i in pagelist:
            try:
                pagename = re.search(r'<page.*?title="(.*?)">', i).group(1)
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
        #print sys.exc_info()[0]
        #print "<br>"
        #print traceback.print_exc(file=sys.stdout)
        return None

def APIcheckadmin(name):
    try:
        u = urllib.urlopen("http://en.wikipedia.org/w/api.php?action=query&list=users&format=xml&usprop=rights&ususers=" + name)
        xml = u.read()
        u.close()
        if "<r>block</r>" in xml:
            return True
        return False
    except:
        #print sys.exc_info()[0]
        #print "<br>"
        #print traceback.print_exc(file=sys.stdout)
        return False

def link(p):
    text = cgi.escape(p.replace("_", " ")[22:])
    if len(text) > 64:
        text = text[:61] + "..."
    return '<a href="http://en.wikipedia.org/wiki/Wikipedia:' + urllib.quote(p) + '">' + text + '</a>'

def unescape(s):
    p = htmllib.HTMLParser(None)
    p.save_bgn()
    p.feed(s)
    return p.save_end()

def maxindex(vl):
    maxvalue = max(vl)
    maxindeces = []
    for i in range(len(vl)):
        if vl[i] == maxvalue:
            maxindeces.append(i)
    return maxindeces

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

def printtable(num):
    print "Out of the last " + num + " AfD's this user edited, I found " + str(len(tablelist)) + " which were closed by this user.<br>"
    print "<ul>\n"
    totalcloses = sum(closestats)
    print "<li>Keep closes: " + str(closestats[0]) + " (" + str(round((100.0*closestats[0]) / totalcloses, 1)) + "%)</li>"
    print "<li>Delete closes: " + str(closestats[1]) + " (" + str(round((100.0*closestats[1]) / totalcloses, 1)) + "%)</li>"
    print "<li>Speedy Keep closes: " + str(closestats[2]) + " (" + str(round((100.0*closestats[2]) / totalcloses, 1)) + "%)</li>"
    print "<li>Speedy Delete closes: " + str(closestats[3]) + " (" + str(round((100.0*closestats[3]) / totalcloses, 1)) + "%)</li>"
    print "<li>Merge closes: " + str(closestats[4]) + " (" + str(round((100.0*closestats[4]) / totalcloses, 1)) + "%)</li>"
    print "<li>Redirect closes: " + str(closestats[5]) + " (" + str(round((100.0*closestats[5]) / totalcloses, 1)) + "%)</li>"
    print "<li>Transwiki closes: " + str(closestats[6]) + " (" + str(round((100.0*closestats[6]) / totalcloses, 1)) + "%)</li>"
    print "<li>Userfy closes: " + str(closestats[7]) + " (" + str(round((100.0*closestats[7]) / totalcloses, 1)) + "%)</li>"
    print "<li>No Consensus closes: " + str(closestats[8]) + " (" + str(round((100.0*closestats[8]) / totalcloses, 1)) + "%)</li>"
    print "</ul><br>\n"

    printstr = "<h2>Individual AfD's</h2><br>\n"
    printstr += '<a href="cgi-bin/afdadminstats.cgi?name=' + username.replace(" ", "_") + '&max=' + str(maxsearch) + '&startdate=' + datefmt(tablelist[-1][3]) + '&altname=' + altusername + '"><small>Next ' + str(maxsearch) + " AfD's &rarr;</small></a><br>"
    printstr += """<table>
<thead>
<tr>
<th scope="col" rowspan="2">Page</th>
<th scope="col" rowspan="2">Date</th>
<th scope="col" rowspan="2">Result</th>
<th scope="col" colspan="8">Votes</th>
<th scope="col" rowspan="2">DRV's</th>
</tr>
<tr>
<th scope="col">K</th>
<th scope="col">D</th>
<th scope="col">SK</th>
<th scope="col">SD</th>
<th scope="col">M</th>
<th scope="col">R</th>
<th scope="col">T</th>
<th scope="col">U</th>
</tr>
</thead>
<tbody>\n"""

    for i in tablelist: #(page, result, votecounts, closuretime, drvs)
        printstr += "<tr>\n"
        printstr += "<td>" + link(i[0]) + "</td>\n"
        printstr += "<td>" + i[3] + "</td>\n"
        matchymatch = matchclose(i[1], i[2])
        printstr += matchymatch[0]
        for j in i[2]:
            if j == max(i[2]):
                printstr += '<td class="' + matchymatch[1] + '">' + str(j) + "</td>\n"
            else:
                printstr += "<td>" + str(j) + "</td>\n"
        printstr += "<td>" + i[4] + "</td>\n"
        printstr += "</tr>\n"
    printstr += "</tbody>\n</table>\n"
    printstr += '<a href="cgi-bin/afdadminstats.cgi?name=' + username.replace(" ", "_") + '&max=' + str(maxsearch) + '&startdate=' + datefmt(tablelist[-1][3]) + '&altname=' + altusername + '"><small>Next ' + str(maxsearch) + " AfD's &rarr;</small></a><br>"
    if sum(matchstats):
        print "Number of AfD's where close matched majority vote: " + str(matchstats[0]) + " (" + str(round((100.0*matchstats[0]) / sum(matchstats), 1)) + "%)<br>"
        print "Number of AfD's where close didn't match majority vote: " + str(matchstats[1]) + " (" + str(round((100.0*matchstats[1]) / sum(matchstats), 1)) + "%)<br>"
        print "Number of AfD's where result was \"No Consensus\": " + str(matchstats[2]) + " (" + str(round((100.0*matchstats[2]) / sum(matchstats), 1)) + "%)<br><br>\n"
        print "Number of AfD's subsequently brought to Deletion Review (DRV): " + str(drvcount) + "<br>\n"
    print printstr

main()
print '<small>Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Snottywong">User talk:Snottywong</a></small><br>'
print '<a href="afdadminstats.html"><small>&larr;New search</small></a>'
print "</BODY>\n</HTML>"


"""
select distinct page_title from revision join page on rev_page=page_id where rev_user_text="Scottywong" and page_namespace=4 and page_title like "Articles_for_deletion%" and not page_title like "Articles_for_deletion/Log/%" order by rev_timestamp desc limit 50;
"""
