#!/usr/bin/python

import types
import sys
from _codecs import utf_8_decode, utf_8_encode

class _NULL:
    pass

class Unmarshaller(object):
    """
    This is a python unmarshaller borrowed from PyPy, modified in order to dump the loaded structure.
    """

    TYPE_NULL     = '0'
    TYPE_NONE     = 'N'
    TYPE_FALSE    = 'F'
    TYPE_TRUE     = 'T'
    TYPE_STOPITER = 'S'
    TYPE_ELLIPSIS = '.'
    TYPE_INT      = 'i'
    TYPE_INT64    = 'I'
    TYPE_FLOAT    = 'f'
    TYPE_COMPLEX  = 'x'
    TYPE_LONG     = 'l'
    TYPE_STRING   = 's'
    TYPE_INTERNED = 't'
    TYPE_STRINGREF= 'R'
    TYPE_TUPLE    = '('
    TYPE_LIST     = '['
    TYPE_DICT     = '{'
    TYPE_CODE     = 'c'
    TYPE_UNICODE  = 'u'
    TYPE_UNKNOWN  = '?'
    TYPE_SET      = '<'
    TYPE_FROZENSET= '>'

    dispatch = {}

    def __init__(self, f, l):
        def _counting_read(n):
            s = f.read(n)
            self._offset += n
            return s

        self._logger = l
        self._offset = 0
        self._read = _counting_read
        self._stringtable = []

    def load(self, level=0):
        self._logger.offset(self._offset)
        c = self._read(1)
        if not c:
            raise EOFError
        try:
            return self.dispatch[c](self, level)
        except KeyError:
            raise ValueError("bad marshal code: %c (%d)" % (c, ord(c)))

    def r_short(self):
        lo = ord(self._read(1))
        hi = ord(self._read(1))
        x = lo | (hi << 8)
        if x & 0x8000:
            x = x - 0x10000
        return x

    def r_long(self):
        s = self._read(4)
        a = ord(s[0])
        b = ord(s[1])
        c = ord(s[2])
        d = ord(s[3])
        x = a | (b << 8) | (c << 16) | (d << 24)
        if d & 0x80 and x > 0:
            x = -((1 << 32) - x)
            return int(x)
        else:
            return x

    def r_long64(self):
        a = ord(self._read(1))
        b = ord(self._read(1))
        c = ord(self._read(1))
        d = ord(self._read(1))
        e = ord(self._read(1))
        f = ord(self._read(1))
        g = ord(self._read(1))
        h = ord(self._read(1))
        x = a | (b << 8) | (c << 16) | (d << 24)
        x = x | (e << 32) | (f << 40) | (g << 48) | (h << 56)
        if h & 0x80 and x > 0:
            x = -((1 << 64) - x)
        return x

    def load_null(self, level):
        self._logger.null(level)
        return _NULL
    dispatch[TYPE_NULL] = load_null

    def load_none(self, level):
        self._logger.none(level)
        return None
    dispatch[TYPE_NONE] = load_none

    def load_true(self, level):
        self._logger.true(level)
        return True
    dispatch[TYPE_TRUE] = load_true

    def load_false(self, level):
        self._logger.false(level)
        return False
    dispatch[TYPE_FALSE] = load_false

    def load_stopiter(self, level):
        self._logger.stop_iteration(level)
        return StopIteration
    dispatch[TYPE_STOPITER] = load_stopiter

    def load_ellipsis(self, level):
        self._logger.ellipsis(level)
        return Ellipsis
    dispatch[TYPE_ELLIPSIS] = load_ellipsis

    def load_int(self, level):
        v = self.r_long()
        self._logger.int(level, v)
        return v
    dispatch[TYPE_INT] = load_int

    def load_int64(self, level):
        self._logger.int64(level)
        return self.r_long64()
    dispatch[TYPE_INT64] = load_int64

    def load_long(self, level):
        size = self.r_long()
        sign = 1
        if size < 0:
            sign = -1
            size = -size
        x = 0
        for i in range(size):
            d = self.r_short()
            x = x | (d << (i * 15))
        l = x * sign
        self._logger.long(level, l)
        return l
    dispatch[TYPE_LONG] = load_long

    def load_float(self, level):
        self._logger.float(level)
        n = ord(self._read(1))
        s = self._read(n)
        return float(s)
    dispatch[TYPE_FLOAT] = load_float

    def load_complex(self, level):
        self._logger.complex(level)
        n = ord(self._read(1))
        s = self._read(n)
        real = float(s)
        n = ord(self._read(1))
        s = self._read(n)
        imag = float(s)
        return complex(real, imag)
    dispatch[TYPE_COMPLEX] = load_complex

    def load_string(self, level):
        self._logger.string(level)
        n = self.r_long()
        s = self._read(n)
        self._logger.value(level, "'%s'" % s)
        return s
    dispatch[TYPE_STRING] = load_string

    def load_interned(self, level):
        self._logger.interned(level)
        n = self.r_long()
        ret = intern(self._read(n))
        self._stringtable.append(ret)
        return ret
    dispatch[TYPE_INTERNED] = load_interned

    def load_stringref(self, level):
        self._logger.stringref(level)
        n = self.r_long()
        return self._stringtable[n]
    dispatch[TYPE_STRINGREF] = load_stringref

    def load_unicode(self, level):
        """
        Unicode is stored as:
        - 4 bytes - n - number of UTF8 bytes to follow
        - n bytes - UTF8-encoded string
        """
        self._logger.unicode(level)
        self._logger.field(level, self._offset, 'n')
        n = self.r_long()
        self._logger.value(level, n)
        self._logger.field(level, self._offset, 's')
        s = self._read(n)
        self._logger.value(level, '%s' % s)
        #ret = s.decode('utf8')
        ret, len_ret = utf_8_decode(s)
        return ret
    dispatch[TYPE_UNICODE] = load_unicode

    def load_tuple(self, level):
        n = self.r_long()
        self._logger.tuple(level, n)
        list = [self.load(level + 1) for i in range(n)]
        return tuple(list)
    dispatch[TYPE_TUPLE] = load_tuple

    def load_list(self, level):
        n = self.r_long()
        self._logger.list(level, n)
        list = [self.load(level + 1) for i in range(n)]
        return list
    dispatch[TYPE_LIST] = load_list

    def load_dict(self, level):
        self._logger.dict(level)
        d = {}
        while 1:
            key = self.load(level + 1)
            if key is _NULL:
                break
            value = self.load(level + 1)
            d[key] = value
        return d
    dispatch[TYPE_DICT] = load_dict

    def load_code(self, level):
        self._logger.code(level)

        self._logger.field(level, self._offset, 'argcount')
        argcount = self.r_long()

        self._logger.field(level, self._offset, 'nlocals')
        nlocals = self.r_long()

        self._logger.field(level, self._offset, 'stacksize')
        stacksize = self.r_long()

        self._logger.field(level, self._offset, 'flags')
        flags = self.r_long()

        self._logger.field(level, self._offset, 'code')
        code = self.load(level + 1)

        self._logger.field(level, self._offset, 'consts')
        consts = self.load(level + 1)

        self._logger.field(level, self._offset, 'names')
        names = self.load(level + 1)

        self._logger.field(level, self._offset, 'varnames')
        varnames = self.load(level + 1)

        self._logger.field(level, self._offset, 'freevars')
        freevars = self.load(level + 1)

        self._logger.field(level, self._offset, 'cellvars')
        cellvars = self.load(level + 1)

        self._logger.field(level, self._offset, 'filename')
        filename = self.load(level + 1)

        self._logger.field(level, self._offset, 'name')
        name = self.load(level + 1)

        self._logger.field(level, self._offset, 'firstlineno')
        firstlineno = self.r_long()

        self._logger.field(level, self._offset, 'lnotab')
        lnotab = self.load(level + 1)
        return types.CodeType(argcount, nlocals, stacksize, flags, code, consts,
                              names, varnames, filename, name, firstlineno,
                              lnotab, freevars, cellvars)
    dispatch[TYPE_CODE] = load_code

    def load_set(self, level):
        self._logger.set(level)
        n = self.r_long()
        args = [self.load(level + 1) for i in range(n)]
        return set(args)
    dispatch[TYPE_SET] = load_set

    def load_frozenset(self, level):
        self._logger.frozenset(level)
        n = self.r_long()
        args = [self.load(level + 1) for i in range(n)]
        return frozenset(args)
    dispatch[TYPE_FROZENSET] = load_frozenset

