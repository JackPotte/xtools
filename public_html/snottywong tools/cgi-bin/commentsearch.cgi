#!/usr/bin/env python
# -*- coding: utf-8 -*-

#TODO: Add JS business for updating ns list into search result page (should just create a standalone js and link to it if not already doing it that way)

import MySQLdb
import sys
import os
import traceback
import cgi
import urllib
import datetime
import time
from babel.dates import format_datetime

starttime = time.time()
username = ""
searchstr = ""
maxsearch = 100     #default number of edits to return
maxlimit = 500      #max number of edits to return, even if the user asks for more
startdate = ""
nosect = False      #whether or not we will be ignoring comments in /* section headers */, false by default = not ignoring section headers
casesensitive = False   #if true, search will be case sensitive
ns = None           #if not None, will only return results in specified namespace
server = "enwiki_p" #Which wiki we're searching, english by default
domain = "en.wikipedia.org"

allwikis = ['abwiki', 'acewiki', 'afwiki', 'akwiki', 'alswiki', 'amwiki', 'angwiki', 'anwiki', 'arcwiki', 'arwiki', 'arzwiki', 'astwiki', 'aswiki', 'avwiki', 'aywiki', 'azwiki', 'barwiki', 'bat_smgwiki', 'bawiki', 'bclwiki', 'be_x_oldwiki', 'bewiki', 'bgwiki', 'bhwiki', 'biwiki', 'bjnwiki', 'bmwiki', 'bnwiki', 'bowiki', 'bpywiki', 'brwiki', 'bswiki', 'bugwiki', 'bxrwiki', 'cawiki', 'cbk_zamwiki', 'cdowiki', 'cebwiki', 'cewiki', 'chrwiki', 'chwiki', 'chywiki', 'ckbwiki', 'commonswiki', 'cowiki', 'crhwiki', 'crwiki', 'csbwiki', 'cswiki', 'cuwiki', 'cvwiki', 'cywiki', 'dawiki', 'dewiki', 'diqwiki', 'dsbwiki', 'dvwiki', 'dzwiki', 'eewiki', 'elwiki', 'emlwiki', 'enwiki', 'eowiki', 'eswiki', 'etwiki', 'euwiki', 'extwiki', 'fawiki', 'ffwiki', 'fiu_vrowiki', 'fiwiki', 'fjwiki', 'foundationwiki', 'fowiki', 'frpwiki', 'frrwiki', 'frwiki', 'furwiki', 'fywiki', 'gagwiki', 'ganwiki', 'gawiki', 'gdwiki', 'glkwiki', 'glwiki', 'gnwiki', 'gotwiki', 'guwiki', 'gvwiki', 'hakwiki', 'hawiki', 'hawwiki', 'hewiki', 'hifwiki', 'hiwiki', 'hrwiki', 'hsbwiki', 'htwiki', 'huwiki', 'hywiki', 'iawiki', 'idwiki', 'iewiki', 'igwiki', 'ikwiki', 'ilowiki', 'incubatorwiki', 'iowiki', 'iswiki', 'itwiki', 'iuwiki', 'jawiki', 'jbowiki', 'jvwiki', 'kaawiki', 'kabwiki', 'kawiki', 'kbdwiki', 'kgwiki', 'kiwiki', 'kkwiki', 'klwiki', 'kmwiki', 'knwiki', 'koiwiki', 'kowiki', 'krcwiki', 'kshwiki', 'kswiki', 'kuwiki', 'kvwiki', 'kwwiki', 'kywiki', 'ladwiki', 'lawiki', 'lbewiki', 'lbwiki', 'lgwiki', 'lijwiki', 'liwiki', 'lmowiki', 'lnwiki', 'lowiki', 'ltgwiki', 'ltwiki', 'lvwiki', 'map_bmswiki', 'mdfwiki', 'mediawikiwiki', 'metawiki', 'mgwiki', 'mhrwiki', 'miwiki', 'mkwiki', 'mlwiki', 'mnwiki', 'mrjwiki', 'mrwiki', 'mswiki', 'mtwiki', 'mwlwiki', 'myvwiki', 'mywiki', 'mznwiki', 'nahwiki', 'napwiki', 'nawiki', 'nds_nlwiki', 'ndswiki', 'newiki', 'newwiki', 'nlwiki', 'nnwiki', 'novwiki', 'nowiki', 'nrmwiki', 'nvwiki', 'nywiki', 'ocwiki', 'omwiki', 'orwiki', 'oswiki', 'outreachwiki', 'pagwiki', 'pamwiki', 'papwiki', 'pawiki', 'pcdwiki', 'pdcwiki', 'pflwiki', 'pihwiki', 'piwiki', 'plwiki', 'pmswiki', 'pnbwiki', 'pntwiki', 'pswiki', 'ptwiki', 'quwiki', 'rmwiki', 'rmywiki', 'rnwiki', 'roa_rupwiki', 'roa_tarawiki', 'rowiki', 'ruewiki', 'ruwiki', 'rwwiki', 'sahwiki', 'sawiki', 'scnwiki', 'scowiki', 'scwiki', 'sdwiki', 'sewiki', 'sgwiki', 'shwiki', 'simplewiki', 'siwiki', 'skwiki', 'slwiki', 'smwiki', 'snwiki', 'sourceswiki', 'sowiki', 'specieswiki', 'sqwiki', 'srnwiki', 'srwiki', 'sswiki', 'stqwiki', 'strategywiki', 'stwiki', 'suwiki', 'svwiki', 'swwiki', 'szlwiki', 'tawiki', 'tenwiki', 'testwiki', 'tetwiki', 'tewiki', 'tgwiki', 'thwiki', 'tiwiki', 'tkwiki', 'tlwiki', 'tnwiki', 'towiki', 'tpiwiki', 'trwiki', 'tswiki', 'ttwiki', 'tumwiki', 'twwiki', 'tywiki', 'udmwiki', 'ugwiki', 'ukwiki', 'urwiki', 'uzwiki', 'vecwiki', 'vewiki', 'viwiki', 'vlswiki', 'vowiki', 'warwiki', 'wawiki', 'wowiki', 'wuuwiki', 'xalwiki', 'xhwiki', 'xmfwiki', 'yiwiki', 'yowiki', 'zawiki', 'zeawiki', 'zh_classicalwiki', 'zh_min_nanwiki', 'zh_yuewiki', 'zhwiki', 'zuwiki']
popularwikis = ['enwiki', 'dewiki', 'eswiki', 'frwiki', 'itwiki', 'nlwiki', 'jawiki', 'plwiki', 'ptwiki', 'ruwiki', 'zhwiki', 'commonswiki']

