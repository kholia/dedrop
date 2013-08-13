/*
 * dbdecrypt.c
 */
#include <windows.h>
#include <stdio.h>

#include "opcode_map.h"
#include "buffer.h"
#include "marshal_types.h"

#define	PYTHON_DLL				"../dll/Python27.dll"
#define DECRYPT_FCALL_OFFSET	(0x1E1021B0 - 0x1E000000)

#define PYC_MAGIC_DBOX			0x0A0DF307
#define PYC_MAGIC_27			0x0A0DF303

#define MAX_INTERNED_STRINGS	(16384)

static const BYTE decryptCheckBytes[] = { 0x81, 0xEC, 0xE0, 0x09, 0x00, 0x00,
		0x8B, 0xC2, 0x69, 0xC9, 0xCD, 0x0D, 0x01, 0x00 };

typedef void (__cdecl* DecryptFunc_t)(UINT32 rounded_size);

/** Total count of interned strings */
unsigned int interned_count;

/**
 * Mapping of interned string IDs. In the modified python, each code object creates new strings list,
 * strarting indexing from 0. Unmodified python has a common index space for the whole file. The instance
 * of interned_strings_map_t is created for each new code object and stores current level's mapping from
 * DropBox IDs to normal python IDs.
 */
typedef struct {
	unsigned int count;
	unsigned int id[MAX_INTERNED_STRINGS];
} interned_strings_map_t;

/**
 * Decrypts the code buffer in place.
 */
void decrypt_buffer(UINT8* pIn, UINT32 rounded_size, UINT32 size, UINT32 key) {
	HMODULE hMod = LoadLibrary(PYTHON_DLL);
	if (hMod == NULL) {
		printf("ERROR: failed to load the DLL\n");
		exit(1);
	}

	/* Calculate the decryption function address */
	DecryptFunc_t* funcAddr = (DecryptFunc_t*) ((DWORD_PTR) hMod
			+ DECRYPT_FCALL_OFFSET);

	/* Do the sanity checks */
	for (unsigned int i = 0;
			i < sizeof(decryptCheckBytes) / sizeof(decryptCheckBytes[0]); i++) {
		if (((BYTE*) funcAddr)[i] != decryptCheckBytes[i]) {
			printf("ERROR: sanity check failed at index %d\n", i);
			exit(1);
		}
	}

	/* Time to call into the DLL.
	 * The parameters are:
	 * EDI = buffer pointer
	 * EDX = size before rounding up
	 * ECX = key
	 *
	 * There's only a single stack parameter - two's complement of the rounded size / 4.
	 */
	asm("mov %0, %%edi;"
			"mov %1, %%edx;"
			"mov %2, %%ecx;"
			"mov %3, %%eax;"
			"mov %4, %%ebx;"
			"sar %%eax;"
			"sar %%eax;"
			"neg %%eax;"
			"push %%eax;"
			"call *%%ebx"
			: /* No output regs */
			: "m"(pIn), "m"(size), "m"(key), "m"(rounded_size), "m"(funcAddr)
			: /* Clobbered */"eax", "ebx", "ecx", "edx", "esi", "edi"
	);

}

void fix_opcodes(buffer_t* in, buffer_t* out) {

	/* Code is written as string, so we should see 's' here, followed by size */
	UINT8 type = get_uint8(in);
	put_uint8(out, type);

	if (type != 's') {
		printf("ERROR: expected code string!\n");
		exit(1);
	}

	UINT32 str_size = get_uint32(in);
	put_uint32(out, str_size);
	printf(", byte code size: 0x%08x\n", str_size);

	for (unsigned int j = 0; j < str_size; j++) {
		UINT8 opcode = get_uint8(in);
		if (opcode >= (sizeof(opcode_map) / sizeof(opcode_map[0]))) {
			printf("ERROR: invalid opcode (1) at %d!\n", (in->i - 1));
			exit(1);
		}
		opcode = opcode_map[opcode];
		if (opcode == _INVALID_OPCODE) {
			printf("ERROR: invalid opcode (2) at %d!\n", (in->i - 1));
			exit(1);
		}

		put_uint8(out, opcode);
		if (HAS_ARG(opcode)) {
			copy_bytes(in, out, 2);
			j += 2;
		}
	}
}

int process_object(buffer_t* in, buffer_t *out, interned_strings_map_t* strings);

/**
 * Function processing code objects
 */
void process_code(buffer_t* in, buffer_t *out) {

	printf("Code at 0x%08x: ", (in->i - 1));

	interned_strings_map_t* map = malloc(sizeof(interned_strings_map_t));
	if (!map) {
		printf("ERROR: out of mem!\n");
		exit(1);
	}
	map->count = 0;


	UINT32 key = get_uint32(in);
	UINT32 size = get_uint32(in);

	/* Round up the data size */
	UINT32 rounded_size = size;
	if ((size & 0x0F) != 0) {
		rounded_size = (size + 0x0F) & 0xFFFFFFF0;
	}

	printf("Key: 0x%08x, size: 0x%08x, rounded: 0x%08x", key, size,
			rounded_size);

	/* Decrypt the buffer with code object in place */
	decrypt_buffer(in->data + in->i, rounded_size, size, key);

	/* At this moment buffer contains decrypted code object, with all the fields. We need to copy the first 4 UINT32 fields verbatim */
	copy_bytes(in, out, 4 * 4);

	/* Next, there should be a bytecode string, which we pass to opcode remapping */
	fix_opcodes(in, out);

	/* Now we need to recuresively process other fields */
	process_object(in, out, map); // co_consts
	process_object(in, out, map); // co_names
	process_object(in, out, map); // co_varnames
	process_object(in, out, map); // co_freevars
	process_object(in, out, map); // co_cellvars
	process_object(in, out, map); // co_filename
	process_object(in, out, map); // co_name

	UINT32 co_firstlineno = get_uint32(in);
	put_uint32(out, co_firstlineno);

	process_object(in, out, map); // co_lnotab

	/* We need to skip the padding */
	in->i += (rounded_size - size);

	free(map);
}

