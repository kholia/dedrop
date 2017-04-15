# ----------------------------------------------------------------------
# Makefile for KgWrapper.dll
# ----------------------------------------------------------------------

CC=C:\MinGW\bin\gcc.exe
CFLAGS=-c -g3 -std=gnu99 -O0 -Wall

OBJS=src\decrypt.o src\buffer.o
EXE=bin\decrypt.exe

all: $(EXE)

$(EXE): $(OBJS)
	-mkdir bin
	$(CC) -O0 -g3 -o $(EXE) $(OBJS)

%.o: %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

clean:
	del $(EXE)
	del $(OBJS)
