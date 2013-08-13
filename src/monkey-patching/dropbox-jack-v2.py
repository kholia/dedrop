#!/usr/bin/env python

# 1. host_id and host_int can captured from DEBUG logs *OR*
#    host_id can be extracted from ~/.dropbox/config.dbx and
#    host_int can be "sniffed" from Dropbox LAN sync traffic
# 2. export DBDEV=a2y6shya
# 3. Restart dropboxd and capture its output

host_id = "147c6cf0e21dcf913e85dcb14a9d5af4"
host_int = 487148435

import hashlib
import time
import webbrowser

now = int(time.time())

h = hashlib.sha1('%ssKeevie4jeeVie9bEen5baRFin9%d' % (host_id, now)).hexdigest()

url = "https://www.dropbox.com/tray_login?i=%d&t=%d&v=%s&url=home&cl=en_US" % (host_int, now, h)

print url

webbrowser.open_new(url)
