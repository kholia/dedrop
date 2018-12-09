ARCH := $(shell getconf LONG_BIT)

CCFLAGS := -Wall -ggdb -fPIC
CFLAGS_32 := -m32
CFLAGS_64 := -m64
OFLAGS_32 := elf32-i386 -B i386
OFLAGS_64 := elf64-x86-64 -B i386:x86-64

CFLAGS=-Wall -ggdb -fPIC

all:
	# dirty hacks
	python3 setup.py build
	cp build/lib.linux-x86_64-*/dedrop*.so .
	cp build/lib.linux-x86_64-*/marshal3*.so .
	python3 -c "import dedrop; dedrop.hello_world()"
	cp ./dedrop.cpython-36m-x86_64-linux-gnu.so .dropbox-dist/dropbox-lnx.x86_64-62.4.103/dedrop.cpython-35m-x86_64-linux-gnu.so
	cp ./marshal3*.so .dropbox-dist/dropbox-lnx.x86_64-62.4.103/marshal3.cpython-35m-x86_64-linux-gnu.so

	objcopy -I binary -O $(OFLAGS_$(ARCH)) payload.py payload.o
	gcc $(CFLAGS) $(CFLAGS_$(ARCH)) -c -I/usr/include/python3.6 -o main.o main.c
	gcc $(CFLAGS) $(CFLAGS_$(ARCH)) -shared -Wl,-soname -Wl,libdedrop.so -o libdedrop.so main.o payload.o -lpthread -ldl

32:
	objcopy -I binary -O $(OFLAGS_32) payload.py payload.o
	gcc $(CFLAGS) $(CFLAGS_32) -c -I/usr/include/python3.6 -o main.o main.c
	gcc $(CFLAGS) $(CFLAGS_32) -shared -Wl,-soname -Wl,libdedrop.so -o libdedrop.so main.o payload.o -lpthread -ldl

64:
	objcopy -I binary -O $(OFLAGS_64) payload.py payload.o
	gcc $(CFLAGS) $(CFLAGS_64) -c -I/usr/include/python3.6 -o main.o main.c
	gcc $(CFLAGS) $(CFLAGS_64) -shared -Wl,-soname -Wl,libdedrop.so -o libdedrop.so main.o payload.o -lpthread -ldl


clean:
	-rm libdedrop.so
	-rm main.o
