#!/usr/bin/python
'''
Written by Edo Liberty. All rights reserved.
Intended for academic use only. No commercial use is allowed.
'''

import random
from math import sqrt,ceil

class StreamMaker():
    def __init__(self):
        self.orders = ['sorted','reversed','zoomin','zoomout','sqrt','random','adv1000'] 
        
    def make(self, n, order=''):
        assert(order in self.orders)
        
        if order == 'sorted': # sorted order
            for item in range(n):
                yield item
        elif order == 'reversed': # reversed sorted order
            for item in range(n-1,-1,-1):
                yield item
        elif order == 'zoomin': 
            for item in range(int(n/2)):
                yield item
                yield n-item
        elif order == 'zoomout': 
            for item in range(1,int(n/2)):
                yield n/2 + item
                yield n/2 - item
        elif order == 'sqrt': 
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
        elif order == 'adv1000': 
            t = 1000
            m = ceil(n/t)
            for i in range(t):
                for j in range(t + m*(t-i), t + m*(t-i-1), -1):
                    yield j
                yield i
        else: # order == 'random':
            items = list(range(n))
            random.shuffle(items)
            for item in items:
                yield item
        
if __name__ == '__main__':
    import sys
    import argparse
    streamer = StreamMaker()

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', type=int, help='the number of generated elements', default=1000)
    parser.add_argument('-o', type=str, help='the order of the streamed integers.',
                        choices=streamer.orders)
    args = parser.parse_args()
    
    n = args.n if args.n > 0 else 1000
    order = args.o if args.o in streamer.orders else 'random'
    for item in streamer.make(n, order):
        sys.stdout.write('%d\n'%item)
