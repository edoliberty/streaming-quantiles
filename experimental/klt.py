#!/usr/bin/python
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
Written by Edo Liberty. 
'''

import sys
#from random import random
from math import ceil
from numpy.random import random, geometric

class KLT:
    def __init__(self, eps=0.01, err='additive', lazy=True, alternate=True, bounded=False):
        eps_lower_bound, eps_upper_bound = 1e-6, 0.5
        if eps < eps_lower_bound or eps > eps_upper_bound:
            raise ValueError(f"eps must be int the range [{eps_lower_bound}.{eps_upper_bound}]")
        self.eps = eps

        self.Compactor = AdditiveCompactor
        if err=='relative':
            self.Compactor = RelativeCompactor

        self.k = int(1/eps)+1
        self.lazy = lazy
        self.alternate = alternate
        self.bounded = bounded
        self.compactors = []
        self.H = 0
        self.size = 0
        self.maxSize = 10*self.k
        self.grow()
        
    def grow(self):
        self.compactors.append(self.Compactor(eps=self.eps, alternate=self.alternate))
        self.H = len(self.compactors)
        if not self.bounded:
            self.maxSize = sum(self.capacity(height) for height in range(self.H))

    def capacity(self, hight):
        return 5*self.k
    
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
        return sum(c.rank(value)*2**h for (h, c) in enumerate(self.compactors))

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

    def __repr__(self):
        lengths = reversed([len(c) for c in self.compactors])
        return '\n'.join(['*'*l for l in lengths])

class AdditiveCompactor(list):
    def __init__(self, *kwargs):
        self.numCompaction = 0
        self.offset = 0
        self.alternate = kwargs.get('alternate', True)

    def compact(self):
        if (self.numCompaction%2==1 and self.alternate):
            self.offset = 1 - self.offset
        else:
            self.offset = int(random() < 0.5)

        self.sort()

        lastItem = None
        if (len(self)%2==1):
            lastItem = self.pop(-1)

        for i in range(self.offset, len(self), 2):
            yield self[i]

        self.clear()
        if lastItem is not None:
            self.append(lastItem)

        self.numCompaction += 1

    def rank(self, value):
        return sum(1 for v in self if v <= value)

class RelativeCompactor(list):
    def __init__(self, **kwargs):
        self.numCompaction = 0
        self.offset = 0
        self.eps = kwargs['eps']
        self.alternate = kwargs.get('alternate', True)

    def compact(self):
        if (self.numCompaction%2==1 and self.alternate):
            self.offset = 1 - self.offset
        else:
            self.offset = int(random() < 0.5)

        self.sort()
        s = geometric(self.eps)
        while s+1 >= len(self)//2:
            s = self.k + geometric(self.eps)
        s1 = len(self)//2 - s
        s2 = len(self)//2 + s
        for i in range(s1+self.offset, s2, 2):
            yield self[i]
        del self[s1:s2]
        self.numCompaction += 1

    def rank(self, value):
        return sum(1 for v in self if v <= value)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-eps', type=float, default=0.01,
                        help='''controls the accuracy of the sketch which is, default is 0.01''')
    parser.add_argument('-t', type=str, choices=["string", "int", "float"], default='string',
                        help='defines the type of stream items, default="string".')
    parser.add_argument('-err', type=str, choices=["additive", "relative"], default='additive',
                        help='sets the compactor to be either additive or relative, default="additive".')
    args = parser.parse_args()
    
    eps = args.eps
    conversions = {'int':int, 'string':str, 'float':float}
         
    kll = KLL(eps=eps, err=args.err)
    for line in sys.stdin:
        item = conversions[args.t](line.strip('\n\r'))
        kll.update(item)
        
    for (item, quantile) in kll.cdf():
        print(f"{quantile}\t{item}")
