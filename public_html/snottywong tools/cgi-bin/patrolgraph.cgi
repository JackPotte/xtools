#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Min, max, average
#Fix missing data points
#Make index page

import cgi
import os
import datetime
import re
import sys
import traceback

def formatdate(d):
    date = datetime.datetime(int(d[:4]), int(d[4:6]), int(d[6:8]), int(d[8:10]), int(d[10:12]), int(d[12:14]))
    return date.strftime("%Y %b %d %H:00")

def formatdate2(d):
    date = datetime.datetime(int(d[:4]), int(d[4:6]), int(d[6:8]), int(d[8:10]), int(d[10:12]), int(d[12:14])) 
    return "new Date(Date.UTC(%s,%s,%s,%s))" % (date.year, date.month-1, date.day, date.hour)   #Javascript Date object - month is zero-referenced
    #return date.strftime("new Date(Date.UTC(%Y,%m,%d,%H))")

def smoothdata(data, smoothinglevel):   #smooth the data, kinda blows
    if len(data) <= smoothinglevel:
        return data
    newdata = []
    for index in range(len(data)):
        if index <= smoothinglevel:     #don't smooth the first n data points
            newdata.append(data[index])
        else:
            newdata.append([data[index][0], str(float(newdata[index-1][1]) + (1.0/smoothinglevel)*(float(data[index][1]) - float(data[index-smoothinglevel][1])))])
    return newdata

tsregex = re.compile("<ts>(.*?)</ts>")
qregex = re.compile("<q>(.*?)</q>")
hours = 720

try:
    f = open("patroldata.txt", "r")
    data = f.readlines()
    f.close()
    
    form = cgi.FieldStorage()
    if "hours" in form:
        try:
            hours = min(len(data), int(form['hours'].value))
        except:
            hours = 720

    f = open("patrolgraphlog.txt", "a")
    f.write("<log><ip>" + os.environ["REMOTE_ADDR"] + "</ip><timestamp>" + datetime.datetime.today().strftime("%m/%d/%y %H:%M:%S") + "</timestamp><hours>" + str(hours) + "</hours></log>\n")
    f.close()
            
    if len(data) > hours:
        data = data[-hours:]
    datapoints = []
    qs = []
    for line in data:
        ts = tsregex.search(line).group(1)
        q = qregex.search(line).group(1)
        #Need some logic here to insert null data points if some were missed.
        if len(qs) > 0 and float(q) > qs[-1]+0.05:
            q = str(qs[-1]+0.05)
        qs.append(float(q))
        datapoints.append([ts, q])
    #datapoints = smoothdata(datapoints, 24)
    html="""<html>
<head>
<title>Special:Newpages queue length in days</title>
<LINK href="menubar3.css" rel="stylesheet" type="text/css">
<script type="text/javascript" src="https://www.google.com/jsapi"></script>
<script type="text/javascript">
google.load("visualization", "1", {packages:["corechart"]});
google.setOnLoadCallback(drawChart);
function drawChart() {
var data = new google.visualization.DataTable();
data.addColumn('datetime', 'datetime');
data.addColumn('number', 'Newpages queue (days)');
"""
    for p in datapoints:
        #html += 'data.addRow(["' + formatdate(p[0]) + '",' + str(p[1]) + ']);\n'
        html += 'data.addRow([' + formatdate2(p[0]) + ',' + str(p[1]) + ']);\n'
    try:
        vaxis = 'curveType: "%s", vAxis: {viewWindow: {max: %s, min: %s}, viewWindowMode: "explicit"}' % ("none" if hours>100 else "function", min(int(max(qs)+1), 30), max(int(min(qs)), 0))
    except ValueError:
        vaxis = 'curveType: "%s", vAxis: {viewWindow: {max: %s, min: %s}, viewWindowMode: "explicit"}' % ("none" if hours>100 else "function", 30, 0)
		
    html += """var formatter = new google.visualization.DateFormat({pattern: "MMM d H':'mm z"});
formatter.format(data,0);
var chart = new google.visualization.LineChart(document.getElementById('chart_div'));
chart.draw(data, {width: 875, height: 600, wmode: "opaque", title: "Special:Newpages queue length in days", interpolateNulls: "True", backgroundColor: "#eeeedd", pointSize:0, %s, hAxis: {slantedText: "False", maxAlternation:1}});
}
</script>
</head>
<BODY id="no">
<!-- <script type="text/javascript" src="/menubar.js"></script>  <==NOT WORKING -->
<br>
<div id="chart_div" style="margin:0;padding:0;position:absolute;top:40;left:0;"></div>
""" % (vaxis)

    html += '<div style="position:absolute;top:640;"><br><small>Display the last:&nbsp;<a href="cgi-bin/patrolgraph.cgi?hours=720">30 days</a>&nbsp;&ndash;&nbsp;<a href="cgi-bin/patrolgraph.cgi?hours=336">2 weeks</a>&nbsp;&ndash;&nbsp;<a href="cgi-bin/patrolgraph.cgi?hours=168">1 week</a>&nbsp;&ndash;&nbsp;<a href="cgi-bin/patrolgraph.cgi?hours=72">3 days</a>&nbsp;&ndash;&nbsp;<a href="cgi-bin/patrolgraph.cgi?hours=24">1 day</a>&nbsp;&ndash;&nbsp;<a href="cgi-bin/patrolgraph.cgi?hours=12">12 hours</a></small><br>'
    try:
        html += '<ul><li>Minimum: ' + str(min(qs)) + " days</li>\n"
        html += "<li>Maximum: " + str(max(qs)) + " days</li>\n"
    except ValueError:
        html += "<ul><li>Minimum: 0 days</li>\n"
        html += "<li>Maximum: 30 days</li>\n"
    try:
        html += "<li>Average: " + str(round(sum(qs)/len(qs), 2)) + " days</li>\n</ul>"
    except ZeroDivisionError:
        html += "<li>Average: 15 days</li>\n</ul>"
    try:
        html += "Last updated: " + formatdate(datapoints[-1][0]) + " UTC<br>\n"
    except IndexError:
        html += "Last updated: - UTC<br>\n"
    html += "<strong>(Graph no longer being updated)</strong></div>"
    html += "</body>\n</html>"

    print html
except:
    print sys.exc_info()[0]
    print traceback.print_exc(file=sys.stdout)
