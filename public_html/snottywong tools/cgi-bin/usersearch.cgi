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
from babel.dates import format_datetime

starttime = time.time()
username = ""
maxsearch = 100     #default number of edits to return
maxlimit = 500      #max number of edits to return, even if the user asks for more
startdate = ""
pagetitle = ""
namespace = 0
namespacename = ""
redirect = False    #if true, don't try to resolve redirects
wildcards = False   #if true, allow wildcards in the page name
casesensitive = False   #if true, page name with wildcards should be case sensitive (only used with wildcards)
server = "enwiki_p" #Which wiki we're searching, english by default
domain = "en.wikipedia.org"

allwikis = ['abwiki', 'acewiki', 'afwiki', 'akwiki', 'alswiki', 'amwiki', 'angwiki', 'anwiki', 'arcwiki', 'arwiki', 'arzwiki', 'astwiki', 'aswiki', 'avwiki', 'aywiki', 'azwiki', 'barwiki', 'bat_smgwiki', 'bawiki', 'bclwiki', 'be_x_oldwiki', 'bewiki', 'bgwiki', 'bhwiki', 'biwiki', 'bjnwiki', 'bmwiki', 'bnwiki', 'bowiki', 'bpywiki', 'brwiki', 'bswiki', 'bugwiki', 'bxrwiki', 'cawiki', 'cbk_zamwiki', 'cdowiki', 'cebwiki', 'cewiki', 'chrwiki', 'chwiki', 'chywiki', 'ckbwiki', 'commonswiki', 'cowiki', 'crhwiki', 'crwiki', 'csbwiki', 'cswiki', 'cuwiki', 'cvwiki', 'cywiki', 'dawiki', 'dewiki', 'diqwiki', 'dsbwiki', 'dvwiki', 'dzwiki', 'eewiki', 'elwiki', 'emlwiki', 'enwiki', 'eowiki', 'eswiki', 'etwiki', 'euwiki', 'extwiki', 'fawiki', 'ffwiki', 'fiu_vrowiki', 'fiwiki', 'fjwiki', 'foundationwiki', 'fowiki', 'frpwiki', 'frrwiki', 'frwiki', 'furwiki', 'fywiki', 'gagwiki', 'ganwiki', 'gawiki', 'gdwiki', 'glkwiki', 'glwiki', 'gnwiki', 'gotwiki', 'guwiki', 'gvwiki', 'hakwiki', 'hawiki', 'hawwiki', 'hewiki', 'hifwiki', 'hiwiki', 'hrwiki', 'hsbwiki', 'htwiki', 'huwiki', 'hywiki', 'iawiki', 'idwiki', 'iewiki', 'igwiki', 'ikwiki', 'ilowiki', 'incubatorwiki', 'iowiki', 'iswiki', 'itwiki', 'iuwiki', 'jawiki', 'jbowiki', 'jvwiki', 'kaawiki', 'kabwiki', 'kawiki', 'kbdwiki', 'kgwiki', 'kiwiki', 'kkwiki', 'klwiki', 'kmwiki', 'knwiki', 'koiwiki', 'kowiki', 'krcwiki', 'kshwiki', 'kswiki', 'kuwiki', 'kvwiki', 'kwwiki', 'kywiki', 'ladwiki', 'lawiki', 'lbewiki', 'lbwiki', 'lgwiki', 'lijwiki', 'liwiki', 'lmowiki', 'lnwiki', 'lowiki', 'ltgwiki', 'ltwiki', 'lvwiki', 'map_bmswiki', 'mdfwiki', 'mediawikiwiki', 'metawiki', 'mgwiki', 'mhrwiki', 'miwiki', 'mkwiki', 'mlwiki', 'mnwiki', 'mrjwiki', 'mrwiki', 'mswiki', 'mtwiki', 'mwlwiki', 'myvwiki', 'mywiki', 'mznwiki', 'nahwiki', 'napwiki', 'nawiki', 'nds_nlwiki', 'ndswiki', 'newiki', 'newwiki', 'nlwiki', 'nnwiki', 'novwiki', 'nowiki', 'nrmwiki', 'nvwiki', 'nywiki', 'ocwiki', 'omwiki', 'orwiki', 'oswiki', 'outreachwiki', 'pagwiki', 'pamwiki', 'papwiki', 'pawiki', 'pcdwiki', 'pdcwiki', 'pflwiki', 'pihwiki', 'piwiki', 'plwiki', 'pmswiki', 'pnbwiki', 'pntwiki', 'pswiki', 'ptwiki', 'quwiki', 'rmwiki', 'rmywiki', 'rnwiki', 'roa_rupwiki', 'roa_tarawiki', 'rowiki', 'ruewiki', 'ruwiki', 'rwwiki', 'sahwiki', 'sawiki', 'scnwiki', 'scowiki', 'scwiki', 'sdwiki', 'sewiki', 'sgwiki', 'shwiki', 'simplewiki', 'siwiki', 'skwiki', 'slwiki', 'smwiki', 'snwiki', 'sourceswiki', 'sowiki', 'specieswiki', 'sqwiki', 'srnwiki', 'srwiki', 'sswiki', 'stqwiki', 'strategywiki', 'stwiki', 'suwiki', 'svwiki', 'swwiki', 'szlwiki', 'tawiki', 'tenwiki', 'testwiki', 'tetwiki', 'tewiki', 'tgwiki', 'thwiki', 'tiwiki', 'tkwiki', 'tlwiki', 'tnwiki', 'towiki', 'tpiwiki', 'trwiki', 'tswiki', 'ttwiki', 'tumwiki', 'twwiki', 'tywiki', 'udmwiki', 'ugwiki', 'ukwiki', 'urwiki', 'uzwiki', 'vecwiki', 'vewiki', 'viwiki', 'vlswiki', 'vowiki', 'warwiki', 'wawiki', 'wowiki', 'wuuwiki', 'xalwiki', 'xhwiki', 'xmfwiki', 'yiwiki', 'yowiki', 'zawiki', 'zeawiki', 'zh_classicalwiki', 'zh_min_nanwiki', 'zh_yuewiki', 'zhwiki', 'zuwiki']
popularwikis = ['enwiki', 'dewiki', 'eswiki', 'frwiki', 'itwiki', 'nlwiki', 'jawiki', 'plwiki', 'ptwiki', 'ruwiki', 'zhwiki', 'commonswiki']

