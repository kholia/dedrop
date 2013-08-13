import json
import requests
import hashlib
import time


# put your host_id below
host_id = "d5e11298cb1d1c2521317fdd416ddd51"

# code to get host_int back
data = """buildno=Dropbox-win-1.7.5&tag=&uuid=123456&server_list=True&host_id=%s&hostname=random""" % host_id

url = 'https://client10.dropbox.com/register_host'

headers = {'content-type': 'application/x-www-form-urlencoded', 'User-Agent': """DropboxDesktopClient/1.7.5 (Windows; 7; i32; en_US)"""}

r = requests.post(url, data=data, headers=headers)

data = json.loads(r.text)

host_int = data["host_int"]

# code for "Desktop Login" URL generation
now = int(time.time())

h = hashlib.sha1('%ssKeevie4jeeVie9bEen5baRFin9%d' % (host_id, now)).hexdigest()

url = "https://www.dropbox.com/tray_login?i=%d&t=%d&v=%s&url=home&cl=en_US" % (host_int, now, h)

print url
