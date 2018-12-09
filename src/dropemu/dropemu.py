#!/usr/bin/env python

import requests
import urllib
import cmd
import json
import zlib
import os
import binascii
import sys
import uuid
import time
import io

from common import list_url, fetch_url, register_url, commit_url, store_url
from common import headers, dropbox_hash, store, form_pickle, base64_to_digest
from common import make_unicode_broken

PY3 = sys.version_info[0] == 3

host_id = sys.argv[1]
print("Using host_Key = %s ..." % host_id)

# Fetch initial data
print("Fetching data ...")
data = 'nonce=None&host_characteristics={}&sscv_auth_version=2&machine_id=00000000-0000-0000-0000-000000000000&sync_engine_version=33.4.16&uuid=88491860316746&server_list=True&install_type=None&hostname=localhost.localdomain&update_manager_id=None&host_key=%s&client_info={}&platform_version=None&buildno=Dropbox-lnx.x86_64-34.4.22&un=["Linux", "localhost.localdomain", "4.12.9-200.fc25.x86_64", "#1 SMP Fri Aug 25 13:23:30 UTC 2017", "x86_64", "x86_64"]&cdm_version=6&tag=' % (host_id)
r = requests.post(register_url, data=data, headers=headers, verify=False)
data = json.loads(r.text)
host_int = data["host_int"]
root_ns = data["root_ns"]
uid = data["uid"]

# Fetch list of files
data = 'host_key=%s&initial_list=1&server_list=1&use_64bit_ns_ids=True&home_ns_id=%s&need_sandboxes=1&home_ns_path=&include_deleted=1&extended_namespace_info=1&buildno=Dropbox-lnx.x86_64-34.4.22&ns_p2p_key_map={"%s": null}&cdm_version=6&paired_host_key=None&dict_return=1&root_ns_id=%s&ns_cursors=%s:&return_file_ids=1&xattrs=1&only_directories=0' % (host_id, root_ns, root_ns, root_ns, root_ns)
headers["X-DBX-REQ-ID"] = uuid.uuid4().hex
headers["X-Dropbox-UID"] = "%s" % uid
headers["X-Dropbox-NSID"] = "all"
headers["X-Dropbox-Path-Root"] = "%s" % root_ns
r = requests.post(list_url, data=data, headers=headers, verify=False)
data = json.loads(r.text)
paths = data["list"]


def get_path(ID):
    for path in paths:
        if str(path["ID"]) == ID:
            return path


def refresh():
    ID = 0
    for path in paths:
        path["ID"] = ID
        ID = ID + 1


