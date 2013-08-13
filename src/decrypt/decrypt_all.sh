#!/bin/bash
# vim: ts=4 expandtab

for i in `find ../pyc_orig/ -name "*pyc"`; do
    echo $i

    o=`echo $i | sed 's/\.\.\/pyc_orig/..\/pyc_decrypted/'`
    mkdir -p `dirname $o`
    bin/decrypt.exe $i $o
    [ $? -ne 0 ] && exit 1

done
