#!/usr/bin/env python

# TODO:
#
# Allow device registrations to be done. By doing this, we don't need
# to steal host_id from official client anymore ;)

# put your host_id below
host_id = "147c6cf0e21dcf913e85dcb14a9d5af4"

import requests
import time
import urllib
import cmd
import json
import zlib
import cStringIO
import os
from binascii import b2a_base64
from hashlib import sha256
import string
import base64
import binascii

_to_websafe = string.maketrans('+/', '-_')
_from_websafe = string.maketrans('-_~', '+/=')

def digest_to_base64(digest):
    return b2a_base64(digest)[:-2].translate(_to_websafe)

BOUNDARY = '-----------------------------%d' % int(time.time() * 1000)

def encode_multipart_formdata(fields = None, files = (), myhash=None, already_compressed = False):
    CRLF = '\r\n'
    L = []
    if fields:
        for key, value in fields.iteritems():
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(str(value))

    for key, filename, value in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: application/octet-stream')
        L.append('')
        if not already_compressed:
            value = zlib.compress(value)
        L.append(value)

    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    headers = {'Content-Type': 'multipart/form-data; boundary=%s' % BOUNDARY,
        'Content-Length': len(body)}
    return (body, headers)


def store(hash, data, myhash, already_compressed = False, ns_id_to_blocklists=None):
    fields = dict(host_id=host_id, hash=hash)
    if ns_id_to_blocklists:
        fields['ns_id_to_blocklists'] = ns_id_to_blocklists
    if not already_compressed:
        data = zlib.compress(data)
    files = (('upload_file', hash, data),)
    data, headers = encode_multipart_formdata(fields=fields,
        files=files, myhash=myhash, already_compressed=True)

    return (data, headers)


def base64_to_digest(b64_digest):
    return base64.decodestring(b64_digest.translate(_from_websafe) + '=')

class DropboxHasher(object):
    __slots__ = ('d', 'total')

    def __init__(self):
        self.d = sha256()
        self.total = 0

    def update(self, data):
        self.d.update(data)
        self.total += len(data)

    def digest(self, data = None):
        if data:
            self.update(data)
        return b2a_base64(self.d.digest())[:-2].translate(_to_websafe)

def dropbox_hash(contents):
      return DropboxHasher().digest(contents)


# URLs
list_url = 'https://client10.dropbox.com/list'
fetch_url = 'https://dl-client568.dropbox.com/retrieve_batch'
store_url = 'https://dl-client568.dropbox.com/store'
register_url = 'https://client10.dropbox.com/register_host'
commit_url = 'https://client10.dropbox.com/commit_batch'
# "/list_dirs" fetches list of directories
# "/desktop_login_sync" => get nonces which are useful for hijacking accounts

# headers
headers = {'content-type': 'application/x-www-form-urlencoded', 'User-Agent': """DropboxDesktopClient/2.0.2 (Linux; 3.9-rc4; Some ARM ;-); en_US)"""}

# message
print "Fetching data ..."
# fetch initial data
data = """buildno=Dropbox-win-1.7.5&tag=&uuid=123456&server_list=True&host_id=%s&hostname=random""" % host_id
r = requests.post(register_url, data=data, headers=headers)
data = json.loads(r.text)
host_int = data["host_int"]
root_ns = data["root_ns"]

# fetch data list
root_ns = str(root_ns) + "_-1"
data = """buildno=Dropbox-win-1.7.5&tag=&uuid=123456&server_list=True&host_id=%s&hostname=random""" % host_id
data = data + "&ns_map=%s&dict_return=1&server_list=True&last_cu_id=-1&need_sandboxes=0&xattrs=True" % root_ns
r = requests.post(list_url, data=data, headers=headers)
data = json.loads(r.text)
paths = data["list"]
# print paths

def get_path(ID):
    for path in paths:
        if str(path["ID"]) == ID:
            return path

def refresh():
    ID = 0
    for path in paths:
        path["ID"] = ID
        ID = ID + 1

def form_pickle(s):
    return base64.encodestring(zlib.compress(s)).translate(_to_websafe, ' \n\t')

def unform_pickle(s):
    s = s.translate(_from_websafe)
    s = base64.decodestring(s + "==")

    s = zlib.decompress(s)
    print s
    return base64.encodestring(zlib.compress(s)).translate(_to_websafe, ' \n\t')

