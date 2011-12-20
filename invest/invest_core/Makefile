LD_LIBRARY_PATH :=.:$(LD_LIBRARY_PATH)

all: libsimplequeue.so a.out test

test: a.out
	./a.out

a.out: main.c
	gcc -L. -lsimplequeue main.c

libsimplequeue.so: simplequeue.o
	gcc -shared -o libsimplequeue.so simplequeue.o

simplequeue.o: simplequeue.h simplequeue.c
	gcc -c -fPIC simplequeue.c -o simplequeue.o

clean:
	rm -rf *.so *.o a.out
