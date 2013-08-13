
#include <windows.h>

#ifndef __BUFFER_H__
#define __BUFFER_H__

/* Structure describing input/output buffers */
typedef struct {
	UINT8* data;
	unsigned int i;
	unsigned int size;
} buffer_t;

void read_file(buffer_t* buf, const char* filename);
void alloc_buffer(buffer_t* buf, size_t size);

UINT8 get_uint8(buffer_t* b);
UINT32 get_uint32(buffer_t* b);

void put_uint8(buffer_t* b, UINT8 v);
void put_uint32(buffer_t* b, UINT32 v);

void copy_bytes(buffer_t* in, buffer_t* out, unsigned int count);

#endif
