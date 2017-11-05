#!/usr/bin/python
'''
Written by Edo Liberty. All rights reserved.
Intended for academic use only. No commercial use is allowed.
'''

import sys
from random import random
from math import ceil

class  KLL:
    def __init__(self, k, c = 2.0/3.0, lazy=True):
        if k<=0: raise ValueError("k must be a positive integer.")
        if c <= 0.5 or c > 1.0: raise ValueError("c must larger than 0.5 and at most 1.0.")
        self.k = k
        self.c = c
        self.lazy = lazy
        self.compactors = []
        self.H = 0
        self.size = 0 
        self.maxSize = 0
        self.grow()
        
    def grow(self):
        self.compactors.append(compactor())
        self.H = len(self.compactors)
        self.maxSize = sum(self.capacity(height) for height in range(self.H))
        
    def capacity(self, hight):
        depth = self.H - hight - 1
        return int(ceil(self.c**depth*self.k)) + 1
    
    def update(self, item):
        self.compactors[0].append(item)
        self.size += 1
        if self.size >= self.maxSize:
            self.compress()
            assert(self.size < self.maxSize)
            
    def compress(self):
        for h in range(len(self.compactors)):
            if len(self.compactors[h]) >= self.capacity(h):
                if h+1 >= self.H: self.grow()
                self.compactors[h+1].extend(self.compactors[h].compact())
                self.size = sum(len(c) for c in self.compactors)
                if(self.lazy):
                    break

    def merge(self, other):
        # Grow until self has at least as many compactors as other
        while self.H < other.H: self.grow()
        # Append the items in same height compactors 
        for h in range(other.H): self.compactors[h].extend(other.compactors[h])
        self.size = sum(len(c) for c in self.compactors)
        # Keep compressing until the size constraint is met
        while self.size >= self.maxSize:
            self.compress()
        assert(self.size < self.maxSize) 
        
    def rank(self, value):
        r = 0
        for (h, c) in enumerate(self.compactors):
             for item in c:
                 if item <= value:
                     r += 2**h
        return r

    def cdf(self):
        itemsAndWeights = []
        for (h, items) in enumerate(self.compactors):
             itemsAndWeights.extend( (item, 2**h) for item in items )
        totWeight = sum( weight for (item, weight) in itemsAndWeights)
        itemsAndWeights.sort()
        cumWeight = 0
        cdf = []
        for (item, weight) in itemsAndWeights:
            cumWeight += weight
            cdf.append( (item, float(cumWeight)/float(totWeight) ) )
        return cdf
    
    def ranks(self):
        ranksList = []
        itemsAndWeights = []
        for (h, items) in enumerate(self.compactors):
             itemsAndWeights.extend( (item, 2**h) for item in items )
        itemsAndWeights.sort()
        cumWeight = 0
        for (item, weight) in itemsAndWeights:
            cumWeight += weight
            ranksList.append( (item, cumWeight) )
        return ranksList

class compactor(list):
    def __init__(self):
        self.numCompaction = 0
        self.offset = None

    def compact(self):
        if (self.numCompaction%2==0):
            self.offset = int(random() < 0.5)
        else:
            self.offset = 1-self.offset

        self.sort()

        lastItem = None
        if (len(self)%2==1):
            lastItem = self.pop(-1)

        for i in range(self.offset,len(self),2):
            yield self[i]

        self.clear()
        if lastItem is not None:
            self.append(lastItem)

        self.numCompaction += 1

                          
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', type=int, default=128, 
                        help='''controls the number of elements in the sketch which is 
                        at most 3k+log2(n). n is the length of the stream.''')
    parser.add_argument('-t', type=str, choices=["string","int","float"], default='string',
                        help='defines the type of stream items, default="string".')
    args = parser.parse_args()
    
    k = args.k if args.k > 0 else 128
    conversions = {'int':int,'string':str,'float':float}
         
    kll = KLL(k)
    for line in sys.stdin:
        item = conversions[args.t](line.strip('\n\r'))
        kll.update(item)
        
    for (item, quantile) in kll.cdf():
        print('%f\t%s'%(quantile,str(item)))
        
