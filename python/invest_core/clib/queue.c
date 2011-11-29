#include <stdlib.h>
#include "queue.h"

#define INITSIZE 64

struct _Queue {
  QueueValue *buf;
  int head;
  int tail;
  int size;
  int buflen;
};

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
  return queue;
}

QueueValue queue_pop_head(Queue *queue) {
  return 0;
}

int queue_size(Queue *queue) {
  return queue->size;
}
