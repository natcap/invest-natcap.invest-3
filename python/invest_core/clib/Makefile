LD_LIBRARY_PATH :=.:$(LD_LIBRARY_PATH)

all: libqueue.so a.out test

test: a.out

	./a.out

a.out: main.c
	gcc -L. -lqueue main.c

libqueue.so: queue.o
	gcc -shared -o libqueue.so queue.o

queue.o: queue.h queue.c
	gcc -c -fPIC queue.c
