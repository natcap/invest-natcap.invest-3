cdef extern from "clib/queue.h":
    ctypedef struct Queue:
        pass
    ctypedef int QueueValue

    Queue *queue_new()
    void queue_free(Queue *queue)
    Queue* queue_push_tail(Queue *queue, QueueValue data)
    QueueValue queue_pop_head(Queue *queue)
    int queue_size(Queue *queue)
