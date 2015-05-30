function getQuerystring(key)
{ 
  key = key.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
  var regex = new RegExp("[\\?&]"+key+"=([^&#]*)");
  var qs = regex.exec(window.location.href);
  if(qs == null)
    return "";
  else
    return qs[1];
}

function initForm()
{
    tehname = getQuerystring("page");
    if (tehname != "")
        {
        document.forms["myform"].elements["page"].value = unescape(tehname.replace(/[_+]/gi, " "));
        document.forms["myform"].elements["max"].value = "100"
        document.forms["myform"].elements["name"].focus()
        }
}