difftext = {"enwiki_p":"diff", "commonswiki_p":"diff", "dewiki_p":"Unterschied", "eswiki_p":"dif", "frwiki_p":"diff", "itwiki_p":"diff", "nlwiki_p":"wijz", "jawiki_p":u"差分", "plwiki_p":u"różn.", "ptwiki_p":"dif", "ruwiki_p":u"обсуждение", "zhwiki_p":u"差异"}
histtext = {"enwiki_p":"hist", "commonswiki_p":"hist", "dewiki_p":"Versionen", "eswiki_p":"hist", "frwiki_p":"hist", "itwiki_p":"cron", "nlwiki_p":"gesch", "jawiki_p":u"履歴", "plwiki_p":"hist.", "ptwiki_p":"his", "ruwiki_p":u"вклад", "zhwiki_p":u"历史"}
minormark = {"enwiki_p":"m", "commonswiki_p":"m", "dewiki_p":"K", "eswiki_p":"m", "frwiki_p":"m", "itwiki_p":"m", "nlwiki_p":"k", "jawiki_p":"m", "plwiki_p":"m", "ptwiki_p":"m", "ruwiki_p":u"м", "zhwiki_p":"m"}

localename = {"enwiki_p":"en", "commonswiki_p":"en", "dewiki_p":"de", "eswiki_p":"es", "frwiki_p":"m", "itwiki_p":"it", "nlwiki_p":"nl", "jawiki_p":"ja", "plwiki_p":"pl", "ptwiki_p":"pt", "ruwiki_p":"ru", "zhwiki_p":"zh"}
localeformat = {"enwiki_p":"HH:mm, d MMMM yyyy", "commonswiki_p":"HH:mm, d MMMM yyyy", "dewiki_p":"HH:mm, d. MMM. yyyy", "eswiki_p":"HH:mm d MMM yyyy", "frwiki_p":u"d MMMM yyyy à HH:mm", "itwiki_p":"HH:mm, d MMM yyyy", "nlwiki_p":"d MMM yyyy HH:mm", "jawiki_p":u"yyyy年M月d日 (EEE) HH:mm", "plwiki_p":"HH:mm, d MMM yyyy", "ptwiki_p":"HH'h'mm'min de' d 'de' MMMM 'de' yyyy", "ruwiki_p":"HH:mm, d MMMM yyyy", "zhwiki_p":u"yyyy年M月d日 (EEEEE) HH:mm"}