/**
 * Main entry point to the decryption process.
 *
 * This method recursively reads the input data, decrypts code objects
 */

int process_object(buffer_t* in, buffer_t *out, interned_strings_map_t* strings) {
	int n;
	unsigned int i;
	UINT32 ref;

	UINT8 type = get_uint8(in);
	/* Type is always copied verbatim */
	put_uint8(out, type);

	switch (type) {

	case TYPE_NULL:
		/* Null is used as termination ! */
		return 0;
		break;

	case TYPE_NONE:
	case TYPE_STOPITER:
	case TYPE_ELLIPSIS:
	case TYPE_FALSE:
	case TYPE_TRUE:
		/* Tokens with no data */
		break;

	case TYPE_INT:
		/* Single int, 4 bytes */
		copy_bytes(in, out, 4);
		break;

	case TYPE_INT64:
		/* Single long long, 8 bytes */
		copy_bytes(in, out, 8);
		break;

	case TYPE_LONG:
		/* Arbitrary number */
		n = get_uint32(in);
		put_uint32(out, n);

		n = n < 0 ? -n : n;

		/* Each digit stored on 2 bytes */
		copy_bytes(in, out, (2 * n));
		break;

	case TYPE_FLOAT:
		n = get_uint8(in);
		put_uint8(out, n);

		/* String of n bytes */
		copy_bytes(in, out, n);
		break;

	case TYPE_BINARY_FLOAT:
		/* Always 8 bytes */
		copy_bytes(in, out, 8);
		break;

	case TYPE_COMPLEX:
		/* Two pascal strings */
		n = get_uint8(in);
		put_uint8(out, n);
		copy_bytes(in, out, n);

		n = get_uint8(in);
		put_uint8(out, n);
		copy_bytes(in, out, n);
		break;

	case TYPE_BINARY_COMPLEX:
		/* Two 8 byte floats */
		copy_bytes(in, out, 2 * 8);
		break;

	case TYPE_STRING: /* Fall through */
	case TYPE_UNICODE: /* Fall through */
	case TYPE_INTERNED:
		/* Pascal style string */
		n = get_uint32(in);
		put_uint32(out, n);
		copy_bytes(in, out, n);
		if (type == TYPE_INTERNED) {
			if (strings->count >= MAX_INTERNED_STRINGS) {
				printf("Too many interned strings!\n");
				exit(1);
			}
			strings->id[strings->count++] = interned_count;
			interned_count++;
		}
		break;

	case TYPE_STRINGREF:
		/* Single UINT32 */
		ref = get_uint32(in);

		/* Workaround for resetting the ref count on each nested object */
		if (ref >= strings->count) {
			printf("Invalid string ref!\n");
			exit(1);
		}
		put_uint32(out, strings->id[ref]);
		break;

	case TYPE_TUPLE: /* Fall through */
	case TYPE_LIST:
		/* UINT32 followed by n objects */
		n = get_uint32(in);
		put_uint32(out, n);

		/* Process objects recursively */
		for (i = 0; i < n; i++) {
			process_object(in, out, strings);
		}
		break;

	case TYPE_DICT:
		/* Serialized as key/value pairs, terminated with NULL */
		for (;;) {
			/* Key */
			if (!process_object(in, out, strings))
				break;

			/* Value */
			process_object(in, out, strings);
		}

		/* Null termination */
		put_uint8(out, '0');
		break;

	case TYPE_SET: /* Fall through */
	case TYPE_FROZENSET:
		n = get_uint32(in);
		put_uint32(out, n);

		/* Process objects recursively */
		for (i = 0; i < n; i++) {
			process_object(in, out, strings);
		}
		break;

	case TYPE_CODE:
		/* Code object needs special care */
		process_code(in, out);
		break;

	default:
		printf("Invalid token type 0x%02x ad 0x%08x", type, (in->i - 1));
		exit(1);
		break;

	}

	return 1;

}

int main(int argc, char** argv) {
	buffer_t in, out;
	interned_strings_map_t* map = NULL;

	if (argc != 3) {
		printf("Correct invocation: %s <input_file> <output_file>\n", argv[0]);
		exit(1);
	}

	read_file(&in, argv[1]);
	alloc_buffer(&out, in.size * 2);

	/* Read and check the magic number */
	UINT32 magic = get_uint32(&in);
	UINT32 mtime = get_uint32(&in);
	if (magic != PYC_MAGIC_DBOX) {
		printf("ERROR: invalid magic number!\n");
		exit(1);
	}
	put_uint32(&out, PYC_MAGIC_27);
	put_uint32(&out, mtime);

	map = malloc(sizeof(interned_strings_map_t));
	if (!map) {
		printf("ERROR: out of mem!\n");
		exit(1);
	}
	map->count = 0;

	/* Start recursive object processing */
	interned_count = 0;
	process_object(&in, &out, map);

	free(map);

	/* We're done, it's time to write it all back */

	FILE* fout = fopen(argv[2], "wb");
	if (!fout) {
		printf("ERROR: failed to open output file!\n");
		exit(1);
	}

	if (fwrite(out.data, 1, out.i, fout) != out.i) {
		printf("ERROR: error writing decrypted buffer!\n");
		exit(1);
	}

	fclose(fout);

	return 0;
}

