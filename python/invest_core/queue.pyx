cimport cqueue

cdef class Queue:
    cdef cqueue.Queue *_c_queue
    def __cinit__(self):
        self._c_queue = cqueue.queue_new()
        
    def __dealloc__(self):
        cqueue.queue_free(self._c_queue)

            