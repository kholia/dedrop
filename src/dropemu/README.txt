HOWTO
-----

Note: The code is very rough at the moment.

0. Install Python 2.7.13. Then install the Requests module.

http://docs.python-requests.org/en/master/

> python -m pip install requests


1. Link this client (named dropemu) with the Dropbox account.

$> python register.py
Initializing Dropbox CLI client (dropemu) ...

Your host_id / host_key / host_secret is 379e0d12632f5331ab2b251c4f01404d.

Please visit https://www.dropbox.com/cli_link_nonce?nonce=1f44542f6317406aaf42afc149b9cc27 in a web browser to link this device.

This device is now linked with (379e0d12632f5331ab2b251c4f01404d) as the host_key.

The associated email address is lulu@mailinator.com.


2. Open the printed link in a web browser and link the client to your Dropbox account.


3. Use the dropemu client to list and download files.

> python dropemu.py 379e0d12632f5331ab2b251c4f01404d
Using host_Key = 379e0d12632f5331ab2b251c4f01404d ...
Fetching data ...

Refreshing Cache ...

(Cmd) ls
   ID  type       size path
    0     f       1268 /Getting Started.rtf
    1     d          0 /testing123
    2     d          0 /testing123/test-inner

(Cmd) get 0
Fetching /Getting Started.rtf (fBFc9XccaRNmhxZTnmDtU_Bu2LSXtHOy9seJWWQ9dw8) ...
Fetched Getting Started.rtf :-)
(Cmd)

(Cmd) put test.txt
Uploading 8sobtsfpB9Btr-Roflefznazfk6Tt2BQItpS5szCb9I ...
[["8sobtsfpB9Btr-Roflefznazfk6Tt2BQItpS5szCb9I", {"ret": "ok"}]]
{"chillout": 8.031287501158066e-08, "changeset_id": {}, "results": [330967181946127464], "need_blocks": []}

(Cmd) ls
   ID  type       size path
    0     f       1268 /Getting Started.rtf
    1     d          0 /testing123
    2     d          0 /testing123/test-inner
    3     f          5 /test.txt

(Cmd) rm 3
Removing 8sobtsfpB9Btr-Roflefznazfk6Tt2BQItpS5szCb9I ...
{"chillout": 8.031287501158066e-08, "changeset_id": {"3540072": 593318256}, "results": [330967340859917416], "need_blocks": []}
{"chillout": 1.1243802501621293e-07, "changeset_id": {}, "results": [330967340859917416], "need_blocks": []}
