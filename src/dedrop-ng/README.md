#### Dedrop-NG

A modern port of `dedrop` to reverse engineer modern Dropbox versions (e.g.
Dropbox 73.4.118 from 29-May-2019).


#### Setup

I am running Ubuntu 19.04 LTS 64-bit which has Python 3.7. On older Ubuntu
versions, install `Python 3.7.2` via `pyenv` (https://github.com/pyenv/pyenv-installer).

```
$ sudo apt install python3-dev python3-pip -y

$ pip3 install --user uncompyle6

$ pwd
...dedrop/src/dedrop-ng

$ wget https://clientupdates.dropboxstatic.com/dbx-releng/client/dropbox-lnx.x86_64-73.4.118.tar.gz

$ tar -xzf dropbox-lnx.x86_64-73.4.118.tar.gz

$ make
```


#### Testing Notes

```
$ make; PYC_FILE=zipfile.pyc LD_PRELOAD=`pwd`/libdedrop.so .dropbox-dist/dropboxd
...
woke up, doing magic...
Needle: 0x5413a990
co_code offset found : 88
[(<class '_frozen_importlib_external.ExtensionFileLoader'>, ['.cpython-37m-x86_64-linux-gnu.so']), (<class '_frozen_importlib_external.SourceFileLoader'>, []), (<class '_frozen_importlib_external.SourcelessFileLoader'>, ['.pyc'])]
<module 'dedrop' from 'dedrop/src/dedrop-ng/.dropbox-dist/dropbox-lnx.x86_64-73.4.118/dedrop.cpython-37m-x86_64-linux-gnu.so'>
Initing coCodeOffset with 88
Hi, this is the payload 2!
3.7.2 (default, May  6 2019, 16:31:02)
[GCC 4.8.4]
    magic: 0x0a0d3452
[+] writing to output.pyc
...
```


```
$ uncompyle6 output.pyc
...
# uncompyle6 version 3.3.3
# Python bytecode 3.7 (3394)
# Decompiled from: Python 3.7.3 (default, Apr  3 2019, 05:39:12)
# [GCC 8.3.0]
# Embedded file name: zipfile.pyc
import io, os, importlib.util, sys, time, stat, shutil, struct, binascii, threading
try:
...
```


#### More Notes

Note the missing `.py` from `_frozen_importlib_external.SourceFileLoader` stuff. I guess this is preventing
the import of `.py` files.

Tip: `make regen-importlib  # grab changes to importlib` is useful.

Note: The `Makefile` is hardcoded to work on Ubuntu 19.04 LTS 64-bit.

Note: We borrow the `marshal` module from Python 3.7.2 tarball.


#### Notes from 'lookinsidethebox' project

Enable Dropbox verbose logging:


```
$ eval `python3 setenv.py`
```

```
$ ./.dropbox-dist/dropboxd
dropbox: locating interpreter
dropbox: logging to /tmp/dropbox-antifreeze-VHHivn
dropbox: initializing
dropbox: initializing python 3.7.2
...
23:00:53.826 |3486 | [            ] RTRACE       : [client/message_queue.pyc:226] Registering on_quit handler: <bound method UserNotificationControllerAdapter.on_quit of <dropbox.client.notifications.notification_adapter.UserNotificationControllerAdapter object at 0x7fa578371940>>
23:00:53.826 |3486 | [            ] RTRACE       : [client/message_queue.pyc:226] Installing exit_tracing handlers
23:00:53.826 |3486 | [            ] RTRACE       : [client/message_queue.pyc:226] Posting 0 early messages ...
23:00:53.829 |3486 | [            ] MainThread   : [client/main.pyc:6667] Registering on_quit handler: <function start_trace_thread.<locals>.cleanup_traces at 0x7fa578337ae8>
23:00:53.857 |3486 | [            ] MainThread   : [exception/reporting.pyc:267] !! 1 instance(s) of exception (build=73.4.118, legacy_hash=f3ca50d0f3233dc931529b85ef2be5da, sync_engine=None):
23:00:53.871 |3486 | [            ] MainThread   : [exception/reporting.pyc:267] !! Traceback (most recent call last):
23:00:53.874 |3486 | [            ] MainThread   : [exception/reporting.pyc:267] !!   File "dropbox/client/high_trace.py", line 554, in track_magic
23:00:53.877 |3486 | [            ] MainThread   : [exception/reporting.pyc:267] !! BadAssumptionError: User is using time-limited cookie
23:00:53.880 |3486 | [            ] MainThread   : [exception/reporting.pyc:368] Sending unauthenticated exception to server
...
```


#### This stopped working?

* Start patching/enhancement work by diffing our `marshal.c` against the
  [latest upstream version](https://github.com/python/cpython/blob/master/Python/marshal.c).

* Decompile the `PyCode_CheckLineNumber` function (in `.dropbox-dist/dropbox-lnx.x86_64-xyz/dropbox`
  binary) to get to PyCodeObject structure.

* Search for `_POP_JUMP` in the same target binary to local the "VM opcode"
  handling function. Modify the `dump_switch_cases.py` script to target this
  function.

* Add more tricks here (using `dis` to see raw code).


#### Resources

* https://stackoverflow.com/questions/47967298/compile-python-code-to-pycodeobject-and-marshal-to-pyc-file
  - Read `_code_to_bytecode` from `importlib/_bootstrap_external.py`.
  - Read code behind `marshal.dumps`.
