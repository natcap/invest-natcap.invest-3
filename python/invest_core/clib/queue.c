#include <stdlib.h>
#include "queue.h"

#define INITSIZE 64

struct _Queue {
  int *buf;
  int head;
  int tail;
  int size;
  int buflen;
};

Queue *queue_new(void)
{
  Queue *queue;
  queue = (Queue *) malloc(sizeof(Queue));
  queue->buf = (int*)malloc(sizeof(int)*INITSIZE);
  queue->head = 0;
  queue->tail = 0;
  queue->size = 0;
  queue->buflen = INITSIZE;
  
  return queue;
}
