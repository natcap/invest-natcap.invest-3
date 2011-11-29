#include<stdio.h>
#include<stdlib.h>
#include "queue.h"

int main(int argc, char** argv) {
  Queue *q = queue_new();
  int i;
  int n=256;
  printf("Starting test\n");
  for (i=0; i < n; i+=1) {
    queue_push_tail(q,i);
    if (i % 7 == 0) {
      printf("%d\n",queue_pop_head(q));
    }
  }
  while(queue_size(q) > 0) {
    printf("%d\n",queue_pop_head(q));
  }
  queue_free(q);

  printf("Ending test\n");
  return 0;
}
