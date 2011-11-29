from collections import deque

cdef class Queue:
    """A queue class for C integer values.

    >>> q = Queue()
    >>> q.append(5)
    >>> q.peek()
    5
    >>> q.pop()
    5
    """
    
    q = deque()
    
    def __init__(self,values=None):
        cdef size_t i
        if values != None:
            for i in xrange(len(values)):
                self.q.append(values[i])
    
    def __cinit__(self):
        pass

    def __dealloc__(self):
        pass

    cdef append(self, int value):
        self.q.append(value)

    cdef extend(self, int* values, size_t count):
        cdef size_t i
        for i in xrange(count):
            self.q.append(values[i])

    def __getitem__(self,i):
        return self.q[i]

    def __size__(self):
        return len(self.q)

    cpdef int pop(self) except? -1:
        return self.q.pop()

    def __bool__(self):
        return self.__size__() == 0
    
    def __len__(self):
        return self.__size__()