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

1. Download Dropbox and "install" it.

   ::

      $ cd ~

      $ wget https://dl-web.dropbox.com/u/17/dropbox-lnx.x86_64-2.7.30.tar.gz

      $ tar -xzf dropbox-lnx.x86_64-2.7.30.tar.gz

2. Build "dedrop". Switch to this repository and do,

   ::

      $ cd src/dedrop

      $ make

      $ cp libdedrop.so ~

3. Use LD_PRELOAD and inject libdedrop.so into Dropbox.

   ::

      $ cd ~

      $ export BLOB_PATH=.dropbox-dist/dropbox

      $ LD_PRELOAD=`pwd`/libdedrop.so .dropbox-dist/dropbox

4. De-compile the "fixed" bytecode files.

   ::

      $ uncompyle2 pyc_decrypted/client_api/hashing.pyc
      ...

5. Study the soure-code, find bugs and make Dropbox better!


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

TODO
====

* Find alternatives to "tray_login" method since it is going to be patched
  soon.

* "While your submission was interesting, there has been other research on
  similar topics. There is nothing wrong with talking about the same topic more
  than once, especially one that has a large impact but if you are expanding on
  a topic, make sure to highlight how you are taking the research to a new
  level. Be clear with the review board about how what you are doing is
  extending the research." <= (apply this feedback to the paper and
  presentation).

* Looking deeper into the (Drop) box.

  - dump bytecode from memory (revive pyREtic).
