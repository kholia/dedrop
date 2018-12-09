#### Dedrop-NG

A modern port of `dedrop` to reverse engineer modern Dropbox versions (e.g.
Dropbox 62.4.103).

#### Testing Notes

```
$ make; PYC_FILE=zipfile.pyc LD_PRELOAD=`pwd`/libdedrop.so .dropbox-dist/dropbox
woke up, doing magic...
Needle: 0x3bfdfa80
co_code offset found : 88
[(<class '_frozen_importlib_external.ExtensionFileLoader'>, ['.cpython-35m-x86_64-linux-gnu.so']), \
    (<class '_frozen_importlib_external.SourceFileLoader'>, []), \
    (<class '_frozen_importlib_external.SourcelessFileLoader'>, ['.pyc'])]
Initing coCodeOffset with 88
Hi, this is the payload 2!
3.5.4 (default, Nov  2 2018, 04:43:38)
[GCC 4.8.4]
...
    magic: 0x0a0d3427
[+] writing to output.pyc

$ uncompyle6 output.pyc
```

#### More Notes

Note the missing `.py` from `_frozen_importlib_external.SourceFileLoader` stuff. I guess this is preventing
the import of `.py` files.

Tip: `make regen-importlib  # grab changes to importlib` is useful.

Note: The `Makefile` is hardcoded to work on Ubuntu 18.04.1 LTS 64-bit.

Grab new version: `wget https://clientupdates.dropboxstatic.com/dbx-releng/client/dropbox-lnx.x86_64-62.4.103.tar.gz`

Grab old version: `wget https://clientupdates.dropboxstatic.com/dbx-releng/client/dropbox-lnx.x86_64-23.4.19.tar.gz`

Note: We borrow the `marshal` module from Python 3.5.4 tarball.


#### Resources

* https://stackoverflow.com/questions/47967298/compile-python-code-to-pycodeobject-and-marshal-to-pyc-file
  - Read `_code_to_bytecode` from `importlib/_bootstrap_external.py`.
  - Read code behind `marshal.dumps`.
