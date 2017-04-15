// vim: ts=4 expandtab

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

volatile int magicSpellCasted;
unsigned int coCodeOffset;

typeof(PyMarshal_ReadLastObjectFromFile) *PyMarshal_ReadLastObjectFromFile_ = NULL;
typeof(Py_CompileStringFlags) *Py_CompileStringFlags_ = NULL;

/* FIXME: I'm now puzzled why I see an error about this one if I try to call it directly - somehow it doesn't resolve */
typeof(PyGILState_Ensure) *PyGILState_Ensure_ = NULL;
typeof(PyGILState_Release) *PyGILState_Release_ = NULL;
typeof(PyString_FromString) * PyString_FromString_ = NULL;

pthread_t magicThread;

#define MAX_PAYLOAD (65536)

#define FIELD(base, offset, ftype) (*(ftype*)(((char*)base) + offset))

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
static PyObject *dedrop_decrypt(PyObject * dummy, PyObject * args)
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
    // printf("    magic: 0x%08lx\n", magic);

    /* Skip .py modification timestamp */
    (void) PyMarshal_ReadLongFromFile(f);

    /* Here we call function from dropbox binary, yeah! */
    PyObject *obj = PyMarshal_ReadLastObjectFromFile_(f);

    fclose(f);

    /* Ownership is passed to the caller, right? */
    return obj;
}

static PyObject *dedrop_load(PyObject * dummy, PyObject * args)
{
    const char *path;

    unsigned char buffer[81920] = { 0 };

    if (!PyArg_ParseTuple(args, "s", &path))
        return NULL;

    printf("%s ->\n", path);
    FILE *f = fopen(path, "rb");
    if (!f) {
        printf("    failed to open, errno=%d\n", errno);
        return NULL;
    }
    fread(buffer, 81920, 1, f);
    PyObject *obj = Py_CompileStringFlags_((char*)buffer, "dummy", Py_file_input, NULL);

    fclose(f);

    /* Ownership is passed to the caller, right? */
    return obj;
}

static PyObject *dedrop_bytecode(PyObject * dummy, PyObject * args)
{
    PyCodeObject *code = NULL;

    // FIXME: PyCode_Type not available?
    //if (!PyArg_ParseTuple(args, "O!:bytecode", &PyCode_Type, &code))

    if (!PyArg_ParseTuple(args, "O:bytecode", &code))
        return NULL;

    if (code) {

        // FIXME: different layout of PyCodeObject ??
        // code->co_code gives a tuple co_consts
        //PyObject* co_code = code->co_code;
        PyObject *co_code = FIELD(code, coCodeOffset, PyObject *);

        Py_XINCREF(co_code);
        //printf("    co_code: 0x%08x\n", (unsigned int) co_code);
        return co_code;
    }

    return NULL;
}

static PyMethodDef dedropMethods[] = {
    {"decrypt", dedrop_decrypt, METH_VARARGS, "Load encrypted pyc file."},
    {"bytecode", dedrop_bytecode, METH_VARARGS,
            "Get co_code from code object."},
    {"load", dedrop_load, METH_VARARGS, "Import a normal .py file."},
    {NULL, NULL, 0, NULL}   /* Sentinel */
};

int findCoCodeOffset()
{
    PyObject *emptystring = PyString_FromString("");
    PyObject *code_str = PyString_FromString("dS");
    PyObject *nulltuple = PyTuple_New(0);
    PyObject *filename_ob = PyString_FromString("");
    PyObject *funcname_ob = PyString_FromString("");

    PyCodeObject* code_object = PyCode_New(0,  /* argcount */
        0,          /* nlocals */
        1,          /* stacksize */
        67,         /* flags */
        code_str,       /* code */
        nulltuple,      /* consts */
        nulltuple,      /* names */
        nulltuple,      /* varnames */
        nulltuple,      /* freevars */
        nulltuple,      /* cellvars */
        filename_ob,    /* filename */
        funcname_ob,    /* name */
        3,              /* firstlineno */
        emptystring     /* lnotab */
        );

    unsigned int i;
    unsigned int probe;
    unsigned int needle = (unsigned long int)code_str;

    printf ("Needle: 0x%08x\n", needle);
    for (i = 0; i < sizeof(PyCodeObject); i+=4) {
        GET_WORD_32_LE(probe, code_object, i);

        printf("%02x: 0x%08x\n", i, probe);
        if (probe == needle) {
            printf("co_code offset found : %d\n", i);
            return i;
        }
    }

    printf("unable to find co_code offset!\n");
    return -1;
}

void *thread()
{
    PyGILState_STATE gstate;
    int ret;

    while((ret = sleep(4))) {
            puts(".");
    }

    printf("woke up, doing magic...\n");

    PyMarshal_ReadLastObjectFromFile_ =
        dlsym(RTLD_DEFAULT, "PyMarshal_ReadLastObjectFromFile");
    PyGILState_Ensure_ = dlsym(RTLD_DEFAULT, "PyGILState_Ensure");
    PyGILState_Release_ = dlsym(RTLD_DEFAULT, "PyGILState_Release");
    PyString_FromString_ = dlsym(RTLD_DEFAULT, "PyString_FromString");
    Py_CompileStringFlags_ = dlsym(RTLD_DEFAULT, "Py_CompileString");

#if 0
    printf("0x%08x\n", PyMarshal_ReadLastObjectFromFile_);
    printf("0x%08x\n", PyGILState_Ensure_);
    printf("0x%08x\n", PyGILState_Release_);
#endif

    gstate = PyGILState_Ensure_();

    coCodeOffset = findCoCodeOffset();
    if (coCodeOffset == -1) {
        return NULL;
    }

    (void) Py_InitModule("dedrop", dedropMethods);

    // this simple opcode-map-recovery trick works for some softwares ;)
    // char *payload = "import dis; print dis; print dis.opmap";
    // PyRun_SimpleString(payload);

    unsigned char *pblob = &_binary_payload_py_start;
    PyRun_SimpleString((char*)pblob);

    PyGILState_Release_(gstate);
    return NULL;
}

size_t strlen(const char *s)
{
    size_t l = 0;

    if (!magicSpellCasted) {
        magicSpellCasted = 1;
        pthread_create(&magicThread, NULL, thread, (void *) "");
    }

    while (*s++)
        l++;

    return l;
}
