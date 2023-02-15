
import logging, sys, pytz, os, headscale, requests
from datetime            import datetime, timedelta, date
from dateutil            import parser

log = logging.getLogger('server.helper')
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
log.addHandler(handler)
log.setLevel(logging.INFO)

def pretty_print_duration(duration):
    days, seconds = duration.days, duration.seconds
    hours = (days * 24 + seconds // 3600)
    mins  = ((seconds % 3600) // 60)
    secs  = (seconds % 60)
    if   days  > 0: return str(days ) + " days ago"     if days  >  1 else str(days ) + " day ago"
    elif hours > 0: return str(hours) + " hours ago"    if hours >  1 else str(hours) + " hour ago"
    elif mins  > 0: return str(mins ) + " minutes ago"  if mins  >  1 else str(mins ) + " minute ago"
    else:           return str(secs ) + " seconds ago"  if secs  >= 1 or secs == 0 else str(secs ) + " second ago"

def text_color_duration(duration):
    days, seconds = duration.days, duration.seconds
    hours = (days * 24 + seconds // 3600)
    mins  = ((seconds % 3600) // 60)
    secs  = (seconds % 60)
    if   days  > 30: return "grey-text                      "
    elif days  > 14: return "red-text         text-darken-2 "
    elif days  >  5: return "deep-orange-text text-lighten-1"
    elif days  >  1: return "deep-orange-text text-lighten-1"
    elif hours > 12: return "orange-text                    "
    elif hours >  1: return "orange-text      text-lighten-2"      
    elif hours == 1: return "yellow-text                    "
    elif mins  > 15: return "yellow-text      text-lighten-2"
    elif mins  >  5: return "green-text       text-lighten-3"
    elif secs  > 30: return "green-text       text-lighten-2" 
    else:            return "green-text                     "

def key_test():
    api_key    = headscale.get_api_key()
    url        = headscale.get_url()

    # Test the API key.  If the test fails, return a failure.  
    # AKA, if headscale returns Unauthorized, fail:
    status = headscale.test_api_key(url, api_key)
    if status != 200: return False
    else:
        # Check if the key needs to be renewed
        headscale.renew_api_key(url, api_key) 
        return True

def get_color(id, type = ""):
    # Define the colors... Seems like a good number to start with
    if type == "text":
        colors = [
            "red-text         text-lighten-1",
            "teal-text        text-lighten-1",
            "blue-text        text-lighten-1",
            "blue-grey-text   text-lighten-1",
            "indigo-text      text-lighten-2",
            "green-text       text-lighten-1",
            "deep-orange-text text-lighten-1",
            "yellow-text      text-lighten-2",
            "purple-text      text-lighten-2",
            "indigo-text      text-lighten-2",
            "brown-text       text-lighten-1",
            "grey-text        text-lighten-1",
        ]
        index = id % len(colors)
        return colors[index]
    else:
        colors = [
            "red         lighten-1",
            "teal        lighten-1",
            "blue        lighten-1",
            "blue-grey   lighten-1",
            "indigo      lighten-2",
            "green       lighten-1",
            "deep-orange lighten-1",
            "yellow      lighten-2",
            "purple      lighten-2",
            "indigo      lighten-2",
            "brown       lighten-1",
            "grey        lighten-1",
        ]
        index = id % len(colors)
        return colors[index]

def error_message_format(type, title, message):
    content = """
        <ul class="collection">
        <li class="collection-item avatar">
    """
    match type.lower():
        case "warning":
            icon  = """<i class="material-icons circle yellow">priority_high</i>"""
            title = """<span class="title">Warning</span>"""
        case "success":
            icon  = """<i class="material-icons circle green">check</i>"""
            title = """<span class="title">Success</span>"""
        case "error":
            icon  = """<i class="material-icons circle red">warning</i>"""
            title = """<span class="title">Error</span>"""
        case "information":
            icon  = """<i class="material-icons circle grey">help</i>"""
            title = """<span class="title">Information</span>"""

    content = content+icon+title+message        
    content = content+"""
            </li>
        </ul>
    """
    return content

def startup_checks():
    url = headscale.get_url()

    # Return an error message if things fail. 
    # Return a formatted error message for EACH fail.
    # Otherwise, return "Pass"
    pass = True

    # Check 1:  See if the Headscale server is reachable:
    reachable = NULL
    response = requests.delete(
        str(url)+"/api/v1/",
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer '+str(api_key)
        }
    )
    if response.status_code == 200:
        reachable = True
    else:
        reachable = False
        pass = False
    
    # Check 2:  See if /data/ is writable:
    writable = NULL
    try:
        key_file = open("/data/key.txt", "wb+")
        writable = True
    except PermissionError:
        writable = False
        pass = False
    
    if pass: return "Pass"

    messageHTML = ""
    # Generate the message:
    if not reachable:
        message = """
        <p>Your headscale server is either unreachable or not properly configured.  
        Please ensure your configuration is correct (Check for 200 status on 
        """+url+"""/api/v1 failed.)</p>
        """
        messageHTML += format_error_message("Error", "Headscale unreachable", message)
    if not writable:
        message = """
        <p>/data/key.txt is not writable.  Please ensure your 
        permissions are correct. /data mount should be writable 
        by UID/GID 1000:1000</p>
        """
        messageHTML += format_error_message("Error", "/data not writable", message)
    return messageHTML