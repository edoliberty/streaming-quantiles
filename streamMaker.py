#!/usr/bin/python
'''
Written by Edo Liberty. All rights reserved.
Intended for academic use only. No commercial use is allowed.
'''

import random
from math import sqrt,ceil

class StreamMaker():
    def __init__(self):
        self.orders = ['sorted','reversed','zoomin','zoomout','sqrt','random','adv'] 
        
    def make(self, n, order='', p=1000, g=0, s=1):
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
        elif order == 'adv': 
            t = p
            m = ceil(n/t)
            for i in range(t):
                for j in range(g + t + m*(t-i), g + t + m*(t-i-1), -1):
                    yield j
                yield s*i
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
    parser.add_argument('-p', type=int, help='parameter for generating some orders (currently for order adv only)', default=1000)
    parser.add_argument('-g', type=int, help='another parameter for generating some orders (currently for order adv only)', default=0)
    parser.add_argument('-s', type=int, help='yet another parameter for generating some orders (currently for order adv only)', default=1)
    parser.add_argument('-o', type=str, help='the order of the streamed integers.',
                        choices=streamer.orders)
    args = parser.parse_args()
    
    n = args.n if args.n > 0 else 1000
    order = args.o if args.o in streamer.orders else 'random'
    p = args.p if args.p > 0 else 1000
    g = args.g if args.g > 0 else 0
    s = args.s if args.s > 0 else 1
    for item in streamer.make(n, order, p, g, s):
        sys.stdout.write('%d\n'%item)
