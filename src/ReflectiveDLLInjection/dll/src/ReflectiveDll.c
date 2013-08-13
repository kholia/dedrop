//===============================================================================================//
// This is a stub for the actuall functionality of the DLL.
//===============================================================================================//
#include "ReflectiveLoader.h"
#include <stdio.h>

// Note: REFLECTIVEDLLINJECTION_VIA_LOADREMOTELIBRARYR and REFLECTIVEDLLINJECTION_CUSTOM_DLLMAIN are
// defined in the project properties (Properties->C++->Preprocessor) so as we can specify our own 
// DllMain and use the LoadRemoteLibraryR() API to inject this DLL.

// You can use this value as a pseudo hinstDLL value (defined and set via ReflectiveLoader.c)
extern HINSTANCE hAppInstance;
//===============================================================================================//

typedef
    enum {PyGILState_LOCKED, PyGILState_UNLOCKED}
        PyGILState_STATE;

typedef int (*Py_IsInitialized_)();
typedef PyGILState_STATE (*PyGILState_Ensure_)(void);
typedef void (*PyGILState_Release_)(PyGILState_STATE);
typedef int (*PyRun_SimpleString_)(const char*);

/* Values are for PYTHON27.DLL from Dropbox 1.7.5 */
Py_IsInitialized_ Py_IsInitialized = (Py_IsInitialized_)(void*)(0x1E113C60);
PyGILState_Ensure_ PyGILState_Ensure = (PyGILState_Ensure_)(void*)(0x1E107240);
PyGILState_Release_ PyGILState_Release = (PyGILState_Release_)(void*)(0x1E106F30);
PyRun_SimpleString_ PyRun_SimpleString = (PyRun_SimpleString_)(void*)(0x1E115A60);

PyGILState_STATE gstate;

#define N 102400

char buffer[N];

FILE *fp;

int count;

BOOL WINAPI DllMain( HINSTANCE hinstDLL, DWORD dwReason, LPVOID lpReserved )
{
    BOOL bReturnValue = TRUE;
    int value = Py_IsInitialized();
	switch( dwReason )
    {
		case DLL_QUERY_HMODULE:
#ifdef _MSC_VER
			if( lpReserved != NULL )
				*(HMODULE *)lpReserved = hAppInstance;
#endif
			break;
		case DLL_PROCESS_ATTACH:
#ifdef _MSC_VER
			hAppInstance = hinstDLL;
#endif
			//MessageBoxA( NULL, "Hello from DllMain!", "Reflective Dll Injection", MB_OK );
			gstate = PyGILState_Ensure();
			PyRun_SimpleString("from __future__ import absolute_import");
			PyRun_SimpleString("f = open('lol.txt', 'w'); f.write('hello'); f.close();");
			PyRun_SimpleString("import sys");
			PyRun_SimpleString("sys.path.append(\".\")");

			fp = fopen("payload.py", "r");
			if (fp) {
				count = fread(buffer, 1, N, fp);
				buffer[count] = 0;
				PyRun_SimpleString(buffer);
			}
			PyGILState_Release(gstate);
			break;
		case DLL_PROCESS_DETACH:
		case DLL_THREAD_ATTACH:
		case DLL_THREAD_DETACH:
            break;
    }
	return bReturnValue;
}
