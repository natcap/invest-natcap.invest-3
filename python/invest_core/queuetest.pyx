cimport cython
import logging
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')
logger = logging.getLogger('queuetest')

from libc.stdlib cimport qsort, const_void 

cdef struct Pair:
    int i,j
    float h

cdef int compare(const_void *a, const_void *b):
    cdef float v = ((<Pair*>a)).h-((<Pair*>b)).h
    if v < 0: return -1
    if v > 0: return 1
    return 0

cdef void go():
    cdef Pair[5] pa
    for i in range(5):
        pa[i].i = i;
        pa[i].j = i*2;
        pa[i].h = i*.5;
    qsort(pa,5,sizeof(Pair),<int(*)>compare)
