#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
#import sys
import os
#import traceback
#import cgi
#import urllib
#import re
#import datetime
import time
#import htmllib
import re

ipregex = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
throttletime = 0
db = MySQLdb.connect(db='enwiki_p', host="enwiki.labsdb", read_default_file=os.path.expanduser("~/replica.my.cnf"))
cursor = db.cursor()

"""Stats to find:
All stats should be compiled per day, in such a way that makes it easy to extrapolate the overall stats for the entire 6-month period
# of articles created by auto-confirmed users (articles_by_autoconfirmed)
# of articles created by non-auto-confirmed users (articles_by_non_autoconfirmed)
# of articles created by non-auto-confirmed users which were not deleted to this day (articles_kept)
# of articles created by non-auto-confirmed users which were deleted (articles_deleted)
# of articles created by non-auto-confirmed users which were deleted, and whose author subsequently quit wikipedia (made no more edits to this day) (users_quit)
# of articles created by non-auto-confirmed users which were deleted, and whose author subsequently continued editing and became auto-confirmed (users_confirmed)
# of articles created by non-auto-confirmed users which were deleted, and whose author was subsequently blocked for any length of time (users_blocked)
# of articles created by non-auto-confirmed users which were deleted, whose author continues to be blocked to this day (users_still_blocked)

#Cache names of auto-confirmed users so that duplicate SQL queries can be skipped on them (autoconfirmedlist)
"""

def init_stat_vars():   #returns an empty dictionary with pre-defined keys for each day
    tempdict = {}

    def appenddict(month, maxday):
        for i in range(1, maxday+1):
            if i>9:
                day = str(i)
            else:
                day = "0" + str(i)
            tempdict["2011" + month + str(day)] = 0
    
    appenddict("01", 31)
    appenddict("02", 28)
    appenddict("03", 31)
    appenddict("04", 30)
    appenddict("05", 31)
    return tempdict

#These dictionaries keep stats on number of articles/users in each category, per day.
articles_by_autoconfirmed = init_stat_vars()
articles_by_non_autoconfirmed = init_stat_vars()
articles_kept = init_stat_vars()
articles_deleted = init_stat_vars()
users_quit = init_stat_vars()
users_confirmed = init_stat_vars()
users_blocked = init_stat_vars()
users_still_blocked = init_stat_vars()
articles_by_autoconfirmed_kept = init_stat_vars()
articles_by_nonautoconfirmed_kept = init_stat_vars()
articles_by_autoconfirmed_deleted = init_stat_vars()
articles_by_nonautoconfirmed_deleted = init_stat_vars()

#These lists keep usernames of unique users in each category.  There should be no duplicates in these lists.
unique_autoconfirmed = []
unique_nonautoconfirmed = []
unique_users_quit = []
unique_users_confirmed = []
unique_users_blocked = []
unique_users_still_blocked = []
unique_ips = []
numips = 0

#This list keeps a cache of autoconfirmed users, so that we don't waste time querying SQL multiple times on the same user.
autoconfirmedlist = []

def isIP(ip):
    global numips
    if ipregex.match(ip):
        numips += 1
        if ip not in unique_ips:
            unique_ips.append(ip)
        return True
    return False

def autoconfirmed(userid, timestamp):  #Query SQL to determine user's autoconfirmed status at the time of article creation
    try:
        #print "1",
        cursor.execute(u'SELECT /* SLOW OK */ COUNT(*) FROM revision WHERE rev_user=' + userid + u' AND rev_timestamp<' + timestamp + u';') #Get number of edits since before timestamp
        results = cursor.fetchall()
        time.sleep(throttletime)
    except:
        #print "Retry1",
        cursor.execute(u'SELECT /* SLOW OK */ COUNT(*) FROM revision WHERE rev_user=' + userid + u' AND rev_timestamp<' + timestamp + u';') #Get number of edits since before timestamp
        results = cursor.fetchall()
        time.sleep(throttletime)
    if results[0][0] < 10:  #If edits < 10, user is not autoconfirmed
        return False
    try:
        #print "2",
        cursor.execute(u'SELECT /* SLOW OK */ DATEDIFF(' + timestamp + u', (SELECT user_registration FROM user WHERE user_id=' + userid + u'));')   #Get number of days before timestamp that user registered account
        results = cursor.fetchall()
        time.sleep(throttletime)
    except:
        #print "Retry2",
        cursor.execute(u'SELECT /* SLOW OK */ DATEDIFF(' + timestamp + u', (SELECT user_registration FROM user WHERE user_id=' + userid + u'));')   #Get number of days before timestamp that user registered account
        results = cursor.fetchall()
        time.sleep(throttletime)
    if results[0][0] < 4:   #If number of days < 4, user is not autoconfirmed
        return False
    return True

