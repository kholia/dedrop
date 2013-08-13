#!/bin/bash
# vim: ts=4 expandtab

for i in `find pyc_decrypted/ -name "*.pyc"`; do
    echo $i

    o=`echo $i | sed 's/pyc_decrypted/py/'`
    o=`echo $o | sed 's/\.pyc/\.py/'`
	echo $o
    mkdir -p `dirname $o`
    echo python2 ~/uncompyle2/uncompyle2.py $i > $o
    python2 ~/uncompyle2/uncompyle2.py $i > $o

done