class Dropbox(cmd.Cmd):
    """Simple command processor example."""
    def do_about(self, line):
        print("Dropbox OSS client v0.02 ;)")

    def do_ls(self, line):
        """ls
        does what you would expect"""

        refresh()
        print("%s%s%s%s" % ("ID".rjust(5), "type".rjust(5), "size".rjust(10), "path"))
        for path in paths:
            if path["is_dir"]:
                out = "d"
            else:
                out = "f"
            if path["size"] == -1:
                out = "g"  # gone
            print("%s%s%s%s" % (str(path["ID"]).rjust(5), out.rjust(5), str(path["size"]).rjust(10), path["path"]))

    def do_lls(self, line):
        """lls => local ls"""
        files = [f for f in os.listdir('.') if os.path.isfile(f)]
        print(files)

    def do_get(self, line):
        """get <ID>
        Get file identified by <ID>"""
        if not line:
            print("\nUsage: get <ID>\n")
            return

        path = get_path(line)
        if path:
            if path["is_dir"]:
                print("%s is a directory!" % path["path"])
                return
            elif path["size"] < 0:
                print("%s is gone!" % path["path"])
                return
        else:
            print("%s can't be found!" % line)
            return

        hd = '[["%s", null, null]]' % path["blocklist"]
        if PY3:
            hd = urllib.parse.quote_plus(hd)
        else:
            hd = urllib.quote_plus(hd)
        data = """host_id=%s&hashes=%s""" % (host_id, hd)
        print("Fetching %s (%s) ..." % (path["path"], path["blocklist"]))
        r = requests.post(fetch_url, data=data, headers=headers, verify=False)
        # buf = StringIO(r.content)
        buf = io.BytesIO(r.content)
        ret = []
        while True:
            head = buf.readline()
            if not head:
                break
            try:
                head = json.loads(make_unicode_broken(head))
            except Exception as exc:
                print(str(exc), r.content)
            ret.append((head['hash'], buf.read(head['len'])))
        for _, data in ret:
            decompressed = zlib.decompress(data)
            basename = os.path.basename(path["path"])
            with open(basename, "wb") as f:
                f.write(decompressed)
            print("Fetched %s :-)" % basename)
            break

    def do_rm(self, line):
        if not line:
            print("\nUsage: rm <filename>\n")
            return

        path = get_path(line)
        if path:
            if path["is_dir"]:
                print("%s is a directory!" % path["path"])
                return
            elif path["size"] < 0:
                print("%s is gone already!" % path["path"])
                return
        else:
            print("%s can't be found!" % line)
            return

        myhash = path["blocklist"]
        ns_id = root_ns

        template = """[
                {
                            "parent_blocklist": "%s",
                            "parent_attrs": null,
                            "blocklist": "",
                            "mtime": "-1",
                            "path": "%s",
                            "is_dir": false,
                            "fileid_rev": null,
                            "fileid_parent_fileid_type": null,
                            "fileid_gid": null,
                            "fileid_parent_fileid_gid": null,
                            "fileid_parent_fileid_rev": null,
                            "target_ns": null,
                            "attrs": {},
                            "ns_id": %s,
                            "size": -1
                        }
        ]""" % (myhash, path["path"], ns_id)

        template = form_pickle(template)
        headers["X-Dropbox-NSID"] = "%s" % root_ns
        print("Removing %s ..." % myhash)
        ds = "changeset_map=&commit_info=%s&allow_guid_sjid_hack=0&extended_ret=True&autoclose=&host_id=%s" % (template, host_id)
        r = requests.post(commit_url, data=ds, headers=headers, verify=False)
        print(r.content)
        r = requests.post(commit_url, data=ds, headers=headers, verify=False)
        print(r.content)

    def do_put(self, line):
        if not line:
            print("\nUsage: put <filename>\n")
            return
        try:
            content = open(line, "rb").read()
        except Exception as exc:
            print(str(exc))

        myhash = dropbox_hash(content)

        # is this hack OK?
        # ns_id = root_ns.split('_')[0]
        ns_id = root_ns

        template = """[
                {
                            "parent_blocklist": null,
                            "parent_attrs": null,
                            "blocklist": "%s",
                            "mtime": "%s",
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
                            "ns_id": %s,
                            "size": %s
                        }
        ]""" % (myhash, int(time.time()), os.path.basename(line), ns_id, len(content))  # instead to current timestamp, use file's original timestamp

        template = form_pickle(template)
        ds = "changeset_map=&commit_info=%s&allow_guid_sjid_hack=0&extended_ret=True&autoclose=&host_id=%s" % (template, host_id)
        r = requests.post(commit_url, data=ds, headers=headers, verify=False)

        print("Uploading %s ..." % myhash)
        md, mh = store(myhash, content, myhash, host_id, root_ns)
        mh["User-Agent"] = headers["User-Agent"]
        mh["Accept-Encoding"] = "identity"
        mh["X-DBX-REQ-ID"] = uuid.uuid4().hex
        mh["X-Dropbox-UID"] = "%s" % uid
        mh["X-Dropbox-Path-Root"] = "%s" % root_ns
        mh["X-Dropbox-User-Agent"] = headers["User-Agent"]
        mh["X-DBX-RETRY"] = "1"
        mh["X-Dropbox-Locale"] = "en_US"
        r = requests.post(store_url, data=md, headers=mh, verify=False)
        print(r.content)

        headers["X-Dropbox-NSID"] = "%s" % root_ns
        r = requests.post(commit_url, data=ds, headers=headers, verify=False)
        print(r.content)

    def preloop(self):
        refresh()
        print("\nRefreshing Cache ...\n")

    def do_hash(self, line):
        """hash <ID>
        prints hash of the file identified by <ID>"""
        if not line:
            print("\nUsage: hash <ID>\n")
            return

        path = get_path(line)
        if path:
            if path["is_dir"]:
                print("%s is a directory!" % path["path"])
            elif path["size"] < 0:
                print("%s is gone!" % path["path"])
            else:
                print("Custom base64 : %s" % path["blocklist"])
                print("Standard SHA256 : %s" % binascii.hexlify(base64_to_digest(str(path["blocklist"]))))
        else:
            print("%s can't be found!" % line)

    def do_EOF(self, line):
        return True

if __name__ == "__main__":
    Dropbox().cmdloop()
