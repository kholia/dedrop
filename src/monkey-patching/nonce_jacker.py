import json
import requests
import hashlib
import time


# put your host_id below
host_id = "d5e11298cb1d1c2521317fdd416ddd51"

# code to get host_int back
data = """ia=1&host_id=%s""" % host_id

url = 'https://client10.dropbox.com/desktop_login_sync'

headers = {'content-type': 'application/x-www-form-urlencoded', 'User-Agent': """DropboxDesktopClient/1.7.5 (Windows; 7; i32; en_US)"""}

r = requests.post(url, data=data, headers=headers)

data = json.loads(r.text)

nonces = data["nonces"]

print nonces

