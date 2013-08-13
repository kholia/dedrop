#!/usr/bin/env python
# Copyright Hagen Fritsch, 2012, License: GPL-2.0

# automated opcode remapping utility
# Copyright Dhiru Kholia, 2013, License: GPL-2.0

import _marshal
import marshal

encrypted_pyc = "eopall.pyc"
name = encrypted_pyc
normal_pyc = "all.pyc"
f2 = normal_pyc

m = {}
v = {}

def fill(c, d):
    if len(c.co_code) != len(d.co_code):
        print "len mismatch", c, d
        return
    for i, j in zip(c.co_code, d.co_code):
        # if i in m and not m[i] == j:
        #    print "mismatch %c (%x) => %c (%x)" % (ord(i),ord(i),ord(j),ord(j))
        v = m.setdefault(i, {})
        v[j] = v.get(j, 0) + 1

c = _marshal.loads(open(name).read()[8:])
d =  marshal.loads(open(f2).read()[8:])
fill(c, d)
codes_c = filter(lambda x: type(x) == type(c), c.co_consts)
codes_d = filter(lambda x: type(x) == type(c), d.co_consts)
for i,j in zip(codes_c, codes_d):
    fill(i,j)

def print_table(m):
    k = m.keys()
    k.sort()
    table = {}
    for i in k:
        # print "%c (%02x %s) =>" % (ord(i),ord(i),bin(ord(i))),
        for j,count in m[i].iteritems():
            if j == i: continue
            table[ord(i)] = ord(j)
            # print "\t%c (%02x %s) [%d]" % (ord(j),ord(j),bin(ord(j)),count),
            # print "%c (%02x %s) => %c (%02x %s)\t%d\t%s" % (ord(i),ord(i),bin(ord(i)),ord(j),ord(j),bin(ord(j)),ord(j)-ord(i),bin(ord(i)^ord(j)|0x100).replace('0', ' '))
    return table

print print_table(m)
