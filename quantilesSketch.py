'''
Written by Edo Liberty. All rights reserved.
Intended for academic use only. No commercial use is allowed.
'''

import sys
from random import random
from math import ceil

class  QuantilesSketch:
    def __init__(self, k, c = 2.0/3.0):
        self.k = k
        self.c = c
        self.compactors = []
        self.H = 0
        self.maxSize = 0
        self.grow()
        
    def grow(self):
        self.compactors.append(compactor())
        self.H = len(self.compactors)
        self.maxSize = sum(self.capacity(hight) for hight in range(self.H))
        
    def capacity(self, hight):
        depth = self.H - hight - 1
        return int(ceil(max(2.0, self.c**depth*self.k)))
    
    def update(self, item):
        self.compactors[0].append(item)
        if sum(len(c) for c in self.compactors) > self.maxSize:
            self.compress()
                 
    def compress(self):
        h=0
        while sum(len(c) for c in self.compactors) > self.maxSize:
            if len(self.compactors[h]) >= self.capacity(h):
                if h+1 >= self.H: self.grow()
                self.compactors[h+1].extend(self.compactors[h].compact())
            h+=1
    
    def merge(self, other):
        while self.H < other.H:
            self.grow()
        for h in xrange(self.H):
            self.compactors[h].extend(other.compactors[h])
        self.compress()
        
    def rank(self, value):
        r = 0
        for (h, items) in enumerate(self.compactors):
             for item in items:
                 if item <= value:
                     r += 2**h
        return r

class compactor(list):
    def compact(self):
        self.sort()
        if random() < 0.5:
            while len(self) >= 2:
                _ = self.pop()
                yield self.pop()
        else:
            while len(self) >= 2:
                yield self.pop()
                _ = self.pop()    
                          
if __name__ == '__main__':
    k = int(sys.argv[1])
    qs = QuantilesSketch(k)
    maxItem = None
    for line in sys.stdin:
        item = int(line.strip())
        qs.update(item)
        maxItem = max(maxItem,item)

    queries = [int(float(q)/10)+1 for q in xrange(0,10*maxItem+1,maxItem)]
    for q in queries:
        print 'query=%d -> rank=%d'%(q,qs.rank(q))