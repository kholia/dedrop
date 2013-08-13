Looking inside the (Drop) box
=============================

Security Analysis of Dropbox.

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

*

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
