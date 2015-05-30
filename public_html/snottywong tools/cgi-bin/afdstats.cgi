#!/usr/bin/env python
# -*- coding: utf-8 -*-

#TO DO:
#Improve voteregex to catch unsigned votes
#Add CSS classes to table, to make it look nicer, as well as to make green/red background for votes which were correct/incorrect, and for diagonals on vote matrix
#Add query string for start timestamp

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
voteregex = re.compile("'{3}?.*?'{3}?.*?(?:(?:\{\{unsigned.*?\}\})|(?:<!--\s*Template:Unsigned\s*-->)|(?:\[\[User.*?\]\].*?\(UTC\)))", re.IGNORECASE) #may need to add "{{unsigned" and "<span class="autosigned"> as optional terminators to reduce errors due to idiots not signing their votes
userregex = re.compile("\[\[User.*?:(.*?)(?:\||(?:\]\]))", re.IGNORECASE)
resultregex = re.compile("The result (?:of the debate )?was(?:.*?)(?:'{3}?)(.*?)(?:'{3}?)", re.IGNORECASE)
timeregex = re.compile("(\d{2}:\d{2}, .*?) \(UTC\)")
timeparseregex = re.compile("\d{2}:\d{2}, (\d{1,2}) ([A-Za-z]*) (\d{4})")
timeunparseregex = re.compile("([A-Za-z]*) (\d{1,2}), (\d{4})")
timestampparseregex = re.compile("(\d{4})-(\d{2})-(\d{2})")
drvregex = re.compile("(?:(?:\{\{delrev xfd)|(?:\{\{delrevafd)|(?:\{\{delrevxfd))(.*?)\}\}", re.IGNORECASE)
drvdateregex = re.compile("\|date=(\d{4} \w*? \d{1,2})", re.IGNORECASE)
drvpageregex = re.compile("\|page=(.*?)(?:\||$)", re.IGNORECASE)
strikethroughregex = re.compile("<(s|strike|del)>.*?</(s|strike|del)>", re.IGNORECASE|re.DOTALL)
monthmap = {"01":"January", "02":"February", "03":"March", "04":"April", "05":"May", "06":"June", "07":"July", "08":"August", "09":"September", "10":"October", "11":"November", "12":"December"}
username = ""
maxsearch = 50
maxlimit = 250
startdate = ""
altusername = ""
matchstats = [0,0,0]  #matches, non-matches, no consensus
nomsonly = False

stats = {}
statsresults = ["k", "d", "sk", "sd", "m", "r", "t", "u", "nc"]
votetypes = ["Keep", "Delete", "Speedy Keep", "Speedy Delete", "Merge", "Redirect", "Transwiki", "Userfy"]
statsvotes = statsresults[:-1]
for v in statsvotes:
    for r in statsresults:
        stats[v+r] = 0
for v in votetypes:
    stats[v] = 0

tablelist = []