def post_deletion_checks(article, creationtime, deletiontime, userid, username, date):   #Checks to do once we determine that an article by a non-autoconfirmed user has been deleted
    try:
        #print "3",
        cursor.execute(u'SELECT /* SLOW OK */ COUNT(*) FROM revision WHERE rev_user=' + userid + u' AND rev_timestamp>' + deletiontime + u';') #Get number of edits since after deletion time
        results = cursor.fetchall()
        time.sleep(throttletime)
    except:
        #print "Retry3",
        cursor.execute(u'SELECT /* SLOW OK */ COUNT(*) FROM revision WHERE rev_user=' + userid + u' AND rev_timestamp>' + deletiontime + u';') #Get number of edits since after deletion time
        results = cursor.fetchall()
        time.sleep(throttletime)
    if results[0][0] == 0:  #No edits were made after deletion
        users_quit[date] += 1
        if username not in unique_users_quit:
            unique_users_quit.append(username)
        return
    try:
        #print "4",
        cursor.execute(u'SELECT /* SLOW OK */ COUNT(*) FROM revision WHERE rev_user=' + userid + u';') #Get number of edits total
        results = cursor.fetchall()
        time.sleep(throttletime)
    except:
        #print "Retry4",
        cursor.execute(u'SELECT /* SLOW OK */ COUNT(*) FROM revision WHERE rev_user=' + userid + u';') #Get number of edits total
        results = cursor.fetchall()
        time.sleep(throttletime)
    if results[0][0] > 9:   #If user has 10 or more edits, we'll assume he's autoconfirmed, since this analysis is being done more than 4 days after the last article was created
        users_confirmed[date] += 1
        if username not in unique_users_confirmed:
            unique_users_confirmed.append(username)
    try:
        #print "5"
        cursor.execute(u'SELECT /* SLOW OK */ COUNT(*) FROM logging WHERE log_type="block" AND log_namespace=2 AND log_action="block" AND log_title="' + username.decode('utf-8') + u'" AND log_timestamp>"' + deletiontime + '";')
        results = cursor.fetchall()
        time.sleep(throttletime)
        if results[0][0] > 0:   #User has been blocked since deletion
            users_blocked[date] += 1
            if username not in unique_users_blocked:
                unique_users_blocked.append(username)
        else:
            return
        #print "6"
        cursor.execute(u'SELECT /* SLOW OK */ COUNT(*) FROM ipblocks WHERE ipb_address="' + username.decode('utf-8') + '";')
        results = cursor.fetchall()
        time.sleep(throttletime)
        if results[0][0] > 0:   #User is still blocked
            users_still_blocked[date] += 1
            if username not in unique_users_still_blocked:
                unique_users_still_blocked.append(username)
    except:
        print "Error with username: " + username
        return

def savestats(variable):
    f = open("acs/stats/" + variable + ".txt", "w")
    varvalue = eval(variable)
    total = 0
    for i in varvalue.itervalues():
        total += i
    f.write("Total: " + str(total) + "\n\n")
    for date in sorted(varvalue.iterkeys()):
        f.write(date + " " + str(varvalue[date]) + "\n")
    f.close()

def savestats2(variable):
    f = open("acs/stats/" + variable + ".txt", "w")
    varvalue = eval(variable)
    f.write("Total: " + str(len(varvalue)) + "\n\n")
    for dude in varvalue:
        f.write(dude + "\n")
    f.close()

def recoverdata():
    f = open("acs/stats/articles_by_autoconfirmed.txt", "r")
    data = f.readlines()[2:]
    f.close()
    for i in data:
        i = i.strip("\n").split(" ")
        articles_by_autoconfirmed[i[0]] = int(i[1])
        
    f = open("acs/stats/articles_by_non_autoconfirmed.txt", "r")
    data = f.readlines()[2:]
    f.close()
    for i in data:
        i = i.strip("\n").split(" ")
        articles_by_non_autoconfirmed[i[0]] = int(i[1])

    f = open("acs/stats/articles_kept.txt", "r")
    data = f.readlines()[2:]
    f.close()
    for i in data:
        i = i.strip("\n").split(" ")
        articles_kept[i[0]] = int(i[1])    

    f = open("acs/stats/unique_autoconfirmed.txt", "r")
    data = f.readlines()[2:]
    f.close()
    for i in data:
        unique_autoconfirmed.append(i.strip("\n"))

    f = open("acs/stats/unique_nonautoconfirmed.txt", "r")
    data = f.readlines()[2:]
    f.close()
    for i in data:
        unique_nonautoconfirmed.append(i.strip("\n"))
        

