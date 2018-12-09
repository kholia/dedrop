Looking inside the (Drop) box
=============================

Security Analysis of Dropbox.

Web-based Presentation
======================

- http://www.openwall.com/presentations/WOOT13-Security-Analysis-of-Dropbox/

"Upstream" Resources
====================

- https://www.usenix.org/looking-inside-drop-box

  (includes video now!)

Reversing Dropbox
=================

0. Note: For handling modern (late 2018) Dropbox versions use "dedrop-ng" which
   is included in this repository.

1. Download Dropbox and extract it.

   ::

      $ cd ~

      $ export DROPBOX_VERSION="dropbox-lnx.x86_64-23.4.19"

      $ wget -c "https://www.dropbox.com/download?plat=lnx.x86_64" -O $DROPBOX_VERSION.tar.gz

      $ tar -xzf $DROPBOX_VERSION.tar.gz

2. Build "dedrop". Switch to this repository and do,

   ::

      $ cd src/dedrop

      $ make

      $ cp libdedrop.so ~

3. Use LD_PRELOAD and inject libdedrop.so into Dropbox.

   ::

      $ cd ~

      $ export BLOB_PATH=.dropbox-dist/$DROPBOX_VERSION/dropbox

      $ LD_PRELOAD=`pwd`/libdedrop.so .dropbox-dist/dropboxd

4. De-compile the "fixed" bytecode files.

   ::

      $ uncompyle6 pyc_decrypted/client_api/hashing.pyc
      ...

5. Study the soure-code, find bugs and make Dropbox better!

6. You might need to do ``xhost local:root`` to start Dropbox.

Dependencies (for paper)
========================

* texlive
* texlive-minted
* texlive-texments
* python-pygments

  ::

    yum install texlive texlive-minted python-pygments texlive-texments \
        texlive-ifplatform texlive-endnotes

Credits
=======

* ReflectiveDLLInjection is written by Stephen Fewer

  See https://github.com/stephenfewer/ReflectiveDLLInjection.git

* uncompyle2

  - https://github.com/wibiti/uncompyle2

  - https://github.com/Mysterie/uncompyle2

Resources
=========

* https://github.com/rocky/python-uncompyle6

* https://github.com/MyNameIsMeerkat/pyREtic

TODO
====

* Find alternatives to "tray_login" method since it is going to be patched
  soon. This is now redundant since Dropbox client now uses 2FA properly.

* "While your submission was interesting, there has been other research on
  similar topics. There is nothing wrong with talking about the same topic more
  than once, especially one that has a large impact but if you are expanding on
  a topic, make sure to highlight how you are taking the research to a new
  level. Be clear with the review board about how what you are doing is
  extending the research." <= (apply this feedback to the paper and
  presentation).

* Looking deeper into the (Drop) box.

  - dump bytecode from memory (revive pyREtic).