class Dropbox(cmd.Cmd):
    """Simple command processor example."""
    def do_about(self, line):
        print "Dropbox OSS client v0.001 ;)"

    def do_ls(self, line):
        """ls
        does what you would expect"""

        refresh()
        print "ID".rjust(5), "type".rjust(5), "size".rjust(10), "path"
        for path in paths:
            if path["is_dir"]:
                out = "d"
            else:
                out = "f"
            if path["size"] == -1:
                out = "g" # gone
            print str(path["ID"]).rjust(5), out.rjust(5), str(path["size"]).rjust(10), path["path"]

    def do_lls(self, line):
        """lls => local ls"""
        files = [f for f in os.listdir('.') if os.path.isfile(f)]
        print files


    def do_get(self, line):
        """get <ID>
        Get file identified by <ID>"""
        if not line:
            print "\nUsage: get <ID>\n"
            return

        path = get_path(line)
        if path:
            if path["is_dir"]:
                print "%s is a directory!" % path["path"]
                return
            elif path["size"] < 0:
                print "%s is gone!" % path["path"]
                return
        else:
            print "%s can't be found!" % line
            return

        hd  = '[["%s", null, null]]' % path["blocklist"]
        hd = urllib.quote_plus(hd)
        data = """host_id=%s&hashes=%s""" % (host_id, hd)
        print "Fetching %s (%s) ..." % (path["path"], path["blocklist"])
        r  = requests.post(fetch_url, data=data, headers=headers)
        buf = cStringIO.StringIO(r.content)
        ret = []
        while True:
            head = buf.readline()
            if not head:
                break
            try:
                head = json.loads(head)
            except Exception, exc:
                print str(exc), r.content
            ret.append((head['hash'], buf.read(head['len'])))
        for _, data in ret:
            decompressed = zlib.decompress(data)
            basename = os.path.basename(path["path"])
            with open(basename, "w") as f:
                f.write(decompressed)
            print "Fetched %s :-)" % basename
            break

    def do_put(self, line):
        if not line:
            print "\nUsage: put <filename>\n"
            return
        try:
            content = open(line, "r").read()
        except Exception as exc:
            print str(exc)

        # content = "We own Dropbox now ;)"
        myhash = dropbox_hash(content)

        # is this hack OK?
        ns_id = root_ns.split('_')[0]
        ns_id = int(ns_id)

        template = """[
                {
                            "parent_blocklist": null,
                            "parent_attrs": null,
                            "blocklist": "%s",
                            "mtime": 1364411770,
                            "path": "/%s",
                            "is_dir": false,
                            "target_ns": null,
                            "attrs": {
                                            "exif": null,
                                            "dropbox_camera_upload": null,
                                            "dropbox_mute": null,
                                            "mac": null,
                                            "flac": null,
                                            "dropbox": null,
                                            "dropbox_tag": null
                                        },
                            "ns_id": %d,
                            "size": %s
                        }
        ]""" % (myhash, os.path.basename(line), ns_id, len(content))

        template = form_pickle(template)

        ds = "changeset_map=&commit_info=%s&allow_guid_sjid_hack=0&extended_ret=True&autoclose=&host_id=%s" % (template, host_id)
        md, mh =  store(myhash, content, myhash)
        mh["User-Agent"] = """DropboxDesktopClient/2.0.2 (Linux; 3.9-rc4; Some ARM ;-)"""
        mh["Accept-Encoding"] = "identity"
        # print mh
        mc = {}
        mc["User-Agent"] = """DropboxDesktopClient/2.0.2 (Linux; 3.9-rc4; Some ARM ;-)"""
        mc["Accept-Encoding"] = "identity"
        mc["Content-type"] = "application/x-www-form-urlencoded"

        r  = requests.post(commit_url, data=ds, headers=mc)
        print r.content
        print "Uploading", myhash, " ..."
        r  = requests.post(store_url, data=md, headers=mh)
        print r.content
        r  = requests.post(commit_url, data=ds, headers=mc)
        print r.content


    def preloop(self):
        refresh()
        print "\nRefreshing Cache ...\n"

    def do_hash(self, line):
        """hash <ID>
        prints hash of the file identified by <ID>"""
        if not line:
            print "\nUsage: hash <ID>\n"
            return

        path = get_path(line)
        if path:
            if path["is_dir"]:
                print "%s is a directory!" % path["path"]
            elif path["size"] < 0:
                print "%s is gone!" % path["path"]
            else:
                print "Custom base64 : %s" % path["blocklist"]
                print "Standard SHA256 : %s" % binascii.hexlify(base64_to_digest(str(path["blocklist"])))
        else:
            print "%s can't be found!" % line

    def do_EOF(self, line):
        return True

if __name__ == "__main__":
    Dropbox().cmdloop()