#nslookup and nsrevlookup are now deprecated
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
    global namespacename
    global redirect
    global wildcards
    global casesensitive
    global server
    global domain

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
        if os.environ["REMOTE_ADDR"].startswith("89.151.116.5"):
            errorout("Your IP address has been flagged for potential abuse.  Please post a message to User talk:Scottywong on the English Wikipedia, or alternatively send an email to snottywong.wiki@gmail.com to prove that you are a human, and to explain why you've been consistently making so many queries on this tool.")
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
        if "server" in form:
            try:
                server = form['server'].value
                server += "_p"
            except:
                server = "enwiki_p"
                
        db = MySQLdb.connect(db=server, host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()

        try:
            cursor.execute('SELECT domain FROM toolserver.wiki WHERE dbname=%s;', (server))
            domain = cursor.fetchall()[0][0]
            if not domain:
                domain = "en.wikipedia.org"
        except:
            domain = "en.wikipedia.org"

        if "page" in form:
            try:
                pagetitle = form['page'].value
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
                if pagetitle.find(":") >= 0:
                    namespacename = pagetitle[:pagetitle.find(":")]
                else:
                    namespacename = ""
                namespace = fetchnamespace(cursor, server, namespacename.replace("_", " "))
                if namespace:
                    pagewons = pagetitle[pagetitle.find(":")+1:]
                else:
                    pagewons = pagetitle
                    namespacename = ""
                if not redirect and not wildcards:  #resolve redirects unless specifically told not to, or if using wildcards
                    retest = findredirect(cursor, pagewons, namespace)
                    if retest:
                        if namespacename:
                            pagetitle = namespacename + ":" + retest
                        else:
                            pagetitle = retest
                        if namespace:
                            pagewons = pagetitle[pagetitle.find(":")+1:]
                        else:
                            pagewons = pagetitle
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
        f.write("<log><ip>" + os.environ["REMOTE_ADDR"] + "</ip><username>" + username + "</username><pagetitle>" + pagetitle + "</pagetitle><max>" + str(maxsearch) + "</max><timestamp>" + datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</timestamp><server>" + server + "</server>" + ("<startdate>" + startdate + "</startdate>" if startdate else "") + ("<wildcards>true</wildcards>" if wildcards else "") + ("<cs>true</cs>" if casesensitive else "") + "</log>\n")
        f.close()

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

        print '<form method="get">'
        print 'Username:&nbsp;<input type="text" name="name" value="' + username.replace('"', '&quot;') + '" />&nbsp;&nbsp;&nbsp;Page:&nbsp;<input type="text" name="page" size="40" value="' + pagetitle.replace('"', '&quot;').replace("_", " ") + '" />&nbsp;&nbsp;&nbsp;Max&nbsp;edits:&nbsp;<input type="text" name="max" maxlength="3" size="5" value="' + str(maxsearch) + '" /><br>'            
        print printdatabases(server)
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
        errorout("Unhandled exception.<br><br>" + traceback.print_exc(file=sys.stdout))
        #errorout('Unhandled exception. Please try again. If this error persists, please contact me at <a href="http://en.wikipedia.org/wiki/User_talk:Snottywong">User talk:Snottywong</a><br><br>')

def printtable(r):  #prints each edit out in an unordered list
    global pagetitle
    global namespace
    global namespacename
    global domain
    global server
    for edit in r:
        revid = str(edit[0])
        timestamp = formatdate(edit[1])
        minoredit = edit[2]
        comment = edit[3].replace("[[WP:AES|←]]", "←")
        title = namespacename + (":" if namespacename else "") + edit[4]
        #print "DEBUG: " + str(namespace) + " " + namespacename + "<BR>"
        #print "DEBUG:<BR>"
        #print domain + "<BR>"
        #print title + "<BR>"
        #print revid + "<BR>"
        #print timestamp + "<BR>"
        #print diff(server) + "<BR>"
        #print hist(server) + "<BR>"
        #print minor(server) + "<BR>"
        #print escapehtml(title.replace("_", " ")) + "<BR>"
        #print fmtcmt(escapehtml(comment)) + "<BR>"
        
        print '<li><a href="http://' + domain + '/w/index.php?title=' + title + '&oldid=' + revid + '">' + timestamp + '</a> (<a href="http://' + domain + '/w/index.php?title=' + title + '&diff=prev&oldid=' + revid + '">' + diff(server) + '</a> | <a href="http://' + domain + '/w/index.php?title=' + title + '&action=history">' + hist(server) + '</a>) ' + (minor(server) if minoredit else "") + ' <a href="http://' + domain + '/wiki/' + title + '">' + escapehtml(title.replace("_", " ")) + '</a> ' + (('(<span class="comment">' + fmtcmt(escapehtml(comment)) + '</span>)') if comment else '') + '</li>'
    
def formatdate(ts): #formats timestamp into text
    global server
    global localename
    global localeformat
    d = datetime.datetime(int(ts[:4]), int(ts[4:6]), int(ts[6:8]), int(ts[8:10]), int(ts[10:12]), int(ts[12:14]))
    if server in localeformat:
        return format_datetime(d, localeformat[server], locale=localename[server]).encode("utf-8")
    else:
        return format_datetime(d, localeformat["enwiki_p"], locale=localename["enwiki_p"]).encode("utf-8") 

def fmtcmt(comment):    #adds an autocomment span into the comment if section header detected
    if "/*" in comment and "*/" in comment:
        return comment.replace("/*", '<span class="autocomment">/*', 1).replace("*/", "*/</span>", 1)
    return comment

def extractns(p):   #returns namespace number of article (this function is deprecated, use fetchnamespace() instead)
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

def findredirect(sqlcursor, p, ns):    #find out if page is a redirect, if so return the redirect target, if not return original page name
    try:
        redirecttarget = None
        sqlcursor.execute('SELECT rd_title FROM redirect JOIN page ON rd_from=page_id WHERE page_title=%s AND page_namespace=%s;', (p, ns))
        redirecttarget = sqlcursor.fetchall()[0][0]
        return redirecttarget
    except:
        return None

def errorout(errorstr): #prints error string and exits
    print "ERROR: " + errorstr + "<br><br>Please try again.<br>"
    print "</div>\n</BODY>\n</HTML>"
    sys.exit(0)

def fetchnamespace(sqlcursor, dbname, nsname):  #Fetch namespace from database
    try:
        sqlcursor.execute('SELECT ns_id FROM toolserver.namespacename WHERE dbname=%s AND ns_name=%s', (dbname, nsname))
        results = int(sqlcursor.fetchall()[0][0])
        if results:
            return results
        return 0
    except:
        return 0

def printdatabases(selectedserv):   #Print drop-down form menu for database server selection
    global popularwikis
    global allwikis

    selectedserv = selectedserv.replace("_p", "")
    popular = False
    printstr = 'Database: <select name="server">\n<optgroup label="Popular Wikis">\n'
    for s in popularwikis:
        if s == selectedserv:
            printstr += '<option value="' + s + '" selected>' + s + '</option>\n'
            popular = True
        else:
            printstr += '<option value="' + s + '">' + s + '</option>\n'
    printstr += '</optgroup>\n<optgroup label="All Wikis">\n'
    if popular:
        for s in allwikis:
            printstr += '<option value="' + s + '">' + s + '</option>\n'
    else:
        for s in allwikis:
            if s == selectedserv:
                printstr += '<option value="' + s + '" selected>' + s + '</option>\n'
            else:
                printstr += '<option value="' + s + '">' + s + '</option>\n'
    printstr += '</optgroup>\n</select>\n<br>\n'
    return printstr

def diff(database):     #return localization for a diff link
    global difftext
    if database in difftext:
        return difftext[database].encode("utf-8")
    return "diff"

def hist(database):     #return localization for a hist link
    global histtext
    if database in histtext:
        return histtext[database].encode("utf-8")
    return "hist"

def minor(database):    #return localization for a minor edit mark
    global minormark
    if database in minormark:
        return u"<b>".encode("utf-8") + minormark[database].encode("utf-8") + u"</b>".encode("utf-8")
    return "<b>m</b>"  

main()
print '<br><small>Bugs, suggestions, questions?  Contact the author at <a href="http://en.wikipedia.org/wiki/User_talk:Snottywong">User talk:Snottywong</a></small><br>'
print '<a href="usersearch.html"><small>&larr;New search</small></a>'
print "</div>\n</BODY>\n</HTML>"




            
"""

Date Format:
enwiki - 01:23, 14 October 2011
commons - same
dewiki - 01:23, 14. Okt. 2011
eswiki - 01:23 14 oct 2011
frwiki - 14 octobre 2011 à 01:23
itwiki - 01:23, 14 ott 2011
nlwiki - 14 oct 2011 01:23
jawiki - 2011年9月8日 (木) 01:05
plwiki - 01:23, 14 paź 2011
ptwiki - 01h23min de 14 outubro de 2011
ruwiki - 01:23, 14 августа 2011
zhwiki - 2011年10月14日 (一) 01:23

Diff text:
enwiki - diff
commons - diff
dewiki - Unterschied
eswiki - dif
frwiki - diff
itwiki - diff
nlwiki - wijz
jawiki - 差分
plwiki - różn.
ptwiki - dif
ruwiki - обсуждение
zhwiki - 差异

History text:
enwiki - hist
commons - hist
dewiki - Versionen
eswiki - hist
frwiki - hist
itwiki - cron
nlwiki - gesch
jawiki - 履歴
plwiki - hist.
ptwiki - his
ruwiki - вклад
zhwiki - 历史

Minor mark:
enwiki - m
commons - m
dewiki - K
eswiki - m
frwiki - m
itwiki - m
nlwiki - k
jawiki - m
plwiki - m
ptwiki - m
ruwiki - м
zhwiki - m

"""
