#ifndef _SIMPLEQUEUE_H
#define _SIMPLEQUEUE_H

typedef struct _Queue Queue;
typedef int QueueValue;

/**
 * Create a new queue.
 *
 * @return A new queue.
 *
 */
Queue *queue_new(void);

/**
 * Destroy a queue.
 *
 * @param queue      The queue to destroy.
 */
void queue_free(Queue *queue);

/**
 * Add a value to the tail of a queue.
 *
 * @param queue      The queue.
 * @param data       The value to add.
 *
 * @return a reference to @ref queue.
 */

Queue* queue_push_tail(Queue *queue, QueueValue data);

/**
 * Remove a value from the head of a queue.
 *
 * @param queue      The queue.
 * @return           Value that was at the head of the queue
 */

QueueValue queue_pop_head(Queue *queue);

/**
 * Query the number of elements in the queue.
 *
 * @param queue      The queue.
 * @return           Size of queue.
 */
int queue_size(Queue *queue);

#endif