class Logger(object):

    def __init__(self):
        self._b = ''

    def _print_indented(self, level, s):
        print self._b + ("  " * level) + s

    def offset(self, offset):
        """
        Sets the offset printed at the beginning of each line.
        """
        self._b = '0x%06x: ' % offset

    def field(self, level, offset, name):
        """
        Helper to print fields of complex objects (most notably 'code')
        """
        self.offset(offset)
        self._print_indented(level, ':%s ->' % name)

    def value(self, level, value):
        """
        For printing arbitrary values/comments
        """
        self._print_indented(level, ': %s' % str(value))

    def code(self, level):
        self._print_indented(level, 'Code')

    def string(self, level):
        self._print_indented(level, 'String')

    def unicode(self, level):
        self._print_indented(level, 'Unicode')

    def tuple(self, level, n):
        self._print_indented(level, 'Tuple %d' % n)

    def list(self, level, n):
        self._print_indented(level, 'List %d' % n)

    def int(self, level, value):
        self._print_indented(level, 'Int: %d' % value)

    def long(self, level, value):
        self._print_indented(level, 'Long: %d' % value)

    def none(self, level):
        self._print_indented(level, 'None')


if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        l = Logger()
        u = Unmarshaller(f, l)

        magic = u.r_long()
        print 'Magic: %s' % hex(magic)

        timestamp = u.r_long()
        print 'Timestamp: %d' % timestamp

        u.load()

