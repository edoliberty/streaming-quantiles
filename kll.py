'''
Written by Edo Liberty. All rights reserved.
Intended for academic use only. No commercial use is allowed.
'''

import sys
from random import random
from math import ceil

class  KLL:
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
    k = 32 if len(sys.argv)<2 else int(sys.argv[1])
    itemType = 'int' if len(sys.argv)<3 else sys.argv[2]
    conversions = {'int':int,'string':str,'float':float}
    
    kll = KLL(k)
    for line in sys.stdin:
        item = conversions[itemType](line.strip('\n\r'))
        kll.update(item)
        
    cdf = kll.cdf()
    for (item, quantile) in cdf:
        print '%s\t%f'%(str(item), quantile)