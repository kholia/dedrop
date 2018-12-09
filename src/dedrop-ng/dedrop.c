// vim: ts=4 expandtab
//
// https://wiki.python.org/moin/PortingExtensionModulesToPy3k

#include <Python.h>
#include <marshal.h>
#include <pythonrun.h>

#include <stdio.h>
#include <dlfcn.h>
#include <stdio.h>
#include <pthread.h>

extern unsigned char _binary_payload_py_start;
extern unsigned char _binary_payload_py_end;
extern unsigned char _binary_payload_py_size;

unsigned int coCodeOffset;

#define MAX_PAYLOAD (65536)

#define FIELD(base, offset, ftype) (*(ftype*)(((unsigned char*)base) + offset))

#define GET_WORD_32_LE(n,b,i)                        \
{                                                    \
        (n) = ( (unsigned int) ((unsigned char*)b)[(i)    ]  )       \
            | ( (unsigned int) ((unsigned char*)b)[(i) + 1] << 8 )   \
            | ( (unsigned int) ((unsigned char*)b)[(i) + 2] << 16 )  \
            | ( (unsigned int) ((unsigned char*)b)[(i) + 3] << 24);  \
}

/**
 * This function loads a given encrypted .pyc file and returns decrypted code object.
 */
static PyObject *dedrop_decrypt(PyObject *dummy, PyObject *args)
{
    const char *path;

    if (!PyArg_ParseTuple(args, "s", &path))
        return NULL;

    long magic;
    // printf("%s ->\n", path);
    FILE *f = fopen(path, "rb");
    if (!f) {
        printf("    failed to open, errno=%d\n", errno);
        return NULL;
    }

    /* TODO: verify magic number */
    // magic = PyMarshal_ReadLongFromFile(f);
    magic = PyMarshal_ReadLongFromFile(f);
    printf("    magic: 0x%08lx\n", magic);

    /* Skip .py modification timestamp */
    (void) PyMarshal_ReadLongFromFile(f);

    /* NOTE: Skip "size parameter" added in Python 3.3 */
    (void) PyMarshal_ReadLongFromFile(f);

    /* Here we call function from dropbox binary, yeah! */
    PyObject *obj = PyMarshal_ReadLastObjectFromFile(f);

    fclose(f);

    /* Ownership is passed to the caller, right? */
    return obj;
}

static PyObject *dedrop_init(PyObject *dummy, PyObject *args)
{
    if (!PyArg_ParseTuple(args, "I", &coCodeOffset))
        return NULL;

    printf("Initing coCodeOffset with %d\n", coCodeOffset);

    return Py_BuildValue("");
}

static PyObject *dedrop_load(PyObject *dummy, PyObject *args)
{
    const char *path;
    int unused __attribute__((unused));

    unsigned char buffer[81920] = { 0 };

    if (!PyArg_ParseTuple(args, "s", &path))
        return NULL;

    printf("%s ->\n", path);
    FILE *f = fopen(path, "rb");
    if (!f) {
        printf("    failed to open, errno=%d\n", errno);
        return NULL;
    }
    unused = fread(buffer, 81920, 1, f);
    PyObject *obj = Py_CompileStringExFlags((char*)buffer, "dummy", Py_file_input, NULL, -1);

    fclose(f);

    /* Ownership is passed to the caller, right? */
    return obj;
}

static PyObject *dedrop_bytecode(PyObject *dummy, PyObject *args)
{
    PyCodeObject *code = NULL;

    // FIXME: PyCode_Type not available?
    //if (!PyArg_ParseTuple(args, "O!:bytecode", &PyCode_Type, &code))

    if (!PyArg_ParseTuple(args, "O:bytecode", &code))
        return NULL;

    if (code) {
        // Dropbox has different layout of PyCodeObject? - Yep! (Dhiru, 2018-12)
        // code->co_code gives a tuple co_consts
        // PyObject* co_code = code->co_code;
        PyObject *co_code = FIELD(code, coCodeOffset, PyObject *);

        Py_XINCREF(co_code);
        //printf("    co_code: 0x%08x\n", (unsigned int) co_code);
        return co_code;
    }

    return NULL;
}

static PyObject* hello_world(PyObject *self, PyObject *args)
{
    printf("Hello, world!\n");
    Py_RETURN_NONE;
}

static PyMethodDef dedropMethods[] = {
    {"init", dedrop_init, METH_VARARGS, "Initialize coCodeOffset."},
    {"decrypt", dedrop_decrypt, METH_VARARGS, "Load encrypted pyc file."},
    {"bytecode", dedrop_bytecode, METH_VARARGS, "Get co_code from code object."},
    {"hello_world", hello_world, METH_NOARGS, "Print 'hello world' from a method defined in a C extension."},
    {"load", dedrop_load, METH_VARARGS, "Import a normal .py file."},
    {NULL, NULL, 0, NULL}   /* Sentinel */
};

// https://docs.python.org/3/howto/cporting.html
static struct PyModuleDef dedrop_definition = {
        PyModuleDef_HEAD_INIT,
        "dedrop", /* name of module */
        "A Python module that prints 'hello world' from C code.",
        -1,
        dedropMethods
};

PyMODINIT_FUNC PyInit_dedrop(void)
{
    Py_Initialize();
    return PyModule_Create(&dedrop_definition);
}