def main_notdeleted():
    print "Checking non-deleted articles..."
    for filename in os.listdir("acs/allarticles/"):    #1 file per day, loop through each file
        f = open("acs/allarticles/" + filename, "r")
        data = f.readlines()
        f.close()
        articles = []
        date = filename[:-4]
        c = 0
        m = str(len(data))
        for i in data:
            articles.append(i.strip("\n").split(" ", 3))    #Each entry in articles is a list consisting of [article_name, creation timestamp, userID, username]
        for entry in articles:
            c += 1
            if c % 100 == 0:
                print str(c) + "/" + m,
            article = entry[0]
            creationtime = entry[1]
            userid = entry[2]
            username = entry[3]
            
            if isIP(username):
                #print "IP address detected.  Skipping..."
                continue
            
            #If user was autoconfirmed at the time (either in the cache or check via SQL), update stats and move on to the next one.
            if username in autoconfirmedlist:
                articles_by_autoconfirmed[date] += 1
                articles_by_autoconfirmed_kept[date] += 1
                continue
            if autoconfirmed(userid, creationtime):
                autoconfirmedlist.append(username)
                articles_by_autoconfirmed[date] += 1
                articles_by_autoconfirmed_kept[date] += 1
                if username not in unique_autoconfirmed:
                    unique_autoconfirmed.append(username)
                continue

            #If we get to this point, then we know the user was not autoconfirmed.
            articles_by_non_autoconfirmed[date] += 1
            articles_kept[date] += 1
            if username not in unique_nonautoconfirmed:
                unique_nonautoconfirmed.append(username)

        print "Finished checking " + filename
        print "Saving stats to files..."
        savestats("articles_by_autoconfirmed")
        savestats("articles_by_autoconfirmed_kept")
        savestats("articles_by_nonautoconfirmed_kept")
        savestats("articles_by_non_autoconfirmed")
        savestats("articles_kept")
        savestats("articles_deleted")
        savestats("users_quit")
        savestats("users_confirmed")
        savestats("users_blocked")
        savestats("users_still_blocked")
            
        savestats2("unique_autoconfirmed")
        savestats2("unique_nonautoconfirmed")
        savestats2("unique_users_quit")
        savestats2("unique_users_confirmed")
        savestats2("unique_users_blocked")
        savestats2("unique_users_still_blocked")
        savestats2("unique_ips")
        print "Saved."
    print "Finished with non-deleted articles...\n\n\n"

def main_deleted():
    print "Checking deleted articles..."
    for filename in os.listdir("acs/deletedarticles/"):    #1 file per day, loop through each file
        f = open("acs/deletedarticles/" + filename, "r")
        data = f.readlines()
        f.close()
        articles = []
        date = filename[:-4]
        c = 0
        m = str(len(data))
        for i in data:
            articles.append(i.strip("\n").split(" ", 4))    #Each entry in articles is a list consisting of [article_name, creation timestamp, deletion timestamp, userID, username]
        for entry in articles:
            c += 1
            if c % 100 == 0:
                print "\n" + filename[:-4] + ":" + str(c) + "/" + m,
            article = entry[0]
            creationtime = entry[1]
            deletiontime = entry[2]
            userid = entry[3]
            username = entry[4]
            #print "u=" + username,
            if isIP(username):
                #print "IP address detected.  Skipping..."
                continue

            #If user was autoconfirmed at the time (either in the cache or check via SQL), update stats and move on to the next one.
            if username in autoconfirmedlist:
                articles_by_autoconfirmed_deleted[date] += 1
                articles_by_autoconfirmed[date] += 1
                continue
            if autoconfirmed(userid, creationtime):
                autoconfirmedlist.append(username)
                articles_by_autoconfirmed[date] += 1
                articles_by_autoconfirmed_deleted[date] += 1
                if username not in unique_autoconfirmed:
                    unique_autoconfirmed.append(username)
                continue

            #If we get to this point, then we know the user was not autoconfirmed.
            articles_by_non_autoconfirmed[date] += 1
            articles_deleted[date] += 1
            if username not in unique_nonautoconfirmed:
                unique_nonautoconfirmed.append(username)

            post_deletion_checks(article, creationtime, deletiontime, userid, username, date)
        print "Finished checking " + filename
        print "Saving stats to files..."
        savestats("articles_by_autoconfirmed")
        savestats("articles_by_autoconfirmed_deleted")
        savestats("articles_by_nonautoconfirmed_deleted")
        savestats("articles_by_non_autoconfirmed")
        savestats("articles_kept")
        savestats("articles_deleted")
        savestats("users_quit")
        savestats("users_confirmed")
        savestats("users_blocked")
        savestats("users_still_blocked")
            
        savestats2("unique_autoconfirmed")
        savestats2("unique_nonautoconfirmed")
        savestats2("unique_users_quit")
        savestats2("unique_users_confirmed")
        savestats2("unique_users_blocked")
        savestats2("unique_users_still_blocked")
        savestats2("unique_ips")
    print "Finished with deleted articles...\n\n\n"


