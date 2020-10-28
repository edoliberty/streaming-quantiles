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
Written by Edo Liberty and Pavel Vesely. 

An implementation of the algorithm described in paper "Relative Error Streaming Quantiles", https://arxiv.org/abs/2004.01668

This implementation is mainly for experimental purposes --- it has many parameters that should be set to constants in prduction.
See RelativeErrorSketch.py for a simpler implementation.
It differs from the algorithm described in the paper in the following:

1) The algorithm requires no upper bound on the stream length (input size).
Instead, each relative-compactor (i.e. buffer) counts the number of compaction operations performed
so far (variable numCompactions). Initially, the relative-compactor starts with 2 buffer sections
and each time the numCompactions exceeds 2^{# of sections}, we double the number of sections
(variable numSections).

2) The size of each buffer section (variable sectionSize in the code and parameter k in the paper)
is initialized with a value set by the user via variable sectionSize (parameter -sec)
or via setting epsilon (parameter -eps). Setting the failure
probability delta is not implememnted. When the number of sections doubles, we decrease sectionSize
by a factor of sqrt(2) (for which we use a float variable sectionSizeF). As in item 1), this is applied
at each level separately.

Thus, when we double the number of section, the buffer size increases by a factor of sqrt(2) (up to +-1 after rounding).

For experimental purposes, the buffer consists of three parts:
- a part that is never compacted (its size can be set by variable never),
- numSections many sections of size sectionSize, and
- a part that is always involved in a compaction (its size can be set by variable always).

3) The merge operation here does not perform "special compactions", which are used in the paper to allow for
a tight analysis of the sketch.

