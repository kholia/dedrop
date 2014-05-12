#!/usr/bin/env python

# The code is licensed under the MIT License

from ctypes import *
import marshal, struct, types, os, argparse

# Dedrop Opcode Map by Przemysław Węgrzyn
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

def remap_opcodes(code):
    code = bytearray(code)
    i = 0
    while i < len(code):
        op = code[i]
        new_code = opcode_map.get(op)
        code[i] = new_code
        i += (new_code >= 90 and 3 or 1) #opcode.HAVE_ARGUMENT:
    return str(code)
# --------------------------
# end code taken from dedrop


# Load fortified Dropbox Python27.dll
pythondll = CDLL("Python27_dropbox.dll")

# Set NoSiteFlag (as Dropbox's py2exe does it)
# and initialize the fortified interpeter
Py_NoSiteFlag = c_int.in_dll(pythondll, "Py_NoSiteFlag")
memset(addressof(Py_NoSiteFlag), 1, 1)
pythondll.Py_Initialize()

# Specify PyMarshal_ReadObjectFromString calling conventions
# https://docs.python.org/2/c-api/marshal.html
readObjectFromString = pythondll.PyMarshal_ReadObjectFromString
readObjectFromString.argtypes = [c_char_p, c_int]
readObjectFromString.restype = py_object

def get_memory_contents(obj):
    """
    Returns the memory contents of obj.
    """
    return string_at(
        id(obj), # CPython implementation: id(obj) == memory address
        obj.__sizeof__()
    )

def get_chunks(obj):
    """
    Returns the memory contents of obj in chunks of 4 bytes each.
    """
    d = get_memory_contents(obj)
    fmt = "<" + ("I" * (len(d)/4))
    return struct.unpack(fmt, d)

def get_referenced_addresses(obj):
    """
    Returns all addresses that are referenced by obj.
    As a simple heuristic, we assume that
    all chunks < 0xfffff are constants/flags, not references.
    """
    return filter(
        lambda x: x > 0xfffff,
        get_chunks(obj)
    )

def get_exposed_addresses(obj):
    return (
        id(getattr(obj, f))
        for f in dir(obj)  # dir(obj) returns a list of all available attributes
    )

def get_co_code_addr(obj):
    """
    Returns address of the co_code object of obj.
    """
    # Get all addresses referenced in memory
    all_addrs = set(get_referenced_addresses(obj))
    # Get addresses of all properties that are exposed at the Python layer
    public_addrs = set(get_exposed_addresses(obj))
    # co_code is the attribute that's referenced in memory, but not exposed.
    co_code_addr = all_addrs - public_addrs

    if len(co_code_addr) != 1:
        raise RuntimeError("Not exactly one unknown address: %s" % co_code_addr)
    return co_code_addr.pop()

def converted_copy(obj):
    """
    Using a PyObject created by a different interpreter is usually something
    that leads to a variety of great crashes.
    This function takes an object created by the Dropbox Interpreter
    and creates a clean copy using the unmodified interpreter.

    Additionally, in the case of code objects, the opcodes are remapped.
    """
    t = type(obj).__name__
    if t == "code":
        addr = get_co_code_addr(obj)
        co_code = cast(addr, py_object).value
        co_code = remap_opcodes("%s" % co_code)
        return types.CodeType(
            *(converted_copy(x) for x in (
                obj.co_argcount,
                obj.co_nlocals,
                obj.co_stacksize,
                obj.co_flags,
                co_code,
                obj.co_consts,
                obj.co_names,
                obj.co_varnames,
                obj.co_filename,
                obj.co_name,
                obj.co_firstlineno,
                obj.co_lnotab,
                obj.co_freevars,
                obj.co_cellvars))
        )
    if t == "str":
        return "%s" % obj
    if t == "NoneType":
        return None
    if t == "tuple":
        return tuple(converted_copy(x) for x in obj)
    if t in ["int", "float", "complex", "long", "unicode"]:
        return getattr(types, t.title()+"Type")("%s" % obj)
    raise RuntimeError("Unknown Element type: %s" % t)

MAGIC = "03F30D0AF0225753".decode("hex")
def decrypt_pyc(filename_encrypted, filename_decrypted):
    """
    Writes a decrypted copy of infile into outfile
    """
    with open(filename_encrypted, "rb") as f:
        c = f.read()[8:] # omit magic and timestamp

    decrypted_bytecode = readObjectFromString(c, len(c))
    code_obj = converted_copy(decrypted_bytecode)

    with open(filename_decrypted, "wb") as f:
        f.write(MAGIC)
        marshal.dump(code_obj, f)

def convert(filename):
    print "Convert %s" % filename

    filename_decrypted = filename.replace("bytecode_encrypted", "bytecode_decrypted")
    if not os.path.isdir(os.path.dirname(filename_decrypted)):
        os.makedirs(os.path.dirname(filename_decrypted))

    decrypt_pyc(filename, filename_decrypted)

if __name__ == '__main__':
        parser = argparse.ArgumentParser()
        parser.add_argument('files', metavar='FILE', type=str, nargs='*', help='files to decrypt')
        parser.add_argument('--all', action='store_true', help='decrypt all files')
        options = parser.parse_args()
        if options.all:
            for path, dirs, files in os.walk("bytecode_encrypted"):
                for filename in [os.path.join(path, fname) for fname in files]:
                    if filename.endswith(".pyc"):
                        convert(filename)
        elif options.files:
            for filename in options.files:
                convert(filename)
        else:
                parser.print_help()

pythondll.Py_Finalize()
