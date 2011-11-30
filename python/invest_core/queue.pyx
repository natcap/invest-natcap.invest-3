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
        
    def __len__(self): 
        return cqueue.queue_size(self._c_queue)

    cpdef extend(self, items):
        for i in items:
            cqueue.queue_push_tail(self._c_queue,i)

    cpdef int pop(self):
        return cqueue.queue_pop_head(self._c_queue)
    
    cpdef append(self, int x):
        cqueue.queue_push_tail(self._c_queue, x)
