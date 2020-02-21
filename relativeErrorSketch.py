#!/usr/bin/python
'''
Written by Edo Liberty and Pavel Vesely. All rights reserved.
Intended for academic use only. No commercial use is allowed.
'''

import sys
#from random import random
from math import ceil
from numpy.random import random, geometric

class RelativeErrorSketch:
    def __init__(self, eps=0.01, schedule='deterministic', initMaxSize=0, lazy=True, alternate=True): #, bounded = False -- PV: makes sense only with schedule == 'alwaysAll', o/w sketch size must grow with new items
        eps_lower_bound, eps_upper_bound = 1e-6, 0.5
        if eps < eps_lower_bound or eps > eps_upper_bound:
            raise ValueError(f"eps must be int the range [{eps_lower_bound}.{eps_upper_bound}]")
        self.eps = eps

        self.Compactor = RelativeCompactor

        self.lazy = lazy
        self.alternate = alternate
        self.schedule = schedule
        #self.bounded = bounded
        #if self.bounded and self.schedule != 'alwaysAll':
        #    raise ValueError("Bounded size sketch should not be used for relative error.")

        #self.k = int(1/eps)+1
        self.sectionSize = 2*(int(1/(4*eps))+1) # ensured to be even and positive (thus >= 2)
        if self.schedule == 'alwaysHalf':
            self.sectionSize = int(1/(eps**2))+1

        self.numSections = 2 # an initial upper bound on log_2 (number of compactions)

        self.compactors = []
        self.H = 0
        self.size = 0
        self.grow()
        
    def grow(self):
        self.compactors.append(self.Compactor(schedule = self.schedule, sectionSize = self.sectionSize, numSections = self.numSections, height = self.H, alternate=self.alternate))
        self.H = len(self.compactors)
        #if not bounded:
        self.updateMaxSize()

    def updateMaxSize(self):
        self.maxSize = sum(c.capacity() for c in self.compactors) # a new bound for when to compress the sketch

    def update(self, item):
        self.compactors[0].append(item)
        self.size += 1
        if self.size >= self.maxSize:
            self.compress()
        assert(self.size < self.maxSize)
            
    def compress(self):
        self.updateMaxSize()
        if self.size < self.maxSize:
            return
        for h in range(len(self.compactors)):
            if len(self.compactors[h]) >= self.compactors[h].capacity():
                if h+1 >= self.H: self.grow()
                self.compactors[h+1].extend(self.compactors[h].compact())
                self.size = sum(len(c) for c in self.compactors)
                if(self.lazy):
                    break
        print(f"compression done: size {self.size}\t maxSize {self.maxSize}")

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

    def quantile(self, rank):
        return "" #TODO

    # the following two fucntions are the same as in kll.py
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


class RelativeCompactor(list):
    def __init__(self, **kwargs):
        self.numCompaction = 0
        self.offset = 0
        #self.eps = kwargs['eps']
        self.alternate = kwargs.get('alternate', True)
        self.sectionSize = kwargs.get('sectionSize', 32)
        self.numSections = kwargs.get('numSections', 5)
        self.height = kwargs.get('height', 0) # not used now
        self.schedule = kwargs.get('schedule', "deterministic")
        self.schedules = ['deterministic','randomized','alwaysHalf','alwaysAll']
        assert(self.schedule in self.schedules)

    def compact(self):
        assert(len(self) >= self.capacity())

        if (self.numCompaction%2==1 and self.alternate):
            self.offset = 1 - self.offset
        else:
            self.offset = int(random() < 0.5)

        self.sort()
        
        lastItem = None
        
        s = 0 # where the compaction starts; default is 0 for self.schedule == 'alwaysAll'
        secsToCompact = 0

        # choose a part to compact according to the selected schedule
        if self.schedule == 'deterministic' or self.schedule == 'randomized':
            if self.schedule == 'randomized':
                while True:
                    secsToCompact = geometric(0.5)
                    if (secsToCompact <= self.numSections):
                        break
            else: #if self.schedule == 'deterministic' 
                secsToCompact = trailing_zeros(self.numCompaction)
            s = int(2/3 * self.capacity()) - secsToCompact * self.sectionSize # 1/3 of capacity always compacted
                        
            # make the number of sections larger 
            if self.numCompaction > 2**self.numSections:
                self.numSections *= 2 # basically, doubling strategy on log_2 (number of compactions)
            
        elif self.schedule == 'alwaysHalf': 
            s = int(self.capacity() / 2)
        #TODO randomizedSimple: set s uniformly and randomly in [0.25 * capacity(), 0.75 * capacity()], or sth like that
        
        assert(s < len(self) - 1)
        
        if ((len(self) - s)%2==1):
            s += 1

        for i in range(s+self.offset, len(self), 2):
            yield self[i]
        print(f"compacting {s}:\t secsToComp {secsToCompact}\t height {self.height}\t capacity {self.capacity()}\t size {len(self)}\t secSize {self.sectionSize}\t numSecs {self.numSections}")
        self[s:] = []
        print(f"compaction done: size {len(self)}")

        self.numCompaction += 1

    def capacity(self):
        return 3 * self.numSections * self.sectionSize

    def rank(self, value):
        return sum(1 for v in self if v <= value)

# AUXILIARY FUNCTIONS
def trailing_zeros(n):
    s = str(n)
    return len(s)-len(s.rstrip('0'))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-eps', type=float, default=0.01,
                        help='''controls the accuracy of the sketch which is, default is 0.01''')
    parser.add_argument('-t', type=str, choices=["string", "int", "float"], default='int',
                        help='defines the type of stream items, default="int".')
    #parser.add_argument('-err', type=str, choices=["additive", "relative"], default='additive', # PV: SUPERSEDED BY THE FOLLOWING ARGUMENT
    #                    help='sets the compactor to be either additive or relative, default="additive".')
    parser.add_argument('-sch', type=str, choices=["deterministic", "randomized", "alwaysHalf", "alwaysAll"], default='deterministic',
                        help='sets the schedule of compactions on each level to either deterministic or randomized; "alwaysHalf" is for compacting half of the buffer each time; use "alwaysAll" for additive error; default="deterministic".')
    #parser.add_argument('-split', type=str, choices=["halves", "thirds"], default='thirds',
    #                    help='an argument for the schedule, default="string".') #TODO explain & implement
    args = parser.parse_args()
    
    eps = args.eps
    conversions = {'int':int, 'string':str, 'float':float}
         
    sketch = RelativeErrorSketch(eps=eps, schedule=args.sch)
    for line in sys.stdin:
        item = conversions[args.t](line.strip('\n\r'))
        sketch.update(item)
        
    for (item, quantile) in sketch.cdf():
        print(f"{quantile}\t{item}")
        
    print(f"final size {sketch.size}\t maxSize {sketch.maxSize}")