def morestuff():    #more stats analysis of how many articles were kept/deleted for autoconfirmed/non-autoconfirmed users
    recoverdata()
    print "Data recovered."
    for filename in os.listdir("acs/allarticles/"):    #1 file per day, loop through each file
        print ".",
        f = open("acs/allarticles/" + filename, "r")
        data = f.readlines()
        f.close()
        date = filename[:-4]
        articles = []
        for i in data:
            articles.append(i.strip("\n").split(" ", 3))    #Each entry in articles is a list consisting of [article_name, creation timestamp, userID, username]
        for entry in articles:
            if entry[3] in unique_autoconfirmed:
                articles_by_autoconfirmed_kept[date] += 1
            else:
                articles_by_nonautoconfirmed_kept[date] += 1
    print "Kept articles done..."
    for filename in os.listdir("acs/deletedarticles/"):
        print ".",
        f = open("acs/deletedarticles/" + filename, "r")
        data = f.readlines()
        f.close()
        date = filename[:-4]
        articles = []
        for i in data:
            articles.append(i.strip("\n").split(" ", 4))    #Each entry in articles is a list consisting of [article_name, creation timestamp, deletion timestamp, userID, username]
        for entry in articles:
            username = entry[4]
            if isIP(username):
                continue
            if username in unique_autoconfirmed:
                articles_by_autoconfirmed_deleted[date] += 1
            else:
                articles_by_nonautoconfirmed_deleted[date] += 1
    print "Deleted articles done..."
    savestats("articles_by_autoconfirmed_kept")
    savestats("articles_by_nonautoconfirmed_kept")
    savestats("articles_by_autoconfirmed_deleted")
    savestats("articles_by_nonautoconfirmed_deleted")
    print "Stats saved."
                                                  

#Do the analysis    
main_notdeleted()
main_deleted()
#morestuff()


#Save stats to files
print "Saving stats to files..."
savestats("articles_by_autoconfirmed")
savestats("articles_by_autoconfirmed_kept")
savestats("articles_by_nonautoconfirmed_kept")
savestats("articles_by_autoconfirmed_deleted")
savestats("articles_by_nonautoconfirmed_deleted")
savestats("articles_by_non_autoconfirmed")
savestats("articles_kept")
savestats("articles_deleted")
savestats("users_quit")
savestats("users_confirmed")
savestats("users_blocked")
savestats("users_still_blocked")
    
savestats2("unique_autoconfirmed")
savestats2("unique_nonautoconfirmed")
savestats2("unique_users_quit")
savestats2("unique_users_confirmed")
savestats2("unique_users_blocked")
savestats2("unique_users_still_blocked")
savestats2("unique_ips")

print "\n\nFound " + str(numips) + " IP addresses."
print "Done!\n\n\n"

###################################### NOTES #############################################

#Main logic:
#1. Determine if article was created by autoconfirmed user.
##1a. First check autoconfirmedlist cache, if not in there, then SQL query.
##1b. If autoconfirmed then +1 to articles_by_autoconfirmed[date] and add name to autoconfirmedlist, if not then +1 to articles_by_nonautoconfirmed[date].
##1c. If autoconfirmed, then skip the rest and go on to the next one.  If not autoconfirmed, continue.
#2. Was article deleted?  (If filename is in /allarticles then yes, if in /deletedarticles then no.)
##2a. If deleted, +1 to articles_deleted[date].  If not, +1 to articles_kept[date].
##2b. If not deleted, skip the rest and go on to the next one.  If deleted, continue.
#3. Did the user make any edits after article was deleted?  If not, +1 to users_quit[date].
#4. Did the user make more edits and eventually become autoconfirmed?  If so, +1 to users_confirmed[date].
#5. Has the user been blocked since article was deleted?  If so, +1 to users_blocked[date].
#6. Is the user still blocked?  If so, +1 to users_still_blocked[date].


#SQL Reference:

#Find number of edits by a user before/after a certain timestamp:
##SELECT COUNT(*) FROM revision where rev_user=1234567 and rev_timestamp<"20110101000000";

#Find user registration date:
##SELECT user_registration FROM user WHERE user_id=3863102;

#Find number of days registered since timestamp:
##SELECT DATEDIFF(<timestamp>, (SELECT user_registration FROM user WHERE user_id=3863102));

#Find if user is currently blocked:
##SELECT COUNT(*) FROM ipblocks WHERE ipb_user=3863102;

#Find if user was blocked after a certain timestamp:
##SELECT COUNT(*) FROM logging WHERE log_type='block' AND log_namespace=2 AND log_action='block' AND log_title='Snottywong AND log_timestamp>'20101201000000''
