import os
import tempfile
import zipfile
from copy import deepcopy
import dedrop
import time

# ---- start of borrowed PyPy code ----

"""Internal Python object serialization

This module contains functions that can read and write Python values in a binary format. The format is specific to Python, but independent of machine architecture issues (e.g., you can write a Python value to a file on a PC, transport the file to a Sun, and read it back there). Details of the format may change between Python versions.
"""

# NOTE: This module is used in the Python3 interpreter, but also by
# the "sandboxed" process.  It must work for Python2 as well.

import types
from _codecs import utf_8_decode, utf_8_encode

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

class _Marshaller:

    dispatch = {}

    def __init__(self, writefunc):
        self._write = writefunc

    def dump(self, x):
        try:
            self.dispatch[type(x)](self, x)
        except KeyError:
            for tp in type(x).mro():
                func = self.dispatch.get(tp)
                if func:
                    break
            else:
                raise ValueError("unmarshallable object")
            func(self, x)

    def w_long64(self, x):
        self.w_long(x)
        self.w_long(x>>32)

    def w_long(self, x):
        a = chr(x & 0xff)
        x >>= 8
        b = chr(x & 0xff)
        x >>= 8
        c = chr(x & 0xff)
        x >>= 8
        d = chr(x & 0xff)
        self._write(a + b + c + d)

    def w_short(self, x):
        self._write(chr((x)     & 0xff))
        self._write(chr((x>> 8) & 0xff))

    def dump_none(self, x):
        self._write(TYPE_NONE)
    dispatch[type(None)] = dump_none

    def dump_bool(self, x):
        if x:
            self._write(TYPE_TRUE)
        else:
            self._write(TYPE_FALSE)
    dispatch[bool] = dump_bool

    def dump_stopiter(self, x):
        if x is not StopIteration:
            raise ValueError("unmarshallable object")
        self._write(TYPE_STOPITER)
    dispatch[type(StopIteration)] = dump_stopiter

    def dump_ellipsis(self, x):
        self._write(TYPE_ELLIPSIS)

    try:
        dispatch[type(Ellipsis)] = dump_ellipsis
    except NameError:
        pass

    # In Python3, this function is not used; see dump_long() below.
    def dump_int(self, x):
        y = x>>31
        if y and y != -1:
            self._write(TYPE_INT64)
            self.w_long64(x)
        else:
            self._write(TYPE_INT)
            self.w_long(x)
    dispatch[int] = dump_int

    def dump_long(self, x):
        self._write(TYPE_LONG)
        sign = 1
        if x < 0:
            sign = -1
            x = -x
        digits = []
        while x:
            digits.append(x & 0x7FFF)
            x = x>>15
        self.w_long(len(digits) * sign)
        for d in digits:
            self.w_short(d)
    try:
        long
    except NameError:
        dispatch[int] = dump_long
    else:
        dispatch[long] = dump_long

    def dump_float(self, x):
        write = self._write
        write(TYPE_FLOAT)
        s = repr(x)
        write(chr(len(s)))
        write(s)
    dispatch[float] = dump_float

    def dump_complex(self, x):
        write = self._write
        write(TYPE_COMPLEX)
        s = repr(x.real)
        write(chr(len(s)))
        write(s)
        s = repr(x.imag)
        write(chr(len(s)))
        write(s)
    try:
        dispatch[complex] = dump_complex
    except NameError:
        pass

    def dump_string(self, x):
        # XXX we can't check for interned strings, yet,
        # so we (for now) never create TYPE_INTERNED or TYPE_STRINGREF
        self._write(TYPE_STRING)
        self.w_long(len(x))
        self._write(x)
    dispatch[bytes] = dump_string

    def dump_unicode(self, x):
        self._write(TYPE_UNICODE)
        #s = x.encode('utf8')
        s, len_s = utf_8_encode(x)

        # FIXME: Bug in PyPy?
        #self.w_long(len_s)
        self.w_long(len(s))
        self._write(s)
    try:
        unicode
    except NameError:
        dispatch[str] = dump_unicode
    else:
        dispatch[unicode] = dump_unicode

    def dump_tuple(self, x):
        self._write(TYPE_TUPLE)
        self.w_long(len(x))
        for item in x:
            self.dump(item)
    dispatch[tuple] = dump_tuple

    def dump_list(self, x):
        self._write(TYPE_LIST)
        self.w_long(len(x))
        for item in x:
            self.dump(item)
    dispatch[list] = dump_list

    def dump_dict(self, x):
        self._write(TYPE_DICT)
        for key, value in x.items():
            self.dump(key)
            self.dump(value)
        self._write(TYPE_NULL)
    dispatch[dict] = dump_dict

    def dump_code(self, x):
        self._write(TYPE_CODE)
        self.w_long(x.co_argcount)
        self.w_long(x.co_nlocals)
        self.w_long(x.co_stacksize)
        self.w_long(x.co_flags)
        self.dump(x.co_code)
        self.dump(x.co_consts)
        self.dump(x.co_names)
        self.dump(x.co_varnames)
        self.dump(x.co_freevars)
        self.dump(x.co_cellvars)
        self.dump(x.co_filename)
        self.dump(x.co_name)
        self.w_long(x.co_firstlineno)
        self.dump(x.co_lnotab)
    try:
        dispatch[types.CodeType] = dump_code
    except NameError:
        pass

    def dump_set(self, x):
        self._write(TYPE_SET)
        self.w_long(len(x))
        for each in x:
            self.dump(each)
    try:
        dispatch[set] = dump_set
    except NameError:
        pass

    def dump_frozenset(self, x):
        self._write(TYPE_FROZENSET)
        self.w_long(len(x))
        for each in x:
            self.dump(each)
    try:
        dispatch[frozenset] = dump_frozenset
    except NameError:
        pass

