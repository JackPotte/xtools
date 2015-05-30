#!/usr/bin/env python
# -*- coding: utf-8 -*-

#TODO remove commented out material
#TODO Logging

import sys
import os
import traceback
import cgi
import re
import urllib
import htmllib
import datetime
import MySQLdb

page = ""

def main():
    global discussiontype
    global page
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
<H1>AfD Vote Counter</H1>"""


    try:
        form = cgi.FieldStorage()

        if "page" in form:
            page = form["page"].value
        else:
            errorout("Missing required parameter: page.")
            
        fast = True
        if "fast" in form:
            if form["fast"].value.lower() in ["no", "false", "0", "slow"]:
                fast = False

        if page == "":
            errorout("Missing required parameter: page.")

        page = urllib.unquote(page).replace("_", " ")

        if os.environ["REMOTE_ADDR"].startswith(("89.151.116.5", "46.236.24", "46.236.7")):
            errorout("Your IP address has been flagged for potential abuse.  Please post a message to User talk:Scottywong on the English Wikipedia, or alternatively send an email to snottywong.wiki@gmail.com to prove that you are a human, and to explain why you've been consistently making so many queries on this tool.")

        f = open("votecounterlog.txt", "a")
        f.write("<log><ip>" + os.environ["REMOTE_ADDR"] + "</ip><page>" + page + "</page><timestamp>" + datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</timestamp></log>\n")
        f.close()

        if not page.lower().startswith("wikipedia:articles for deletion/"):
            errorout("Requested page is not an AfD.")

        db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()

        data = APIget(page)

        data = unescape(data)
        data = re.sub("<(s|strike|del)>.*?</(s|strike|del)>", "", data, flags=re.IGNORECASE|re.DOTALL)  #remove all struck-through text, so that it is ignored
        #TODO remove commented out material
        #votes = re.findall("\n.*?'{3}?.*?'{3}?.*?\(UTC\)", data[data.find("=="):], re.IGNORECASE)

        """
        votes = []
        tempdata = data[data.find("=="):]
        while True:
            part = tempdata.partition("(UTC)")
            if not part[1]:
                break
            votes.append(part[0] + part[1])
            tempdata = part[2]
        """

        votes = []
        voteiter = re.finditer("'{3}?.*?'{3}?.*?((\[\[User.*?\]\].*?\(UTC\))|(\{\{unsigned.*?\}\})|(<!--\s*Template:Unsigned\s*-->))", data[data.find("=="):], re.IGNORECASE)
        for i in voteiter:
            votes.append(i.group(0))

        errors = 0
        dupvotes = 0
        votedict = {}
        spa = {}

        for vote in votes:
            try:
                voter = re.match("\[\[User.*?:(.*?)(?:/|#|\||(?:\]\]))", vote[vote.lower().rfind("[[user"):], re.IGNORECASE)
                if not voter:
                    voter = re.search("\{\{unsigned\|(.*?)(\||(\{\{))", vote, re.IGNORECASE)
                    if not voter:
                        voter = re.search("<span class=\"autosigned\">.*?\[\[User:(.*?)\|.*?<!--\s*Template:Unsigned\s*-->", vote, re.IGNORECASE)
                        if not voter:
                            continue
                voter = voter.group(1).strip()
                bolded = re.search("'''(.*?)'''", vote)
                if not bolded:
                    #print "NOT BOLDED  -  " + cgi.escape(vote) + "<br><br>"
                    continue
                votetype = parsevote(bolded.group(1))
                if votetype == None:    #Unparseable
                    #print "UNPARSEABLE  -  " + bolded.group(1) + "  -  " + cgi.escape(vote) + "<br><br>"
                    continue
                if voter in votedict.keys():
                    dupvotes += 1
                votedict[voter] = votetype
                if not fast:
                    editcount = getEditCount(voter, cursor)
                    if editcount < 500 and editcount > 0:
                        if voter not in spa.keys():
                            spa[voter] = editcount
                #print "SUCCESSFUL " + votetype + "  -  " + cgi.escape(vote) + "<br><br>"

            except:
                errors += 1
                print sys.exc_info()[0]
                print "<br>"
                print traceback.print_exc(file=sys.stdout)
                print "<br>"
                print vote
                print "<br>"
                continue

        print "<H2>" + page + "</H2>"
            
        if len(votedict) == 0:
            errorout("No votes were found on this page.")

        nominator = APIfirsteditor(page)
        if nominator:
            if nominator in votedict.keys():
                dupvotes += 1
            else:
                votedict[nominator] = "Delete"
        
        print "<ul>"
        for v in ["Keep", "Speedy Keep", "Delete", "Speedy Delete", "Merge", "Redirect", "Transwiki", "Userfy"]:
            if votedict.values().count(v):
                voterlist = []
                for voter in votedict.keys():
                    if votedict[voter] == v:
                        voterlist.append(voter)
                print "<li><b>" + v + " votes: " + str(votedict.values().count(v)) + "</b>  <small>(" + ", ".join(voterlist) + ")</small>"
        print "</ul>"
        print "<BR>Found " + str(dupvotes) + " potential duplicate vote" + ("" if dupvotes==1 else "s") + ".<BR>"
        if spa.keys():
            print "<BR>Potential SPA's (voters with less than 500 edits):\n<ul>\n"
            for s in spa.keys():
                print "<li>" + s + " (" + str(spa[s]) + " edits) (voted " + votedict[s] + ")</li>"
            print "</ul>"
        if not spa.keys() and not fast:
            print "<BR>No potential SPA's found.</BR>"
        if fast:
            print '<BR><small><a href="votecounter.cgi?page=' + form['page'].value + '&fast=false">Click here to check for possible SPA\'s (can be slow for large AfD\'s)</a></small><BR>'
        if errors:
            print "<BR>Encountered " + str(errors) + " non-fatal errors while parsing this page.<BR>"
            
        print "<br><br><br><small>Disclaimer: This tool only searches for <b>bolded</b> votes in AfD's, and it may not even find those with 100% accuracy.  Please do not rely on the accuracy of this tool for critical applications, and also keep in mind that consensus is not determined by counting votes.</small><br>"
        print '<br><small>Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Scottywong">User talk:Scottywong</a></small><br>'
        print "</div></BODY>\n</HTML>"
    except:
        errors += 1
        print sys.exc_info()[0]
        print "<br>"
        print traceback.print_exc(file=sys.stdout)
        print "<br>"
    

def APIget(p):
    try:
        u = urllib.urlopen("http://en.wikipedia.org/w/api.php?action=query&prop=revisions&titles=" + urllib.quote(p).replace(" ", "_") + "&rvprop=content&format=xml")
        xml = u.read()
        u.close()

        if re.search(r'<page .*? missing="".*?/>', xml):
            errorout("Page doesn't exist: " + p)
        text = re.search(r'<rev.*?xml:space="preserve">(.*?)</rev>', xml, re.DOTALL).group(1)
        return text
    except:
        #print sys.exc_info()[0]
        #print "<br>"
        #print traceback.print_exc(file=sys.stdout)
        #print "<br>"
        errorout("Error getting content of page: " + p)

def APIfirsteditor(p):
    try:
        u = urllib.urlopen("http://en.wikipedia.org/w/api.php?action=query&prop=revisions&titles=" + urllib.quote(p).replace(" ", "_") + "&rvlimit=1&rvprop=timestamp|user&rvdir=newer&format=xml")
        xml = u.read()
        u.close()
        return re.search("<rev user=\"(.*?)\".*?/>", xml).group(1)
    except:
        #print sys.exc_info()[0]
        #print "<br>"
        #print traceback.print_exc(file=sys.stdout)
        return None

def getEditCount(username, cursor):
    try:
        cursor.execute("SELECT COUNT(*) FROM revision WHERE rev_user_text=%s;", (username))
        ec = cursor.fetchall()[0][0]
        return int(ec)
    except:
        return 0

def unescape(s):
    p = htmllib.HTMLParser(None)
    p.save_bgn()
    p.feed(s)
    return p.save_end()

def errorout(errorstr):
    print "ERROR: " + errorstr + "<br><br>Please try again.<br>"
    print '<br><small>Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Scottywong">User talk:Scottywong</a></small><br>'
    print "</div></BODY>\n</HTML>"
    sys.exit(0)

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
        return None

main()
