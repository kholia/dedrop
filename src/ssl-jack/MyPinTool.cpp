// OpenSSL snooper
//
// PIN_StartProgramProbed (probe mode) is broken in
// pin-2.13-62141-gcc.4.4.7-linux (Fedora 20)
//
// RTN_InsertCall(rtn, IPOINT_AFTER, ...) to hijack SSL_read does not work!
//
// "NOTE: IPOINT_AFTER is implemented by instrumenting each return instruction
// in a routine. Pin tries to find all return instructions, but success is not
// guaranteed" ;(
//
// Usage,
//
// ./pin -t source/tools/MyPinTool/obj-intel64/MyPinTool.so -- ~/.dropbox-dist/dropbox

#include "pin.H"
#include <iostream>
#include <fstream>
#include <openssl/ssl.h>

using namespace std;

std::ofstream TraceFile;

typedef typeof(SSL_write) *SSL_write_type;
typedef typeof(SSL_read) *SSL_read_type;

/////////////////////////////
// Replacement Routines START
/////////////////////////////

// int SSL_write(SSL *ssl, const void *buf, int num);
int New_SSL_write(SSL_write_type orgFuncptr, SSL * ssl, const void *buf, int num, ADDRINT returnIp)
{
	printf("\n<<< SSL_write with length %d >>>\n\n%s\n\n", num,
			(unsigned char*)buf);

	TraceFile << "<<< " << "SSL_write" << " of size " << num << " >>>" <<
		endl << endl << (unsigned char*)buf << endl << endl;

	int ret = orgFuncptr(ssl, buf, num);

	return ret;
}

// int SSL_read(SSL *ssl, void *buf, int num);
int New_SSL_read(SSL_read_type orgFuncptr, SSL * ssl, void *buf, int num, ADDRINT returnIp)
{
	int ret = orgFuncptr(ssl, buf, num);

	if (num < 8 || ret < 8) {
		printf("\n!!! SSL_read with length %d !!!\n\n%s\n", num,
				(unsigned char*)buf);
		return ret;
	}

	printf("\n<<< SSL_read with length %d >>>\n\n%s\n\n", num, (unsigned
				char*)buf);

	TraceFile << "<<< " << "SSL_read" << " of size " << num << " >>>" <<
		endl << endl << (unsigned char*)buf << endl << endl;

	return ret;
}

///////////////////////////
// Replacement Routines END
///////////////////////////


VOID ImageLoad(IMG img, VOID * v)
{
	RTN rtn = RTN_FindByName(img, "SSL_write");

	if (RTN_Valid(rtn)) {
		cout << "Replacing SSL_write in " << IMG_Name(img) << endl;

		// Define a function prototype that describes the application routine
		// that will be replaced.
		PROTO proto_SSL_write =
		    PROTO_Allocate(PIN_PARG(int), CALLINGSTD_DEFAULT,
		    "SSL_write", PIN_PARG(SSL *), PIN_PARG(const void *),
		    PIN_PARG(int), PIN_PARG_END());

		// Replace the application routine with the replacement function.
		// Additional arguments have been added to the replacement routine.
		RTN_ReplaceSignature(rtn, AFUNPTR(New_SSL_write),
		    IARG_PROTOTYPE, proto_SSL_write,
		    IARG_ORIG_FUNCPTR,
		    IARG_FUNCARG_ENTRYPOINT_VALUE, 0,
		    IARG_FUNCARG_ENTRYPOINT_VALUE, 1,
		    IARG_FUNCARG_ENTRYPOINT_VALUE, 2,
		    IARG_RETURN_IP, IARG_END);

		// Free the function prototype.
		PROTO_Free(proto_SSL_write);
	}

	RTN rrtn = RTN_FindByName(img, "SSL_read");

	if (RTN_Valid(rrtn)) {
		cout << "Replacing SSL_read in " << IMG_Name(img) << endl;

		// Define a function prototype that describes the application routine
		// that will be replaced.
		PROTO proto_SSL_read =
		    PROTO_Allocate(PIN_PARG(int), CALLINGSTD_DEFAULT,
		    "SSL_read", PIN_PARG(SSL *), PIN_PARG(void *),
		    PIN_PARG(int), PIN_PARG_END());

		// Replace the application routine with the replacement function.
		// Additional arguments have been added to the replacement routine.
		RTN_ReplaceSignature(rrtn, AFUNPTR(New_SSL_read),
		    IARG_PROTOTYPE, proto_SSL_read,
		    IARG_ORIG_FUNCPTR,
		    IARG_FUNCARG_ENTRYPOINT_VALUE, 0,
		    IARG_FUNCARG_ENTRYPOINT_VALUE, 1,
		    IARG_FUNCARG_ENTRYPOINT_VALUE, 2,
		    IARG_RETURN_IP, IARG_END);

		// Free the function prototype.
		PROTO_Free(proto_SSL_read);
	}
}

INT32 Usage()
{
	cerr << "Use the source, Luke! ;)" << endl;
	return -1;
}


VOID Fini(INT32 code, VOID *v)
{
	TraceFile.close();
}

int main(INT32 argc, CHAR * argv[])
{
	// Initialize symbol processing
	PIN_InitSymbols();

	// Initialize pin
	if (PIN_Init(argc, argv))
		return Usage();

	TraceFile.open("ssltrace.out");

	IMG_AddInstrumentFunction(ImageLoad, 0);
	PIN_AddFiniFunction(Fini, 0);

	PIN_StartProgram();  // JIT mode

	return 0;
}
