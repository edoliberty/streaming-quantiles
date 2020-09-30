#!/usr/bin/python
'''
Written by Edo Liberty and Pavel Vesely. All rights reserved.
Intended for academic use only. No commercial use is allowed.
'''

import random
from math import sqrt,ceil

class StreamMaker():
    def __init__(self):
        self.orders = ['sorted','reversed','zoomin','zoomout','sqrt','random','adv','clustered', 'clustered-zoomin'] 
        
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
            m = ceil(n/p)
            for i in range(p):
                for j in range(s*(g + p + m*(p-i)), s*(g + p + m*(p-i-1)), -s):
                    yield j
                yield i
                if i == p // 2:
                    for j in range(p, s*(g + p + m), s*(g + p + m) // 10):
                        yield j
        elif order == 'clustered': # sorted clustered order
            m = ceil(n/p) # number of clusters  of size p
            for i in range(m):
                # output cluster; g is the gap between clusters
                for j in range(i*g, i*g + p):
                    yield i*g + j / p
            for i in range(m):
                # put some items (roughly s many) into the gap between clusters
                for j in range(i*g + p, (i+1)*g, g // s):
                    yield j
        elif order == 'clustered-zoomin': # order roughly as in zoomin
            m = ceil(n/p) # number of clusters  of size p
            for i in range(m):
                # output cluster; g is the gap between clusters
                for j in range(i*g, i*g + p, 2):
                    yield i*g + j / p
            for i in range(m):
                # put some items (roughly s many) into the gap between clusters
                for j in range(i*g + p, (i+1)*g, g // s):
                    yield j
            for i in range(m - 1, 0, -1):
                # output cluster; g is the gap between clusters
                for j in range(i*g + p, i*g, -2):
                    yield i*g + (j + 1) / p
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
    parser.add_argument('-p', type=int, help='parameter for generating some orders (for orders adv and clustered only)', default=1000)
    parser.add_argument('-g', type=int, help='another parameter for generating some orders (for orders adv and clustered only)', default=0)
    parser.add_argument('-s', type=int, help='yet another parameter for generating some orders (for orders adv and clustered only)', default=1)
    parser.add_argument('-o', type=str, help='the order of the streamed integers.',
                        choices=streamer.orders)
    args = parser.parse_args()
    
    n = args.n if args.n > 0 else 1000
    order = args.o if args.o in streamer.orders else 'random'
    p = args.p if args.p > 0 else 1000
    g = args.g if args.g > 0 else 0
    s = args.s if args.s > 0 else 1
    for item in streamer.make(n, order, p, g, s):
        sys.stdout.write('%f\n'%item)