'''

import sys
from math import ceil,sqrt
from random import random,randint

# CONSTANTS
SECTION_SIZE_SCALAR = 0.25
INIT_NUMBER_OF_SECTIONS = 2
SMALLEST_MEANINGFUL_SECTION_SIZE = 4
DEFAULT_EPS = 0.01
EPS_UPPER_BOUND = 0.1 # the sketch gives rather bad results for eps > 0.1

class RelativeErrorSketch:
    # initializaiton procedure
    def __init__(self, eps=DEFAULT_EPS, schedule='deterministic', always=-1, never=-1, sectionSize=-1, initNumSections = INIT_NUMBER_OF_SECTIONS, lazy=True, alternate=True):
        if eps > EPS_UPPER_BOUND:
            raise ValueError(f"eps must be at most {EPS_UPPER_BOUND}")
        self.eps = eps

        self.Compactor = RelativeCompactor

        self.lazy = lazy
        self.alternate = alternate
        self.schedule = schedule
        self.always = always
        self.never = never
        self.sectionSize = sectionSize
        
        self.initNumSections = initNumSections # an initial upper bound on log_2 of the number of compactions

        # default setting of sectionSize, always, and never according to eps
        if self.sectionSize == -1:
            self.sectionSize = 2*(int(SECTION_SIZE_SCALAR/eps)+1) # ensured to be even and positive (thus >= 2)
        if self.always == -1:
            self.always = self.sectionSize

        self.sizeOfNeverPartChanges = False # if never is set by the user, then we do not let it grow
        if self.never == -1:
            self.never = self.sectionSize * self.initNumSections + self.always # should be half of the buffer size
            self.sizeOfNeverPartChanges = True

        self.compactors = []
        self.H = 0
        self.size = 0
        self.grow()
        
    def grow(self):
        self.compactors.append(self.Compactor(schedule=self.schedule, sectionSize=self.sectionSize, numSections=self.initNumSections, always=self.always, never=self.never, sizeOfNeverPartChanges=self.sizeOfNeverPartChanges, height=self.H, alternate=self.alternate))
        self.H = len(self.compactors)
        self.updateMaxSize()

    # computes a new bound for determining when to compress the sketch
    def updateMaxSize(self):
        self.maxSize = sum(c.capacity() for c in self.compactors) 

    def update(self, item):
        self.compactors[0].append(item)
        self.size += 1
        if self.size >= self.maxSize:
            self.compress(self.lazy)
        assert(self.size < self.maxSize)
    
    def compress(self, lazy):
        self.updateMaxSize() # update in case parameters have changed
        if self.size < self.maxSize:
            return
        for h in range(len(self.compactors)):
            if len(self.compactors[h]) >= self.compactors[h].capacity():
                if h+1 >= self.H: self.grow()
                self.compactors[h+1].extend(self.compactors[h].compact())
                self.size = sum(len(c) for c in self.compactors)
                if(lazy and self.size < self.maxSize):
                    break
        debugPrint(f"compression done: size {self.size}\t maxSize {self.maxSize}")

    # merges sketch other into sketch self; one should use it only if sketch other is "smaller" than sketch self
    def mergeIntoSelf(self, other):
        # Grow until self has at least as many compactors as other
        while self.H < other.H: self.grow()
        # Append the items in same height compactors 
        for h in range(other.H):
            self.compactors[h].state = self.compactors[h].state | other.compactors[h].state
            self.compactors[h].numCompactions += other.compactors[h].numCompactions
            self.compactors[h].extend(other.compactors[h])
        self.size = sum(len(c) for c in self.compactors)
        if self.size >= self.maxSize:
            self.compress(False)
        assert(self.size < self.maxSize)
    
    # general merge operation; does NOT discard the input sketches;
    # tacitly assumes the sketches are created with the same parameters (but should not output an error if not, only the accuracy guanratees would be affected)
    def merge(one, two):
        if one.size >= two.size:
            one.mergeIntoSelf(two)
            return one
        else:
            two.mergeIntoSelf(one)
            return two

    def rank(self, value):
        return sum(c.rank(value)*2**h for (h, c) in enumerate(self.compactors))

    # the following two functions are the same as in kll.py

    # computes cummulative distribution function (as a list of items and their ranks expressed as a number in [0,1])
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
    
    # computes a list of items and their ranks
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
        self.numCompactions = 0 # number of compaction operations performed
        self.state = 0 # state of the deterministic compaction schedule
        self.offset = 0 # 0 or 1 uniformly at random in each compaction
        self.alternate = kwargs.get('alternate', True) # every other compaction has the opposite offset 
        self.sectionSize = kwargs.get('sectionSize', 32)
        self.sectionSizeF = float(self.sectionSize)
        self.numSections = kwargs.get('numSections', INIT_NUMBER_OF_SECTIONS)
        self.always = kwargs.get('always', self.sectionSize)
        self.never = kwargs.get('never', self.sectionSize * self.numSections)
        self.sizeOfNeverPartChanges = kwargs.get('sizeOfNeverPartChanges', True)
        self.height = kwargs.get('height', 0) 
        self.schedule = kwargs.get('schedule', "deterministic")
        self.schedules = ['deterministic','randomized', 'randomizedLinear']

        assert(self.schedule in self.schedules)

    def compact(self):
        assert(len(self) >= self.capacity())
        
        self.sort()
        
        s = self.never # where the compaction starts; default is self.never (that is, after the part that is never compacted)
        secsToCompact = 0

        # choose a part (number of sections) to compact according to the selected schedule
        if self.schedule == "randomizedLinear": # set s uniformly and randomly in [self.never,  self.never + self.numSections * self.sectionSize - 1]
            s = self.never + randint(0, self.numSections * self.sectionSize - 1)
        elif self.sectionSize >= SMALLEST_MEANINGFUL_SECTION_SIZE: # the smallest meaningful section size; o/w we use s = self.never
            if self.schedule == 'randomized':
                while (random() < 0.5 and secsToCompact < self.numSections): # ... according to the geometric distribution
                    secsToCompact += 1
            else: #if self.schedule == 'deterministic' -- choose according to the number of trailing zeros in binary representation of the number of compactions so far
                secsToCompact = trailing_ones_binary(self.state)
            s = self.never + (self.numSections - secsToCompact) * self.sectionSize
                        
            # make the number of sections larger 
            if self.numCompactions >= 2**self.numSections:
                self.numSections *= 2 # basically, a doubling strategy on log_2(number of compactions)
                #TODO replace doubling strategy by increments by 1?
                self.sectionSizeF = self.sectionSizeF / sqrt(2) # decreasing section size so that it equals roughly const/(eps * sqrt(log_2 (number of compactions))
                self.sectionSize = int(self.sectionSizeF)
                self.always = self.sectionSize
                if self.sizeOfNeverPartChanges: # update the part that is never compacted
                    self.never = self.sectionSize * self.numSections + self.always # should be half of the buffer size
        
        if (len(self) - s)%2==1: # ensure that the compacted part has an even size
            if s > 0: s -= 1
            else: s += 1

        assert(s < len(self) - 1)
        
        # random offset for choosing odd/even items in the compacted part; if alternate, then random choice done every other time
        if (self.numCompactions%2==1 and self.alternate):
            self.offset = 1 - self.offset
        else:
            self.offset = int(random() < 0.5)

        for i in range(s+self.offset, len(self), 2):
            yield self[i] # yield selected items
        debugPrint(f"compacting {s}:\tnumCompactions {self.numCompactions}\tsecsToComp {secsToCompact}\theight {self.height}\tcapacity {self.capacity()}\tsize {len(self)}\tsecSize {self.sectionSize}\tnumSecs {self.numSections}") #secSizeF {self.sectionSizeF}\t
        self[s:] = [] # delete items from the buffer part selected for compaction
        #debugPrint(f"compaction done: size {len(self)}")

        self.numCompactions += 1
        self.state += 1

    def capacity(self):
        cap = self.never + self.numSections * self.sectionSize + self.always
        assert(cap > 1)
        return cap

    def rank(self, value):
        return sum(1 for v in self if v <= value)

# AUXILIARY FUNCTIONS
def trailing_ones_binary(n):
    s = str("{0:b}".format(n))
    return len(s)-len(s.rstrip('1'))

def debugPrint(s):
    if debug:
        print(s)

debug = False

# MAIN -- INTENDED FOR TESTING THE SKETCH
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Program for testing the relative error sketch. Processes an input file with stream items (one per each line)')
    parser.add_argument('-eps', type=float, default=DEFAULT_EPS,
                        help='controls the accuracy of the sketch which is, default is 0.01; alternatively, accuracy can be controlled by -sec, -never, and -always')
    parser.add_argument('-t', type=str, choices=["string", "int", "float"], default='int',
                        help='defines the type of stream items, default="int".')
    parser.add_argument('-sch', type=str, choices=["deterministic", "randomized", "randomizedLinear"], default='deterministic',
                        help='sets the schedule of compactions on each level to deterministic, or randomized (geometric probability function), or randomizedLinear (linear probability function); default="deterministic".')
    parser.add_argument('-sec', type=int, default=-1,
                        help='size of each buffer section, should be even; by default set according to -eps.')
    parser.add_argument('-never', type=int, default=-1,
                        help='size of the buffer part that is never compacted, by default set to the section size times the number of sections.')
    parser.add_argument('-always', type=int, default=-1,
                        help='size of the buffer part that is always compacted, by default set to the section size.')
    parser.add_argument('-debug', action='store_true',
                        help='print debug messages; default=False.')
    parser.add_argument('-testMerge', type=str, choices=["binary", "random", "none"], default='none',
                        help='processes input by merge operations instead of stream updates; default=none (= do not test merge operation).')
    parser.add_argument('-print', action='store_true',
                        help='print stored items and theirs ranks; default=False.')
    parser.add_argument('-csv', action='store_true',
                        help='prints sketch statistics as one csv line (instead of in a user-friendly way); default=False.')
    parser.add_argument('-repeat', type=int, default=1,
                        help='the number of times to repeat building the sketch and calculating the maximum error; default = 1.')
    args = parser.parse_args()
    #print("args: ", args)
    
    debug = args.debug
    eps = args.eps
    printStored = args.print
    testMerge = args.testMerge
    csv = args.csv
    type = args.t
    conversions = {'int':int, 'string':str, 'float':float}
    
    # load all items (for testing purposes store every item)
    items = []
    for line in sys.stdin:
        item = conversions[type](line.strip('\n\r'))
        items.append(item)
    n = len(items)
    sortedItems = items.copy()
    sortedItems.sort()

    for r in range(0,args.repeat):
        sketch = RelativeErrorSketch(eps=eps, schedule=args.sch, always=args.always, never=args.never, sectionSize=args.sec)
    
        sketchesToMerge = [] # for testing merge operations
        for item in items:
            if testMerge == "none":
                sketch.update(item) # stream update
            else: # testing merge operations
                sketch.update(item)
                if sketch.size == sketch.compactors[0].capacity() / 10 - 1: # each sketch to be merged will be nearly full at level 0
                    sketchesToMerge.append(sketch)
                    sketch = RelativeErrorSketch(eps=eps, schedule=args.sch, always=args.always, never=args.never, sectionSize=args.sec)
        
    
        if testMerge != "none":
            if sketch.size > 0: sketchesToMerge.append(sketch)
            if testMerge == "random": # merge sketches in a random way
                while len(sketchesToMerge) > 1:
                    i = randint(0,len(sketchesToMerge) - 1)
                    j = i
                    while j == i:
                        j = randint(0,len(sketchesToMerge) - 1)
                    sketch = RelativeErrorSketch.merge(sketchesToMerge[i], sketchesToMerge[j])
                    sketchesToMerge.remove(sketchesToMerge[max(i,j)])
                    sketchesToMerge.remove(sketchesToMerge[min(i,j)])
                    sketchesToMerge.append(sketch)
                sketch = sketchesToMerge[0]
            elif testMerge == "binary": # complete binary merge tree
                while len(sketchesToMerge) > 1:
                    newList = []
                    for i in range(0, len(sketchesToMerge)-1, 2):
                        sketch = RelativeErrorSketch.merge(sketchesToMerge[i], sketchesToMerge[i+1])
                        newList.append(sketch)
                    if len(sketchesToMerge) % 2 == 1:
                        newList.append(sketchesToMerge[len(sketchesToMerge) - 1])
                    sketchesToMerge = newList
                sketch = sketchesToMerge[0]
    
        # calculate maximum relative error
        ranks = sketch.ranks()
        if printStored: 
            maxErrStored = 0
            print("item|apx.r.|true r.|err")
            #maximum relative error just among stored items
            for i in range(0, len(ranks)):
                (item, rank) = ranks[i]
                trueRank = sortedItems.index(item) + 1 #TODO speed this up
                err = abs(trueRank - rank) / trueRank
                maxErrStored = max(maxErrStored, err)
                errR = round(err, 4)
                print(f"{item}\t{rank}\t{trueRank}\t{errR}")
            print(f"\nmax rel. error among stored {maxErrStored}\n")

        # maximum relative error among all items
        maxErr = 0
        maxErrItem = -1
        i = 1
        j = 0
        for item in sortedItems:
            while j < len(ranks) - 1 and item == ranks[j+1][0]:
                j += 1
            (stored, rank) = ranks[j]
            err = abs(rank - i) / i
            if err > maxErr:
                maxErr = err
                maxErrItem = item
            #print(f"item {item}\t stored {stored}\t rank {rank}\t trueRank {i}\t{err}")
            i += 1

        sizeInBytes = sys.getsizeof(sketch) + sum(sys.getsizeof(c) for (h, c) in enumerate(sketch.compactors))
        if csv: # print sketch statistics as one csv line
            print(f"{n};{args.sch};{eps};{r};{maxErr};{maxErrItem};{sketch.size};{sketch.maxSize};{sketch.H};{sizeInBytes}")
        else: # user friendly sketch statistics
            print(f"n={n}\nmax rel. error overall \t{maxErr}\nmax. err item \t{maxErrItem}\nfinal size\t{sketch.size}\nmaxSize\t{sketch.maxSize}\nlevels\t{sketch.H}\nsize in bytes\t{sizeInBytes}")
