function loadNamespaces() {
	$(function() {
			$.get("cgi-bin/namespace.cgi?db=" + document.myform.server.options[document.myform.server.selectedIndex].value + "_p", processResults);
    });
}

function processResults(results) {
	var nslist = jQuery.parseJSON(results);
	var nsselect = document.myform.ns.options;
	nsselect.length = 1;
	for (var i=0;i<nslist.length;i++)
	{
		if (nslist[i][1] < 0) continue;
		if (nslist[i][0] == "") nslist[i][0] = "(Article)";
		nsselect[nsselect.length] = new Option(nslist[i][0], nslist[i][1]);
	}
}
