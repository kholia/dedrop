#!/usr/bin/env python

from binascii import b2a_base64
from hashlib import sha256
import zlib
import string
import time
import base64
import requests
import uuid
import sys

DROPBOX_MAX_BLOCK_SIZE = 4194304
PY3 = sys.version_info[0] == 3

if PY3:
    _to_websafe = bytes.maketrans(b'+/=', b'-_~')
    _from_websafe = bytes.maketrans(b'-_~', b'+/=')
else:
    _to_websafe = string.maketrans('+/=', '-_~')
    _from_websafe = string.maketrans('-_~', '+/=')

# _from_websafe = string.maketrans('-_~', '+/=')
requests.packages.urllib3.disable_warnings()


def digest_to_base64(digest):
    return b2a_base64(digest)[:-2].translate(_to_websafe)

BOUNDARY = '-----------------------------%d' % int(time.time() * 1000)


def encode_multipart_formdata(fields=None, files=(), myhash=None, already_compressed=False):
    CRLF = '\r\n'
    L = []
    if fields:
        if PY3:
            kvs = list(fields.items())
        else:
            kvs = fields.iteritems()
        for key, value in kvs:
            L.append('--' + BOUNDARY)
            if PY3:
                key = make_bytes(key, 'ascii')
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            if PY3:
                if isinstance(value, bytes):
                    pass
                else:
                    value = str(value).encode('ascii')
                L.append(value)
            else:
                L.append(str(value))

    for key, filename, value in files:
        L.append('--' + BOUNDARY)
        if PY3:
            key = make_bytes(key, 'ascii')
            filename = make_bytes(filename, 'ascii')
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (filename, filename))
        L.append('Content-Type: application/octet-stream')
        L.append('')
        if not already_compressed:
            value = zlib.compress(value)
        L.append(value)

    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    headers = {'Content-Type': 'multipart/form-data; boundary=%s' % BOUNDARY,
               'Content-Length': "%s" % len(body)}
    return (body, headers)


def store(hash, data, myhash, host_id, root_ns, already_compressed=False, ns_id_to_blocklists=None):
    fields = dict(host_key=host_id, batch_info_version="2", batch_info='[{"advisory_nses": [%s], "hash": "%s", "parent": null}]' % (root_ns, myhash))
    if ns_id_to_blocklists:
        fields['ns_id_to_blocklists'] = ns_id_to_blocklists
    if not already_compressed:
        data = zlib.compress(data)
    files = (('upload_file', hash, data),)
    data, headers = encode_multipart_formdata(fields=fields, files=files,
                                              myhash=myhash,
                                              already_compressed=True)

    return (data, headers)


def form_pickle(s):
    r = base64.encodestring(zlib.compress(make_bytes(s, 'ascii'))).translate(_to_websafe, b' \n\t')
    if PY3:
        r = r.decode("ascii")
    return r


def unform_pickle(s):
    s = s.translate(_from_websafe)
    s = base64.decodestring(s + "==")

    s = zlib.decompress(s)
    print(s)
    return base64.encodestring(zlib.compress(s)).translate(_to_websafe, b' \n\t')


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

    def digest(self, data=None):
        if data:
            self.update(data)
        return b2a_base64(self.d.digest())[:-2].translate(_to_websafe)


def dropbox_hash(contents):
    return DropboxHasher().digest(contents)


# URLs
nonce_url = 'https://client-lb.dropbox.com/cli_link_nonce_gen'
register_url = 'https://client.dropbox.com/register_host'
list_url = 'https://client-cf.dropbox.com/list'
fetch_url = 'https://block.dropbox.com/retrieve_batch'
commit_url = 'https://client-cf.dropbox.com/commit_batch'
store_url = 'https://block.dropbox.com/store_batch'

# headers
headers = {'Content-Type': 'application/x-www-form-urlencoded'}
headers["X-DBX-REQ-ID"] = uuid.uuid4().hex
headers["X-Dropbox-User-Agent"] = "DropboxDesktopClient/34.4.22 (Linux; 4.12.9-200.fc25.x86_64; x64; en_US)"
headers["User-Agent"] = "DropboxDesktopClient/34.4.22 (Linux; 4.12.9-200.fc25.x86_64; x64; en_US)"
headers["X-DBX-RETRY"] = "1"
headers["X-Dropbox-Locale"] = "en_US"


def make_unicode_broken(buf, encoding='utf-8', errors='strict'):
    if buf is None:
        return buf
    else:
        # if isinstance(buf, unicode):
        if isinstance(buf, str):
            return buf
        if isinstance(buf, bytes):
            return buf.decode(encoding if encoding else 'utf-8', errors)
        return buf


def make_bytes(buf, encoding='utf-8', errors='strict'):
    if isinstance(buf, bytes):
        return buf
    else:
        return buf.encode(encoding if encoding else 'utf-8', errors)


def make_str(buf, encoding='utf-8', errors='strict'):
    if PY3:
        return make_unicode_broken(buf, encoding, errors)
    else:
        return make_bytes(buf, encoding, errors)
