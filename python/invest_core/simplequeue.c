#include <stdlib.h>
#include "simplequeue.h"

#define INITSIZE 64

struct _Queue {
  QueueValue *buf;
  int head;
  int tail;
  int size;
  int buflen;
};

void _reallocateQueue(Queue* q) {
  if (q->size == q->buflen) {
    int ntocopy = ((q->size)-q->head);
    q->buflen *= 2;
    q->buf = (QueueValue*)realloc(q->buf,q->buflen*sizeof(QueueValue));
    q->head = q->buflen-ntocopy;
    memcpy(q->buf+q->head,q->buf+q->tail,sizeof(QueueValue)*ntocopy);
  }
}

Queue *queue_new(void)
{
  Queue *queue;
  queue = (Queue *) malloc(sizeof(Queue));
  queue->buf = (QueueValue*)malloc(sizeof(QueueValue)*INITSIZE);
  queue->head = 0;
  queue->tail = 0;
  queue->size = 0;
  queue->buflen = INITSIZE;
  
  return queue;
}

void queue_free(Queue *queue) {
  free(queue->buf);
}

Queue* queue_push_tail(Queue *queue, QueueValue data) {
  _reallocateQueue(queue);
  queue->buf[queue->tail] = data;
  queue->tail = (queue->tail+1)%queue->buflen;
  queue->size += 1;
  return queue;
}

QueueValue queue_pop_head(Queue *queue) {
  QueueValue v = queue->buf[queue->head];
  queue->head = (queue->head+1)%queue->buflen;
  queue->size -= 1;
  return v;
}

int queue_size(Queue *queue) {
  return queue->size;
}
