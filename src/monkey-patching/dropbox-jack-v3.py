#!/usr/bin/env python

# 1. host_id and host_int can captured from DEBUG logs *OR*
#    host_id can be extracted from ~/.dropbox/config.dbx and
#    host_int can be "sniffed" from Dropbox LAN sync traffic.
#
#    host_int can also be fetched from the Dropbox server!
#
# 2. export DBDEV=a2y6shya
#
# 3. Restart dropboxd and capture its output

host_id = "147c6cf0e21dcf913e85dcb14a9d5af4"

import hashlib
import time
import webbrowser
import requests
import json

headers = {'content-type': 'application/x-www-form-urlencoded', 'User-Agent': """DropboxDesktopClient/2.0.2 (Linux; 3.9-rc4; Some ARM ;-); en_US)"""}
register_url = 'https://client10.dropbox.com/register_host'

# fetch host_int
data = """buildno=Dropbox-win-1.7.5&tag=&uuid=123456&server_list=True&host_id=%s&hostname=random""" % host_id
r = requests.post(register_url, data=data, headers=headers)
data = json.loads(r.text)
host_int = data["host_int"]
root_ns = data["root_ns"]

# generate auto-login URL
now = int(time.time())
h = hashlib.sha1('%ssKeevie4jeeVie9bEen5baRFin9%d' % (host_id, now)).hexdigest()
url = "https://www.dropbox.com/tray_login?i=%d&t=%d&v=%s&url=home&cl=en_US" % (host_int, now, h)
print url

webbrowser.open_new(url)
