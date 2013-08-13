#!/usr/bin/env python

# from __future__ import division
#
# it is impossible to have BINARY_TRUE_DIVIDE and BINARY_DIVIDE opcodes to
# occur in a same bytecode file

# based on http://unpyc.sourceforge.net/Opcodes.html

def main():

  (lambda:1)()

  a = 1; b = 2
  (a, b) = (b, a)

  a = 1
  (a, a, a) = (a, a, a)

  {'a':1}

  x = range(6)
  x[2:4] += 'abc'

  a = 1
  a = +a

  a = 1
  a = -a

  a = 1
  a = not a

  a = 1
  a = `a`

  a = 1
  a = ~a

  a = [i*i for i in (1,2)]

  a = 2
  a = a ** 2

  a = 2
  a = a * 2

  a = 2
  a = a / 2

  a = 2
  a = a % 2

  a = 2
  a = a + 2

  a = 2
  a = a - 2

  a = [1]
  a[0]

  a = 2
  a = a // 2

  a = 2
  a = a / 2
  a = a // 2

  a = 1
  a //= 10.2

  a = 1
  a /= 2
  a //= 2
  b = 2
  a //= b
  a /= b

  a = [1,2,3]
  a = a[:]


  a = [1,2,3]
  a = a[1:]

  a = [1,2,3]
  a = a[:2]

  a = [1,2,3]
  a = a[1:2]

  a = [1,2,3]
  a[:] = [1,2,3]

  a = [1,2,3]
  a[1:] = [2,3]

  a = [1,2,3]
  a[:2] = [1,2]

  a = [1,2,3]
  a[1:2] = [2]

  a = [1,2,3]
  del a[:]

  a = [1,2,3]
  del a[1:]

  a = [1,2,3]
  del a[:2]


  a = [1,2,3]
  del a[1:2]

  a = 1
  a += 1

  a = 1
  a -= 1

  a = 1
  a *= 1

  a = 1
  a /= 1

  a = 1
  a %= 1

  a = []
  a[0] = 1

  a = [1]
  del a[0]

  a = 1
  a = a << 1

  a = 1
  a = a >> 1

  a = 1
  a = a & 1

  a = 1
  a = a ^ 1

  a = 1
  a = a | 1

  a = 1
  a **= 1

  for a in (1,2): pass

  print "hello world!"

  print

  def fv(a,b): pass
  av = (1,2)
  fv(*av)

  def fkv(a,b,c): pass
  akv = {"b":1,"c":2}
  b = (3,)
  fkv(*b, **akv)

  def fk(a,b): pass
  ak = {"a":1,"b":2}
  fk(**ak)


  import sys
  print >> sys.stdout, "hello world",

  import sys
  print >> sys.stdout
  del sys.api_version

  zzz = 89
  del zzz


  a = 1
  a <<= 1

  a = 1
  a >>= 1

  a = 1
  a &= 1

  a = 1
  a ^= 1

  a = 1
  a |= 1

  for a in (1,2): break

  with open("1.txt") as f:
    print f.read()

  class a: pass

  # empty file

  exec("print 'hello world'", globals(), locals())

  frozenset({1, 2, 3})

  for a in (1,2): break

  try:
    a = 1
  except ValueError:
    a = 2
  finally:
    a = 3

  class a: pass

  a = 1

  a = 1
  del a

  (a, b) = "ab"

  for i in (1,2): pass

  a = 0
  b = [0]
  b[a] += 1

  a = 1

  a = 1
  a = a

  a = 1;
  a = (a, a)

  [1,2,3]

  {"a":1,"b":2}

  [].sort()

  a = 1 == 2

  a = 2+3+4
  "@"*4
  a="abc" + "def"
  a = 3**4
  a = 13//4

  a //= 2

  import new

  from dis import opmap

  if 1 == 2: pass
  else: pass

  if 1 == 2: pass
  else: pass

  if not(1 == 2): pass
  else: pass

  for i in (1,2): pass

  for x in (1,2):
    try: continue
    except: pass

  while 0 > 1: pass

  try:
    a = 1
  except ValueError:
    a = 2
  finally:
    a = 3

  try:
    a = 1
  except ValueError:
    a = 2
  finally:
    a = 3

  raise ValueError

  a = [1,2,3,4]
  b = a[::-1]

  xyz = 0

  def lolcats():
    global xyz
    pass


def fc():
  a = 1
  def g():
    return a + 1
  return g()

print fc()


def f(): pass
f()


def f1():
  from sys import *
  a = 1
  a = a

def f2():
  a = 1
  a = a

def f3():
  a = 1
  del a


import sys
sys.stderr = sys.stdout

import sys
# del sys.stderr

l1 = 0
def lolx():
  global l1
  l1 = 1

l2 = 0
def loly():
  global l2
  del l2
  def f():
    a = 3
    b = 5
    def g():
      return a + b
  f()

  mylist = [1, 1, 1, 2, 2, 3]
  z ={x for x in mylist if mylist.count(x) >= 2}
  a = {x for x in 'abracadabra' if x not in 'abc'}
  set([20, 0])

lolx()
loly()

def foo():
        print 'hello'
        yield 1
        print 'world'
        yield 2

a = foo()
print a.next()
print a.next()

def myfunc(alist):
  return len(alist)