def main():
    global username
    global maxsearch
    global maxlimit
    global startdate
    global altusername
    global nomsonly
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
                if "key" in form:
                    if form['key'].value == "huggadugga":
                        maxsearch = int(form['max'].value)
                if "startdate" in form:
                    try:
                        tehdate = str(form['startdate'].value)
                        if len(tehdate) != 8 or int(tehdate) < 20000000 or int(tehdate) > 20150000:
                            pass
                        else:
                            startdate = " AND rev_timestamp<=" + str(form['startdate'].value) + "235959"
                    except:
                        pass
                if "nomsonly" in form:
                    if form['nomsonly'].value.lower() in ['1', 'true', 'yes']:
                        nomsonly = True
                if "altname" in form:
                    altusername = urllib.unquote(form.getvalue('altname'))
                username = form['name'].value.replace("_", " ").replace("+", " ")
                username = urllib.unquote(username)
                username = username[0].capitalize() + username[1:]
                if os.environ["REMOTE_ADDR"].startswith("89.151.116.5"):
                    sys.exit(0)
                    
                f = open("afdstatslog.txt", "a")
                f.write("<log><ip>" + os.environ["REMOTE_ADDR"] + "</ip><username>" + username + "</username><max>" + str(maxsearch) + "</max><timestamp>" + datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</timestamp>" + ("<startdate>" + tehdate + "</startdate>" if startdate else "") + ("<altname>" + altusername + "</altname>" if altusername else "") + ("<nomsonly>true</nomsonly>" if nomsonly else "") + "</log>\n")
                f.close()
                #cursor.execute(u'SELECT user_id FROM user WHERE user_name=%s;', (username))        #<--Stupid
                #userid = cursor.fetchall()[0][0]
            except:
                #print sys.exc_info()[0]
                #print "<br>"
                #print traceback.print_exc(file=sys.stdout)
                #print "<br>"
                print "Username not found."
                errors = True
        if not errors:
            cursor = db.cursor()
            if nomsonly:
                cursor.execute(u'SELECT page_title FROM revision JOIN page ON rev_page=page_id WHERE rev_user_text=%s AND page_namespace=4 AND page_title LIKE "Articles_for_deletion%%" AND NOT page_title LIKE "Articles_for_deletion/Log/%%" AND rev_parent_id=0' + startdate + ' ORDER BY rev_timestamp DESC;', (username))
            else:
                cursor.execute(u'SELECT DISTINCT page_title FROM revision JOIN page ON rev_page=page_id WHERE rev_user_text=%s AND page_namespace=4 AND page_title LIKE "Articles_for_deletion%%" AND NOT page_title LIKE "Articles_for_deletion/Log/%%"' + startdate + ' ORDER BY rev_timestamp DESC;', (username))
            results = cursor.fetchall()
            #results = tuple(reversed(results))
            db.close()
            print """<!doctype html>
<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
<LINK href="greyscale.css" rel="stylesheet" type="text/css">
<LINK href="menubar3.css" rel="stylesheet" type="text/css">
<TITLE>AfD Stats</TITLE>
</HEAD>
<BODY id="no">
<script type="text/javascript" src="/menubar.js"></script>
<br>
<div style="width:875px;">
<a href="afdstats.html"><small>&larr;New search</small></a>
"""
            #print "<BR><BR>Debugging: <XMP>" + username + "  " + altusername + "</XMP><BR><BR>"
            print "<div style=\"width:875px;\"><h1>AfD statistics for User:" + username + "</h1>\n"
            if len(results) == 0:
                print "No AfD's found.  Try a different date range.  Also, note that if the user's username does not appear in the wikitext of their signature, you may need to specify an alternate name.<br>\n"
            else:
                print "These statistics were compiled by an automated process, and may contain errors or omissions due to the wide variety of styles with which people cast votes at AfD.  Any result fields which contain \"UNDETERMINED\" were not able to be parsed, and should be examined manually.\n"
                print "<br><h2>Vote totals</h2>\n"
                datestr = ""
                if startdate:
                    tehdate = str(form["startdate"].value)
                    datestr = " from " + tehdate[4:6] + "/" + tehdate[6:8] + "/" + tehdate[:4] + " and earlier"
                print "Total number of unique AfD pages edited by " + username + datestr + ": " + str(len(results)) + "<br>\n"
                print "Analyzed the last " + str(min(maxsearch, len(results))) + " votes by this user.<br>\n"
                analyze(results[:min(maxsearch, len(results))])
                printtable()
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
            data = unescape(alldata["Wikipedia:" + page.replace("_", " ")])
            data = strikethroughregex.sub("", data)     #remove all struck-through text, so that it is ignored
            votes = voteregex.findall(data[data.find("=="):])
            result = findresults(data[:max(data.find("=="), data.find("(UTC)"))])
            dupvotes = []
            deletionreviews = findDRV(data[:data.find("==")], page)
            for vote in votes:
                try:
                    votermatch = userregex.match(vote[vote.rfind("[[User"):])
                    if votermatch == None:
                        continue
                    else:
                        voter = votermatch.group(1).strip()
                    #print "<XMP>" + page + "  " + voter + "  " + altusername + " " + str(altusername.lower()==voter.lower()) + "</XMP><BR>"
                    if voter.lower() == username.lower() or voter.lower() == altusername.lower():
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
                        dupvotes.append((page, votetype, votetime, result, 0, deletionreviews))
                except:
                    #print sys.exc_info()[0]
                    #print "<br>"
                    #print traceback.print_exc(file=sys.stdout)
                    continue
            if len(dupvotes) < 1:
                firsteditor = APIfirsteditor(page)
                if firsteditor:
                    if firsteditor[0].lower() == username.lower(): #user is nominator
                        tablelist.append((page, "Delete", firsteditor[1], result, 1, deletionreviews))
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
            #print sys.exc_info()[0]
            #print "<br>"
            #print traceback.print_exc(file=sys.stdout)
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
        if "The following discussion is an archived debate of the proposed deletion of the article below" in thepage or "This page is an archive of the proposed deletion of the article below." in thepage or "'''This page is no longer live.'''" in thepage:
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
        elif "speedy keep" in result or "speedily kept" in result or "speedily keep" in result or "snow keep" in result or "snowball keep" in result or "speedy close" in result:
            return "Speedy Keep"
        elif "speedy delete" in result or "speedily deleted" in result or "snow delete" in result or "snowball delete" in result:
            return "Speedy Delete"
        elif "keep" in result:
            return "Keep"
        elif "delete" in result:
            return "Delete"
        elif "transwiki" in result:
            return "Transwiki"
        elif ("userfy" in result) or ("userfied" in result) or ("incubat" in result):
            return "Userfy"
        elif "withdraw" in result:
            return "Speedy Keep"
        else:
            return "UNDETERMINED"

def findDRV(thepage, pagename):
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
                drvs += '<a href="http://en.wikipedia.org/wiki/Wikipedia:Deletion_review/Log/' + drvdate.group(1).strip().replace(" ", "_") + '#' + nametext + '"><sup><small>[' + str(drvcounter) + ']</small></sup></a>'
        return drvs
    except:
        #print sys.exc_info()[0]
        #print "<br>"
        #print traceback.print_exc(file=sys.stdout)
        #print "findDRV error"
        return ""
        

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

def match(v, r, drv):
    if r == "No Consensus":
        matchstats[2] += 1
        return '<td class="m">' + r + drv + '</td>'
    elif r == "Not closed yet":
        return '<td class="m">' + r + drv + '</td>'
    elif r == "UNDETERMINED":
        return '<td class="m">' + r + drv + '</td>'
    elif v == r:
        matchstats[0] += 1
        return '<td class="y">' + r + drv + '</td>'
    elif v == "Speedy Keep" and r == "Keep":
        matchstats[0] += 1
        return '<td class="y">' + r + drv + '</td>'
    elif r == "Speedy Keep" and v == "Keep":
        matchstats[0] += 1
        return '<td class="y">' + r + drv + '</td>'
    elif v == "Speedy Delete" and r == "Delete":
        matchstats[0] += 1
        return '<td class="y">' + r + drv + '</td>'
    elif r == "Speedy Delete" and v == "Delete":
        matchstats[0] += 1
        return '<td class="y">' + r + drv + '</td>'
    elif r == "Redirect" and v == "Delete":
        matchstats[0] += 1
        return '<td class="y">' + r + drv + '</td>'
    elif r == "Delete" and v == "Redirect":
        matchstats[0] += 1
        return '<td class="y">' + r + drv + '</td>'
    elif r == "Merge" and v == "Redirect":
        matchstats[0] += 1
        return '<td class="y">' + r + drv + '</td>'
    elif r == "Redirect" and v == "Merge":
        matchstats[0] += 1
        return '<td class="y">' + r + drv + '</td>'
    else:
        matchstats[1] += 1
        return '<td class="n">' + r + drv + '</td>'

def matrixmatch(v, r):
    if stats[v+r]:
        if r=="nc":
            return '<td class="mm">'
        elif v == r:
            return '<td class="yy">'
        elif v=="sk" and r=="k":
            return '<td class="yy">'
        elif v=="k" and r=="sk":
            return '<td class="yy">'
        elif v=="d" and r=="sd":
            return '<td class="yy">'
        elif v=="sd" and r=="d":
            return '<td class="yy">'
        elif v=="d" and r=="r":
            return '<td class="yy">'
        elif v=="r" and r=="d":
            return '<td class="yy">'
        elif v=="m" and r=="r":
            return '<td class="yy">'
        elif v=="r" and r=="m":
            return '<td class="yy">'
        else:
            return '<td class="nn">'
    else:
        if r=="nc":
            return '<td class="mmm">'
        elif v == r:
            return '<td class="yyy">'
        elif v=="sk" and r=="k":
            return '<td class="yyy">'
        elif v=="k" and r=="sk":
            return '<td class="yyy">'
        elif v=="d" and r=="sd":
            return '<td class="yyy">'
        elif v=="sd" and r=="d":
            return '<td class="yyy">'
        elif v=="d" and r=="r":
            return '<td class="yyy">'
        elif v=="r" and r=="d":
            return '<td class="yyy">'
        elif v=="m" and r=="r":
            return '<td class="yyy">'
        elif v=="r" and r=="m":
            return '<td class="yyy">'
        else:
            return '<td class="nnn">'
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
            p += urllib.quote("Wikipedia:" + page[0].replace("_", " ") + "|")
        #u = urllib.urlopen("http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=xml&titles=" + p[:-3])
        u = urllib.urlopen("http://en.wikipedia.org/w/api.php?action=query&prop=revisions|info&rvprop=content&format=xml&titles=" + p[:-3])
        xml = u.read()
        u.close()
        pagelist = re.findall(r'<page.*?>.*?</page>', xml, re.DOTALL)
        pagedict = {}
        for i in pagelist:
            try:
                pagename = re.search(r'<page.*?title=\"(.*?)\"', i).group(1)
                text = re.search(r'<rev.*?xml:space="preserve">(.*?)</rev>', i, re.DOTALL).group(1)
                if re.search('<page.*?redirect=\"\".*?>', i):    #AfD page is a redirect
                    continue
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

def datefmt(datestr):
    try:
        tg = timeunparseregex.search(datestr)
        if tg == None:
            return ""
        month = [k for k,v in monthmap.items() if v==tg.group(1)][0]
        day = tg.group(2)
        year = tg.group(3)
        if len(day) == 1:
            day = "0" + day
        return year + month + day
    except:
        return ""


def printtable():
    totalvotes = 0
    for i in votetypes:
        totalvotes += stats[i]
    if totalvotes > 0:
        print "<ul>\n"
        for i in votetypes:
            print "<li>" + i + " votes: " + str(stats[i]) + " (" + str(round((100.0*stats[i]) / totalvotes, 1)) + "%)</li>"
        print "</ul><br>\n"
        print """<h2>Voting matrix</h2>
This table compares the user's votes to the way the AfD eventually closed. The only AfD's included in this matrix are those that have already closed, where both the vote and result could be reliably determined. Results are across the top, and the user's votes down the side.  Green cells indicate "matches", meaning that the user's vote matched (or closely resembled) the way the AfD eventually closed, whereas red cells indicate that the vote and the end result did not match.<br>
<br></div>
<table border=1 style="float:left;" class="matrix">
<thead>
<tr>
<th colspan=2 rowspan=2></th>
<th colspan=9>Results</th>
</tr>
<tr>
"""
        for i in statsresults:
            print "<th>" + i.upper() + "</th>"
        print "</tr>"
        print "</thead>\n<tbody>"
        print "<tr><th rowspan=9>Votes</th></tr>"
        for vv in statsvotes:
            print "<tr>\n<th>" + vv.upper() + "</th>"
            for rr in statsresults:
                print matrixmatch(vv, rr) + str(stats[vv+rr]) + "</td>"
            print "</tr>"
        print "</tbody>"
        print "</table>"
        print """<br><div style="float:left;padding:20px;">
<small>Abbreviation key:
<br>K = Keep
<br>D = Delete
<br>SK = Speedy Keep
<br>SD = Speedy Delete
<br>M = Merge
<br>R = Redirect
<br>T = Transwiki
<br>U = Userfy
<br>NC = No Consensus</small></div>
<div style="clear:both;"></div><br><br>
<div style="width:875px;">"""
            
        printstr = "<h2>Individual AfD's</h2><br>\n"
        if len(tablelist) > 0 and tablelist[-1][2]:
            printstr += '<a href="cgi-bin/afdstats.cgi?name=' + username.replace(" ", "_") + '&max=' + str(maxsearch) + '&startdate=' + datefmt(tablelist[-1][2]) + '&altname=' + altusername + '"><small>Next ' + str(maxsearch) + " AfD's &rarr;</small></a><br>"
        printstr += """</div>
<table>
<thead>
<tr>
<th scope="col">Page</th>
<th scope="col">Date</th>
<th scope="col">Vote</th>
<th scope="col">Result</th>
</tr>
</thead>
<tbody>\n"""
        
        for i in tablelist:
            printstr += "<tr>\n"
            printstr += "<td>" + link(i[0]) + "</td>\n"
            printstr += "<td>" + i[2] + "</td>\n"
            if i[4] == 1:
                printstr += "<td>" + i[1] + " (Nom)</td>\n"
            else:
                printstr += "<td>" + i[1] + "</td>\n"
            printstr += match(i[1], i[3], i[5]) + "\n"
            printstr += "</tr>\n"
        printstr += "</tbody>\n</table>\n"
        printstr += '<div style="width:875px;">\n<a href="cgi-bin/afdstats.cgi?name=' + username.replace(" ", "_") + '&max=' + str(maxsearch) + '&startdate=' + datefmt(tablelist[-1][2]) + '&altname=' + altusername + '"><small>Next ' + str(maxsearch) + " AfD's &rarr;</small></a><br>"

        if sum(matchstats) > 0:
            print "Number of AfD's where vote matched result (green cells): " + str(matchstats[0]) + " (" + str(round((100.0*matchstats[0]) / sum(matchstats), 1)) + "%)<br>"
            print "Number of AfD's where vote didn't match result (red cells): " + str(matchstats[1]) + " (" + str(round((100.0*matchstats[1]) / sum(matchstats), 1)) + "%)<br>"
            print "Number of AfD's where result was \"No Consensus\" (yellow cells): " + str(matchstats[2]) + " (" + str(round((100.0*matchstats[2]) / sum(matchstats), 1)) + "%)<br>\n"
        print printstr
    else:
        print "<BR><BR>No votes found."

main()
print '<small>Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Snottywong">User talk:Snottywong</a></small><br>'
print '<a href="afdstats.html"><small>&larr;New search</small></a>'
print "</div></BODY>\n</HTML>"
