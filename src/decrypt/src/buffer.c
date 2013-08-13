/*
 * buffer.c
 */

#include <stdio.h>

#include "buffer.h"

void read_file(buffer_t* buf, const char* filename) {
	FILE* fin = fopen(filename, "rb");

	if (!fin) {
		printf("ERROR: failed to open input file!\n");
		exit(1);
	}

	if (fseek(fin, 0, SEEK_END)) {
		fclose(fin);
		printf("ERROR: fseek failed!\n");
		exit(1);
	}

	size_t size = ftell(fin);

	if (fseek(fin, 0, SEEK_SET)) {
		fclose(fin);
		printf("ERROR: fseek failed!\n");
		exit(1);
	}

	buf->data = malloc(size);
	buf->size = size;
	buf->i = 0;

	if (fread(buf->data, 1, size, fin) != size) {
		printf("ERROR: error reading input file!\n");
		exit(1);
	}

	fclose(fin);
}

void alloc_buffer(buffer_t* buf, size_t size) {
	buf->data = malloc(size);
	buf->size = size;
	buf->i = 0;
}

UINT8 get_uint8(buffer_t* b) {
	if (b->i >= b->size) {
		printf("get_uint8 underflow\n");
		exit(1);
	}
	UINT8 v = b->data[b->i];
	b->i++;
	return v;
}

UINT32 get_uint32(buffer_t* b) {
	if (b->i >= b->size) {
		printf("get_uint32 underflow\n");
		exit(1);
	}

	UINT32 v = *((UINT32*) &b->data[b->i]);
	b->i += sizeof(UINT32);
	return v;
}

void put_uint8(buffer_t* b, UINT8 v) {
	if (b->i >= b->size) {
		printf("put_uint8 overflow\n");
		exit(1);
	}

	b->data[b->i] = v;
	b->i++;
}

void put_uint32(buffer_t* b, UINT32 v) {
	if (b->i >= b->size) {
		printf("put_uint32 overflow\n");
		exit(1);
	}

	*((UINT32*) &b->data[b->i]) = v;
	b->i += sizeof(UINT32);
}

void copy_bytes(buffer_t* in, buffer_t* out, unsigned int count) {
	if (out->i + count > out->size) {
		printf("copy_bytes overflow\n");
		exit(1);
	}
	if (in->i + count > in->size) {
		printf("copy_bytes underflow\n");
		exit(1);
	}

	memcpy(&out->data[out->i], &in->data[in->i], count);
	in->i += count;
	out->i += count;
}
