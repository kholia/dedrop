ARCH := $(shell getconf LONG_BIT)

CCFLAGS := -Wall -ggdb -fPIC
CFLAGS_32 := -m32
CFLAGS_64 := -m64
OFLAGS_32 := elf32-i386 -B i386
OFLAGS_64 := elf64-x86-64 -B i386:x86-64

# Update me
VER := 74.4.115

CFLAGS=-Wall -ggdb -fPIC

all:
	./opcode_mapper.py > map.h

	# dirty hacks
	python3 setup.py build
	cp build/lib.linux-x86_64-*/dedrop*37m*.so .
	cp build/lib.linux-x86_64-*/marshal3*37m*.so .
	python3 -c "import dedrop; dedrop.hello_world()"
	cp ./dedrop.cpython-37m-x86_64-linux-gnu.so .dropbox-dist/dropbox-lnx.x86_64-${VER}/dedrop.cpython-37m-x86_64-linux-gnu.so
	cp ./marshal3*.so .dropbox-dist/dropbox-lnx.x86_64-${VER}/marshal3.cpython-37m-x86_64-linux-gnu.so

	objcopy -I binary -O $(OFLAGS_$(ARCH)) payload.py payload.o
	# gcc $(CFLAGS) $(CFLAGS_$(ARCH)) -c -I$(HOME)/.pyenv/versions/3.7.2/include/python3.7m -o main.o main.c
	gcc $(CFLAGS) $(CFLAGS_$(ARCH)) -c -I/usr/include/python3.7 -o main.o main.c
	gcc $(CFLAGS) $(CFLAGS_$(ARCH)) -shared -Wl,-soname -Wl,libdedrop.so -o libdedrop.so main.o payload.o -lpthread -ldl

32:
	objcopy -I binary -O $(OFLAGS_32) payload.py payload.o
	gcc $(CFLAGS) $(CFLAGS_32) -c -I/usr/include/python3.6 -o main.o main.c
	gcc $(CFLAGS) $(CFLAGS_32) -shared -Wl,-soname -Wl,libdedrop.so -o libdedrop.so main.o payload.o -lpthread -ldl

64:
	objcopy -I binary -O $(OFLAGS_64) payload.py payload.o
	gcc $(CFLAGS) $(CFLAGS_64) -c -I/usr/include/python3.6 -o main.o main.c
	gcc $(CFLAGS) $(CFLAGS_64) -shared -Wl,-soname -Wl,libdedrop.so -o libdedrop.so main.o payload.o -lpthread -ldl


dump:
	python -c "import abc; import dis; dis.dis(abc)"


dump2:
	python -c "import output; import dis; dis.dis(output)"

compile:
	python -c "import compileall; compileall.compile_file('abcd.py', optimize=2)"

clean:
	-rm libdedrop.so
	-rm main.o
	-rm -rf build
