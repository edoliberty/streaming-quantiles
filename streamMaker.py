#!/usr/bin/python
'''
Written by Edo Liberty. All rights reserved.
Intended for academic use only. No commercial use is allowed.
'''

import random
from math import sqrt

class StreamMaker():
    def __init__(self):
        self.orders = ['sorted','zoomin','zoomout','sqrt','random'] 
        
    def make(self, n, order=''):
        assert(order in self.orders)
        
        if order == 'sorted': # sorted order
            for item in xrange(n):
                yield item
        elif order == 'zoomin': # zoom1
            for item in xrange(n/2):
                yield item
                yield n-item
        elif order == 'zoomout': # zoom1
            for item in xrange(1,n/2):
                yield n/2 + item
                yield n/2 - item
        elif order == 'sqrt': # zoom1
            t = int(sqrt(2*n))
            item = 0
            initialItem = 0
            initialSkip = 1
            for i in range(t):
                item = initialItem
                skip = initialSkip
                for j in range(t-i):
                    yield item
                    item+=skip
                    skip+=1 
                initialSkip+=1
                initialItem+=initialSkip
        else: # order == 'random':
            for _ in xrange(n):
                yield random.randint(0,n-1)
        
if __name__ == '__main__':
    import sys
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', type=int, help='the number of generated elements', default=1000)
    parser.add_argument('-o', type=str, help='the order of the streamed integers.',
                        choices=["sorted","zoomin","zoomout","sqrt","random"])
    args = parser.parse_args()
    
    
    streamer = StreamMaker()
    
    n = args.n if args.n > 0 else 1000
    order = args.o if args.o in streamer.orders else 'random'
    
    for item in streamer.make(n, order):
        sys.stdout.write('%d\n'%item)