# ---- end of PyPy code ----

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
    137 : 255, 138 : 255, 139 : 255, 140 : 145, 141 : 146, 142 : 147}


"""
opcode_map = {
    0: 79, 1: 78, 2: 77, 3: 76, 4: 75, 5: 74, 6: 73, 7: 72, 8: 71, 9: 70, 10:
    80, 11: 81, 12: 82, 13: 83, 14: 84, 15: 85, 16: 86, 17: 87, 18: 88, 19: 89,
    20: 30, 21: 31, 22: 32, 23: 33, 30: 40, 31: 41, 32: 42, 33: 43, 40: 50, 41:
    51, 42: 52, 43: 53, 44: 54, 45: 55, 46: 56, 47: 57, 48: 58, 49: 59, 50: 60,
    51: 61, 52: 62, 53: 63, 54: 64, 55: 65, 56: 66, 57: 67, 58: 68, 60: 0, 61:
    1, 62: 2, 63: 3, 64: 4, 65: 5, 69: 9, 70: 29, 71: 28, 72: 27, 73: 26, 74:
    25, 75: 24, 76: 23, 77: 22, 78: 21, 79: 20, 80: 10, 81: 11, 82: 12, 83: 13,
    85: 15, 89: 19, 90: 100, 91: 101, 92: 102, 93: 103, 94: 104, 95: 105, 96:
    106, 97: 107, 98: 108, 99: 109, 100: 90, 101: 91, 102: 92, 103: 93, 104: 94,
    105: 95, 106: 96, 107: 97, 108: 98, 109: 99, 110: 130, 111: 131, 112: 132,
    113: 133, 114: 134, 115: 135, 116: 136, 117: 137, 120: 140, 121: 141, 122:
    142, 123: 143, 130: 110, 131: 111, 132: 112, 133: 113, 134: 114, 135: 115,
    136: 116, 139: 119, 140: 120, 141: 121, 142: 122, 144: 124, 145: 125, 146:
    126, 159: 145, 160: 146, 161: 147
}

# for druva-insync-client-5.9-51251.x86_64.rpm
"""

def remap_opcodes(code):
    code = bytearray(code)
    i = 0
    while i < len(code):
        op = code[i]
        new_code = opcode_map.get(op)
        code[i] = new_code
        i += (new_code >= 90 and 3 or 1) #opcode.HAVE_ARGUMENT:
    return str(code)

def dump_code(self, x):
    co_code = remap_opcodes(dedrop.bytecode(x))

    self._write(TYPE_CODE)
    self.w_long(x.co_argcount)
    self.w_long(x.co_nlocals)
    self.w_long(x.co_stacksize)
    self.w_long(x.co_flags)
    self.dump(co_code)
    self.dump(x.co_consts)
    self.dump(x.co_names)
    self.dump(x.co_varnames)
    self.dump(x.co_freevars)
    self.dump(x.co_cellvars)
    self.dump(x.co_filename)
    self.dump(x.co_name)
    self.w_long(x.co_firstlineno)
    self.dump(x.co_lnotab)

