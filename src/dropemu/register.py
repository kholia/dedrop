#!/usr/bin/env python

import requests
import json
from common import nonce_url, register_url, headers
import time

requests.packages.urllib3.disable_warnings()

print "Initializing Dropbox CLI client (dropemu) ...\n"

# Get a host_id / host_key assigned
data = 'nonce=None&host_characteristics={}&sscv_auth_version=2&machine_id=00000000-0000-0000-0000-000000000000&sync_engine_version=33.4.16&uuid=88491860316746&server_list=True&install_type=None&hostname=localhost.localdomain&update_manager_id=None&host_key=%s&client_info={}&platform_version=None&buildno=Dropbox-lnx.x86_64-34.4.22&un=["Linux", "localhost.localdomain", "4.12.9-200.fc25.x86_64", "#1 SMP Fri Aug 25 13:23:30 UTC 2017", "x86_64", "x86_64"]&cdm_version=6&tag=' % "None"
r = requests.post(register_url, data=data, headers=headers, verify=False)
data = json.loads(r.text)
host_key = data["host_key"]
if not host_key:
    assert(0)
print("Your host_id / host_key / host_secret is %s.\n" % host_key)

# Link this host_key with the Dropbox account
data = 'host_key=%s&cli_nonce=None' % host_key
r = requests.post(nonce_url, data=data, headers=headers, verify=False)
data = json.loads(r.text)
url = data["nonce_uri"]
print("Please visit %s in a web browser to link this device.\n" % url)

# Check if this device has been linked yet!
while True:
    time.sleep(4)
    data = 'nonce=None&host_characteristics={}&sscv_auth_version=2&machine_id=00000000-0000-0000-0000-000000000000&sync_engine_version=33.4.16&uuid=88491860316746&server_list=True&install_type=None&hostname=localhost.localdomain&update_manager_id=None&host_key=%s&client_info={}&platform_version=None&buildno=Dropbox-lnx.x86_64-34.4.22&un=["Linux", "localhost.localdomain", "4.12.9-200.fc25.x86_64", "#1 SMP Fri Aug 25 13:23:30 UTC 2017", "x86_64", "x86_64"]&cdm_version=6&tag=' % host_key
    r = requests.post(register_url, data=data, headers=headers, verify=False)
    data = json.loads(r.text)
    root_ns_id = data["root_ns_id"]
    if not root_ns_id or root_ns_id == "null":
        # keep going
        pass
    else:
        print("This device is now linked with (%s) as the host_key." % host_key)
        break
