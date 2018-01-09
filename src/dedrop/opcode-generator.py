#!/usr/bin/env python
# Copyright Hagen Fritsch, 2012, License: GPL-2.0

# automated opcode remapping utility
# Copyright Dhiru Kholia, 2013, License: GPL-2.0

import _marshal
import marshal
import dis

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
d = marshal.loads(open(f2).read()[8:])
fill(c, d)
codes_c = filter(lambda x: type(x) == type(c), c.co_consts)
codes_d = filter(lambda x: type(x) == type(c), d.co_consts)
for i, j in zip(codes_c, codes_d):
    fill(i, j)


def print_table(m):
    k = m.keys()
    k.sort()
    table = {}
    for i in k:
        # print "%c (%02x %s) =>" % (ord(i),ord(i),bin(ord(i))),
        for j, count in m[i].iteritems():
            if j == i:
                continue
            table[ord(i)] = ord(j)
            # print "\t%c (%02x %s) [%d]" % (ord(j),ord(j),bin(ord(j)),count),
            # print "%c (%02x %s) => %c (%02x %s)\t%d\t%s" % (ord(i),ord(i),bin(ord(i)),ord(j),ord(j),bin(ord(j)),ord(j)-ord(i),bin(ord(i)^ord(j)|0x100).replace('0', ' '))
    return table

print print_table(m)


# verify against known good opcode map

# known good opcode map
opcode_map = {
    0 : 0, 1 : 87, 2 : 66, 3 : 59, 4 : 25, 5 : 27, 6 : 55, 7 : 62, 8 : 57,
    9 : 71, 10 : 79, 11 : 75, 12 : 21, 13 : 4, 14 : 72, 15 : 1, 16 : 30,
    17 : 31, 18 : 32, 19 : 33, 20 : 70, 21 : 65, 22 : 63, 23 : 78, 24 : 77,
    25 : 13, 26 : 86, 27 : 58, 28 : 19, 29 : 56, 30 : 29, 31 : 60, 32 : 28,
    33 : 73, 34 : 15, 35 : 74, 36 : 20, 37 : 81, 38 : 12, 39 : 68, 40 : 80,
    41 : 22, 42 : 89, 43 : 26, 44 : 50, 45 : 51, 46 : 52, 47 : 53, 48 : 10,
    49 : 5, 50 : 64, 51 : 82, 52 : 23, 53 : 9, 54 : 11, 55 : 24, 56 : 84,
    57 : 67, 58 : 76, 59 : 2, 60 : 3, 61 : 40, 62 : 41, 63 : 42, 64 : 43,
    65 : 85, 66 : 83, 67 : 88, 68 : 255, 69 : 61, 70 : 54, 71 : 255, 72 : 255,
    73 : 255, 74 : 255, 75 : 255, 76 : 255, 77 : 255, 78 : 255, 79 : 255, 80 : 116,
    81 : 126, 82 : 100, 83 : 94, 84 : 120, 85 : 122, 86 : 132, 87 : 133, 88 : 105,
    89 : 101, 90 : 102, 91 : 93, 92 : 125, 93 : 255, 94 : 95, 95 : 134, 96 : 106,
    97 : 96, 98 : 108, 99 : 109, 100 : 255, 101 : 130, 102 : 124, 103 : 92, 104 : 91,
    105 : 90, 106 : 119, 107 : 135, 108 : 98, 109 : 136, 110 : 137, 111 : 107, 112 : 131,
    113 : 113, 114 : 99, 115 : 97, 116 : 121, 117 : 103, 118 : 104, 119 : 110, 120 : 111,
    121 : 115, 122 : 112, 123 : 114, 124 : 255, 125 : 255, 126 : 255, 127 : 255, 128 : 255,
    129 : 255, 130 : 255, 131 : 255, 132 : 255, 133 : 140, 134 : 141, 135 : 142, 136 : 143,
    137 : 255, 138 : 255, 139 : 255, 140 : 145, 141 : 146, 142 : 147
}


our_map = print_table(m)

# add known entries
our_map[0] = 0  # STOP_CODE

for k, v in opcode_map.items():
    ov = our_map.get(k, -1)
    if ov < 0:
        print("Missing entry for %s -> %s (%s)" % (k, v, dis.opname[v]))
        continue
    if v != ov:
        print("Mismatch for entry for (%s, %s) -> (%s, %s)" % (k, v, k, ov))
        continue
    # print("Found entry for %s -> %s (%s)" % (k, v, dis.opname[v]))

nkeys = 0
for k, v in opcode_map.items():
    if v != 255:
        nkeys = nkeys + 1
print("\nDiscovery ratio is %f%%" % ((len(our_map) * 100.0) / nkeys))