def dump_ecode(self, x):
    """dump encrypted bytecode"""

    co_code = dedrop.bytecode(x)

    self._write(TYPE_CODE)
    self.w_long(x.co_argcount)
    self.w_long(x.co_nlocals)
    self.w_long(x.co_stacksize)
    self.w_long(x.co_flags)
    self.dump(co_code)
    self.dump(x.co_consts)
    self.dump(x.co_names)
    self.dump(x.co_varnames)
    self.dump(x.co_freevars)
    self.dump(x.co_cellvars)
    self.dump(x.co_filename)
    self.dump(x.co_name)
    self.w_long(x.co_firstlineno)
    self.dump(x.co_lnotab)


_Marshaller.dispatch[types.CodeType] = dump_code

print "Hi, this is the payload 2!"
import sys
print sys.version

py_file = os.environ.get('OPALL')

def dump_encrypted_pyc(py_file):
    pyc_code = dedrop.load(py_file)
    out = "eopall.pyc"
    print "[+] writing to", out
    with open(out, "w") as f:
        f.write('\x03\xf3\r\n')
        # We don't care about a timestamp
        f.write('\x00\x00\x00\x00')
        _Marshaller.dispatch[types.CodeType] = dump_ecode
        _Marshaller(f.write).dump(pyc_code)

if py_file:
    print "dumping encrypted bytecode ;)"
    dump_encrypted_pyc(py_file)

pyc_file = os.environ.get('PYC_FILE')

def decrypt_pyc(pyc_file, new_pyc_file=None):
    pyc_code = dedrop.decrypt(pyc_file)
    if not new_pyc_file:
        new_pyc_file = pyc_file.replace(".pyc", ".npyc")
    print "[+] writing to", new_pyc_file
    with open(new_pyc_file, "w") as f:
        f.write('\x03\xf3\r\n')
        # We don't care about a timestamp
        f.write('\x00\x00\x00\x00')
        _Marshaller(f.write).dump(pyc_code)

if pyc_file:
    decrypt_pyc(pyc_file)

pyc_path = os.environ.get('PYC_PATH')

if pyc_path:
    if not os.path.isdir(pyc_path):
        print "PYC_PATH is not a directory!"
    else:
        pyc_path = os.path.abspath(pyc_path)
        base_path = os.path.dirname(pyc_path)
        decrypted_path = os.path.join(base_path, "pyc_decrypted")
        for path, dirs, files in os.walk(pyc_path):
            for filename in [os.path.abspath(os.path.join(path, fname)) for fname in files]:
                new_filename = filename.replace(pyc_path, decrypted_path)
                current_base_path = os.path.dirname(new_filename)
                try:
                    os.makedirs(current_base_path)
                except Exception, e:
                    print str(e)
                decrypt_pyc(filename, new_filename)

blob_path = os.environ.get('BLOB_PATH')

if blob_path:
    if not os.path.isfile(blob_path):
        print "BLOB_PATH is not a file!"
    else:
        blob_path = os.path.abspath(blob_path)
        mode = "r"

        print "\n:) :) :) Having Fun Yet?\n\n"
        time.sleep(2)

        f = zipfile.PyZipFile(blob_path, mode, zipfile.ZIP_DEFLATED)
        # base_path = os.path.dirname(blob_path)
        base_path = os.getcwd()
        base_decrypted_path = os.path.join(base_path, "pyc_decrypted")
        for filename in f.namelist():
            new_filename = os.path.join(base_decrypted_path, filename)
            current_base_path = os.path.dirname(new_filename)
            try:
                os.makedirs(current_base_path)
            except Exception, e:
                # print str(e)
                pass
            fh = tempfile.NamedTemporaryFile(delete=False)
            data = f.open(filename, "r").read()
            fh.write(data)
            tname= fh.name
            fh.close()
            decrypt_pyc(tname, new_filename)
            try:
                os.remove(tname)
            except Exception, e:
                print str(e)

        print "\n:) :) :) w00t! \n\n"