difftext = {"enwiki_p":"diff", "commonswiki_p":"diff", "dewiki_p":"Unterschied", "eswiki_p":"dif", "frwiki_p":"diff", "itwiki_p":"diff", "nlwiki_p":"wijz", "jawiki_p":u"差分", "plwiki_p":u"różn.", "ptwiki_p":"dif", "ruwiki_p":u"обсуждение", "zhwiki_p":u"差异"}
histtext = {"enwiki_p":"hist", "commonswiki_p":"hist", "dewiki_p":"Versionen", "eswiki_p":"hist", "frwiki_p":"hist", "itwiki_p":"cron", "nlwiki_p":"gesch", "jawiki_p":u"履歴", "plwiki_p":"hist.", "ptwiki_p":"his", "ruwiki_p":u"вклад", "zhwiki_p":u"历史"}
minormark = {"enwiki_p":"m", "commonswiki_p":"m", "dewiki_p":"K", "eswiki_p":"m", "frwiki_p":"m", "itwiki_p":"m", "nlwiki_p":"k", "jawiki_p":"m", "plwiki_p":"m", "ptwiki_p":"m", "ruwiki_p":u"м", "zhwiki_p":"m"}

localename = {"enwiki_p":"en", "commonswiki_p":"en", "dewiki_p":"de", "eswiki_p":"es", "frwiki_p":"m", "itwiki_p":"it", "nlwiki_p":"nl", "jawiki_p":"ja", "plwiki_p":"pl", "ptwiki_p":"pt", "ruwiki_p":"ru", "zhwiki_p":"zh"}
localeformat = {"enwiki_p":"HH:mm, d MMMM yyyy", "commonswiki_p":"HH:mm, d MMMM yyyy", "dewiki_p":"HH:mm, d. MMM. yyyy", "eswiki_p":"HH:mm d MMM yyyy", "frwiki_p":u"d MMMM yyyy à HH:mm", "itwiki_p":"HH:mm, d MMM yyyy", "nlwiki_p":"d MMM yyyy HH:mm", "jawiki_p":u"yyyy年M月d日 (EEE) HH:mm", "plwiki_p":"HH:mm, d MMM yyyy", "ptwiki_p":"HH'h'mm'min de' d 'de' MMMM 'de' yyyy", "ruwiki_p":"HH:mm, d MMMM yyyy", "zhwiki_p":u"yyyy年M月d日 (EEEEE) HH:mm"}

