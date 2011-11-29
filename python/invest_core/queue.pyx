cimport cqueue

cdef class Queue:
    cdef cqueue.Queue *_c_queue
    def __cinit__(self,items=None):
        self._c_queue = cqueue.queue_new()
        if items != None:
            for i in items:
                cqueue.queue_push_tail(self._c_queue,i)

    def __dealloc__(self):
        cqueue.queue_free(self._c_queue)

    cdef extend(self, int* items, size_t count):
        for i in range(count):
            cqueue.queue_push_tail(self._c_queue,items[i])
