ARCH := $(shell getconf LONG_BIT)

CCFLAGS := -Wall -ggdb -fPIC
CFLAGS_32 := -m32
CFLAGS_64 := -m64
OFLAGS_32 := elf32-i386 -B i386
OFLAGS_64 := elf64-x86-64 -B i386:x86-64

CPP_FLAGS := $(CPP_FLAGS_$(ARCH))  ... all the other flags ...

CFLAGS=-Wall -ggdb -fPIC -Wno-unused-but-set-variable

all:
	objcopy -I binary -O $(OFLAGS_$(ARCH)) payload.py payload.o
	gcc $(CFLAGS) $(CFLAGS_$(ARCH)) -c -I/usr/include/python2.7 -o main.o main.c
	gcc $(CFLAGS) $(CFLAGS_$(ARCH)) -shared -Wl,-soname -Wl,libdedrop.so -o libdedrop.so main.o payload.o -lpthread -ldl

32:
	objcopy -I binary -O $(OFLAGS_32) payload.py payload.o
	gcc $(CFLAGS) $(CFLAGS_32) -c -I/usr/include/python2.7 -o main.o main.c
	gcc $(CFLAGS) $(CFLAGS_32) -shared -Wl,-soname -Wl,libdedrop.so -o libdedrop.so main.o payload.o -lpthread -ldl

64:
	objcopy -I binary -O $(OFLAGS_64) payload.py payload.o
	gcc $(CFLAGS) $(CFLAGS_64) -c -I/usr/include/python2.7 -o main.o main.c
	gcc $(CFLAGS) $(CFLAGS_64) -shared -Wl,-soname -Wl,libdedrop.so -o libdedrop.so main.o payload.o -lpthread -ldl


clean:
	-rm libdedrop.so
	-rm main.o