namespaces = {0:"", 1:"Talk:", 2:"User:", 3:"User talk:", 4:"Wikipedia:", 5:"Wikipedia talk:", 6:"File:", 7:"File talk:", 8:"MediaWiki:", 9:"MediaWiki talk:", 10:"Template:", 11:"Template talk:", 12:"Help:", 13:"Help talk:", 14:"Category:", 15:"Category talk:", 100:"Portal:", 101:"Portal talk:", 108:"Book:", 109:"Book talk:"}

#nslookup and nsrevlookup are now deprecated
#nslookup = {0:"", 1:"Talk:", 2:"User:", 3:"User talk:", 4:"Wikipedia:", 5:"Wikipedia talk:", 6:"File:", 7:"File talk:", 8:"MediaWiki:", 9:"MediaWiki talk:", 10:"Template:", 11:"Template talk:", 12:"Help:", 13:"Help talk:", 14:"Category:", 15:"Category talk:", 100:"Portal:", 101:"Portal talk:", 108:"Book:", 109:"Book talk:"}
#nsrevlookup = dict((v,k) for k,v in nslookup.iteritems())
#del nsrevlookup['']

def main():
    global username
    global maxsearch
    global maxlimit
    global startdate
    global searchstr
    global nosect
    global casesensitive
    global ns
    global server
    global domain
    global namespaces

    print """<!doctype html>
<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
<LINK href="menubar3.css" rel="stylesheet" type="text/css">
<TITLE>Edit summary search results</TITLE>
</HEAD>
<BODY id="yes">
<script type="text/javascript" src="/menubar.js"></script>
<script type="text/javascript" src="/jquery.js"></script>
<script type="text/javascript" src="/globalnamespaces.js"></script>
<br>
<div id="globalWrapper">
<a href="commentsearch.html"><small>&larr;New search</small></a>
<br><br>"""

    try:
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
        if "server" in form:
            try:
                server = form['server'].value
                server += "_p"
            except:
                server = "enwiki_p"
                
        db = MySQLdb.connect(db=server, host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
        cursor = db.cursor()
        
        #fetchnamespaces(cursor, server)
        if "ns" in form:
            try:
                ns = form['ns'].value
                if ns.lower() == "none":
                    ns = None
                else:
                    ns = int(ns)
                    if ns not in namespaces.keys():
                        raise
            except:
                errorout("Invalid namespace specified.")
                
        username = form['name'].value.replace("_", " ").replace("+", " ")
        if username.lower().startswith("user:"):
            username = username[5:]
        #username = username[0].capitalize() + username[1:]
            
        f = open("commentsearchlog.txt", "a")
        f.write("<log><ip>" + os.environ["REMOTE_ADDR"] + "</ip><username>" + username + "</username><searchstr>" + searchstr + "</searchstr><max>" + str(maxsearch) + "</max><timestamp>" + datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</timestamp><server>" + server + "</server>" + ("<startdate>" + startdate + "</startdate>" if startdate else "") + ("<case>true</case>" if casesensitive else "") + ("<ns>" + str(ns) + "</ns>" if ns else "") + "</log>\n")
        f.close()

        try:
            cursor.execute('SELECT domain FROM toolserver.wiki WHERE dbname=%s;', (server))
            domain = cursor.fetchall()[0][0]
            if not domain:
                domain = "en.wikipedia.org"
        except:
            domain = "en.wikipedia.org"
        
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
        results = cursor.fetchall()
        db.close()
        
        print '<form name="myform" action="cgi-bin/commentsearch.cgi" method="get">'
        print 'Username:&nbsp;<input type="text" name="name" value="' + username.replace('"', '&quot;') + '" />&nbsp;&nbsp;&nbsp;Search&nbsp;string:&nbsp;<input type="text" name="search" size="40" value="' + searchstr.replace('"', '&quot;') + '" />&nbsp;&nbsp;&nbsp;Max&nbsp;pages:&nbsp;<input type="text" name="max" maxlength="3" size="5" value="' + str(maxsearch) + '" />'
        print "<br>" + printdatabases(server)
        print """<br><a href="javascript:;" onmousedown="if(document.getElementById('mydiv').style.display == 'none'){ document.getElementById('mydiv').style.display = 'block'; }else{ document.getElementById('mydiv').style.display = 'none'; }">Advanced options &darr;</a><br>"""
        print '<div id="mydiv" style="display:' + ('block' if (nosect == True or casesensitive == True or ns != None) else 'none') + '">'
        print '<br>\n<input type="checkbox" name="nosect" value="1"' + ("checked" if nosect else "") + ">Don't search within /* section headings */<br>"
        print '<input type="checkbox" name="casesensitive" value="1"' + ("checked" if casesensitive else "") + '/>Case sensitive search<br />'
        print 'Restrict search to namespace: <select name="ns">'

        print '<option value="none"' + (' selected' if ns==None else '') + '>All namespaces</option>'
        for nsnum in sorted(namespaces.keys()):
            if nsnum == 0:
                print '<option value="0"' + (' selected' if ns==0 else '') + '>(Article)</option>'
            else:
                print '<option value="' + str(nsnum) + '"' + (' selected' if ns==nsnum else '') + '>' + namespaces[nsnum] + '</option>'

        print '</select>\n</div>'
        print """<input type="submit" value="Submit" /> 
</form>
<br>
<hr style="text-align:left;width:875px;margin-left:0">
<br>
"""

        if len(results) == maxsearch:
            print '<a href="cgi-bin/commentsearch.cgi?name=' + urllib.quote_plus(username) + '&max=' + str(maxsearch) + '&search=' + urllib.quote_plus(searchstr) + '&startdate=' + str(int(results[-1][1])-1) + '&server=' + server.replace("_p", "") + '"><small>Next ' + str(maxsearch) + " results &rarr;</small></a><br>"

        print "<ul>"
        printtable(results)
        print "</ul>"
        
        if len(results) == maxsearch:
            print '<a href="cgi-bin/commentsearch.cgi?name=' + urllib.quote_plus(username) + '&max=' + str(maxsearch) + '&search=' + urllib.quote_plus(searchstr) + '&startdate=' + str(int(results[-1][1])-1) + '&server=' + server.replace("_p", "") + '"><small>Next ' + str(maxsearch) + " results &rarr;</small></a><br>"

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

def fetchnamespace(sqlcursor, dbname, nsname):  #Fetch namespace from database
    try:
        sqlcursor.execute("SELECT ns_id FROM " + server + ".namespacename WHERE dbname=%s AND ns_name=%s", (dbname, nsname))
        results = int(sqlcursor.fetchall()[0][0])
        if results:
            return results
        return 0
    except:
        return 0

def fetchnamespaces(sqlcursor, dbname):     #Fetch all namespaces for a particular server
    global namespaces
    try:
        sqlcursor.execute("SELECT ns_name, ns_id FROM " + server + ".namespacename WHERE dbname=%s", (dbname))
        namespacelist = sqlcursor.fetchall()
        if len(namespacelist) == 0:
            errorout("Invalid server.")
        nslist = []
        for i in namespacelist:
            if i[1] in nslist:
                continue
            if i[1] < 0:
                continue
            nslist.append(i[1])
            namespaces[i[1]] = i[0]
    except:
        errorout("Invalid server.")

def printdatabases(selectedserv):   #Print drop-down form menu for database server selection
    global popularwikis
    global allwikis

    selectedserv = selectedserv.replace("_p", "")
    popular = False
    printstr = 'Database: <select name="server" onchange="loadNamespaces()">\n<optgroup label="Popular Wikis">\n'
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

def formatline(edit):   #returns unordered list html for an edit
    global domain
    global namespaces
    revid = str(edit[0])
    timestamp = formatdate(edit[1])
    minoredit = edit[2]
    comment = escapehtml(edit[3].replace("[[WP:AES|←]]", "←"))
    pagetitle = edit[4]
    namespace = edit[5]
    fulltitle = namespaces[namespace].replace(" ", "_") + (":" if namespaces[namespace] else "") + pagetitle
    return '<li><a href="http://' + domain + '/w/index.php?title=' + fulltitle + '&oldid=' + revid + '">' + timestamp + '</a> (<a href="http://' + domain + '/w/index.php?title=' + fulltitle + '&diff=prev&oldid=' + revid + '">' + diff(server) + '</a> | <a href="http://' + domain + '/w/index.php?title=' + fulltitle + '&action=history">' + hist(server) + '</a>) ' + (minor(server) if minoredit else "") + ' <a href="http://' + domain + '/wiki/' + fulltitle + '">' + escapehtml(fulltitle.replace("_", " ")) + '</a> ' + (('(<span class="comment">' + fmtcmt(escapehtml(comment)) + '</span>)') if comment else '') + '</li>'

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
