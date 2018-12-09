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

volatile int magicSpellCasted;
unsigned int coCodeOffset;

typeof(PyMarshal_ReadLastObjectFromFile) *PyMarshal_ReadLastObjectFromFile_ = NULL;
typeof(Py_CompileStringExFlags) *Py_CompileStringExFlags_ = NULL;

/* FIXME: I'm now puzzled why I see an error about this one if I try to call it directly - somehow it doesn't resolve */
typeof(PyGILState_Ensure) *PyGILState_Ensure_ = NULL;
typeof(PyGILState_Release) *PyGILState_Release_ = NULL;
typeof(PyUnicode_FromString) * PyUnicode_FromString_ = NULL;

pthread_t magicThread;

#define GET_WORD_32_LE(n,b,i)                        \
{                                                    \
        (n) = ( (unsigned int) ((unsigned char*)b)[(i)    ]  )       \
            | ( (unsigned int) ((unsigned char*)b)[(i) + 1] << 8 )   \
            | ( (unsigned int) ((unsigned char*)b)[(i) + 2] << 16 )  \
            | ( (unsigned int) ((unsigned char*)b)[(i) + 3] << 24);  \
}

int findCoCodeOffset()
{
    PyObject *emptystring = PyBytes_FromString("");
    PyObject *code_str = PyBytes_FromString("dS");
    PyObject *nulltuple = PyTuple_New(0);
    PyObject *filename_ob = PyUnicode_FromString("AAABBBCCC");
    PyObject *funcname_ob = PyUnicode_FromString("AAABBBCCC");

    PyCodeObject* code_object = PyCode_New(0,  /* argcount */
        0,          /* kwonlyargcount */
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

        // printf("%02x: 0x%08x\n", i, probe);
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
    PyUnicode_FromString_ = dlsym(RTLD_DEFAULT, "PyUnicode_FromString");
    Py_CompileStringExFlags_ = dlsym(RTLD_DEFAULT, "Py_CompileString");

    // this is critical
    gstate = PyGILState_Ensure_();

    coCodeOffset = findCoCodeOffset();
    if (coCodeOffset == -1) {
        return NULL;
    }

    // execute setup code
    PyRun_SimpleString("import importlib; print(importlib._bootstrap_external._get_supported_file_loaders()); import dedrop; import sys; sys.path.append(''); print(sys.modules['dedrop']); import marshal3; print(marshal3.dumps('CHECK_MARSHAL_MODULE'))");
    char dirty[256];
    sprintf(dirty, "dedrop.init(%u)", coCodeOffset);
    PyRun_SimpleString(dirty);

    // this simple opcode-map-recovery trick works for some softwares ;)
    // char *payload = "import dis; print(dis.opmap)";
    // PyRun_SimpleString(payload);

    // main payload
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
