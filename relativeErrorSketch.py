#!/usr/bin/python
'''
Written by Edo Liberty and Pavel Vesely. All rights reserved.
Intended for academic use only. No commercial use is allowed.

Proof-of-concept code for paper "Relative Error Streaming Quantiles", https://arxiv.org/abs/2004.01668

This implementation differs from the algorithm described in the paper in the following:

1) The algorithm requires no upper bound on the stream length (input size).
Instead, each relative-compactor (i.e. buffer) counts the number of compaction operations performed
so far (variable numCompactions). Initially, the relative-compactor starts with 2 buffer sections
and each time the numCompactions exceeds 2^{# of sections}, we double the number of sections
(variable numSections).

2) The size of each buffer section (variables k and sectionSize in the code and parameter k in the paper)
is initialized with a value set by the user via variable k (parameterk -sec).
When the number of sections doubles, we decrease sectionSize by a factor of sqrt(2)
(for which we use a float variable sectionSizeF). As in item 1), this is applied at each level separately.

Thus, when we double the number of section, the buffer size increases by a factor of sqrt(2) (up to +-1 after rounding).

3) The merge operation here does not perform "special compactions", which are used in the paper to allow for
a tight analysis of the sketch.

'''

import sys
from math import ceil,sqrt
from random import random,randint

# CONSTANTS
INIT_NUMBER_OF_SECTIONS = 3 # an initial upper bound on log_2 (number of compactions) + 1
SMALLEST_MEANINGFUL_SECTION_SIZE = 4
DEFAULT_K = 50 # should be even; value of 50 roughly corresponds to 0.01-relative error guarantee w/ const. probability (TODO determine confidence bounds)

class RelativeErrorSketch:
    # initializaiton procedure; integer k sets the accuracy
    def __init__(self, k = DEFAULT_K):
        self.Compactor = RelativeCompactor
        self.k = k
        self.compactors = []
        self.H = 0
        self.size = 0
        self.grow()
        
    def grow(self):
        self.compactors.append(self.Compactor(sectionSize=self.k))
        self.H = len(self.compactors)
        self.updateMaxSize()

    # computes a new bound for determining when to compress the sketch
    def updateMaxSize(self):
        self.maxSize = sum(c.capacity() for c in self.compactors) 

    def update(self, item):
        self.compactors[0].append(item)
        self.size += 1
        if self.size >= self.maxSize:
            self.compress(True) # be lazy when compressing after adding a new item
        assert(self.size < self.maxSize)
    
    def compress(self, lazy):
        self.updateMaxSize() # update in case parameters have changed (perhaps, a more efficient way to do it is possible)
        if self.size < self.maxSize:
            return
        for h in range(len(self.compactors)):
            if len(self.compactors[h]) >= self.compactors[h].capacity():
                if h+1 >= self.H: self.grow()
                self.compactors[h+1].extend(self.compactors[h].compact())
                self.size = sum(len(c) for c in self.compactors) # again, a speed-up of this may be possible (subtract items discarded during compaction)
                if(lazy and self.size < self.maxSize):
                    break
        debugPrint(f"compression done: size {self.size}\t maxSize {self.maxSize}")

    # merges sketch other into sketch self; one should use it only if sketch other is "smaller" than sketch self
    def mergeIntoSelf(self, other):
        # Grow until self has at least as many compactors as other
        while self.H < other.H: self.grow()
        # Append the items in same height compactors 
        for h in range(other.H):
            self.compactors[h].mergeIntoSelf(other.compactors[h])
        self.size = sum(len(c) for c in self.compactors)
        if self.size >= self.maxSize:
            self.compress(False) # after merging, we should not be lazy when compressing the sketch (as the capacity bound may be exceeded on many levels)
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
    def __init__(self, sectionSize = DEFAULT_K):
        self.numCompactions = 0 # number of compaction operations performed
        self.state = 0 # state of the deterministic compaction schedule; if there are no merge operations performed, state == numCompactions
        self.offset = 0 # 0 or 1 uniformly at random in each compaction
        self.sectionSize = sectionSize
        self.sectionSizeF = float(self.sectionSize) # allows for an accurate decrease of sectionSize by factor of sqrt(2); possibly, not really needed
        self.numSections = INIT_NUMBER_OF_SECTIONS

    def compact(self):
        cap = self.capacity()
        assert(len(self) >= cap)
        
        # sort the items in the buffer; use self.sort(reverse=True) for a better accuracy for higher-ranked items; TODO: test this reversed order
        # remark: it's actually not needed to sort the whole buffer, we just need to ensure that the compacted part of the buffer is sorted and contains largest items
        self.sort() 
        
        # choose a part of the buffer to compact
        if self.sectionSize < SMALLEST_MEANINGFUL_SECTION_SIZE: # too small sections => compact half of the buffer always
            s = cap // 2
        else: # choose according to the deterministic schedule, i.e., according to the number of trailing zeros in binary representation of the state (which is the number of compactions so far, unless there are merge operations)
            secsToCompact = trailing_ones_binary(self.state) + 1
            s = cap // 2 + (self.numSections - secsToCompact) * self.sectionSize
            
            if self.numCompactions >= 2**(self.numSections - 1): # make the number of sections larger 
                self.numSections *= 2 # basically, a doubling strategy on log_2(number of compactions)
                #TODO replace doubling strategy by increments by 1?
                self.sectionSizeF = self.sectionSizeF / sqrt(2) # decreasing section size so that it equals roughly initial size / sqrt(log_2 (number of compactions)
                self.sectionSize = int(self.sectionSizeF)
        
        if (len(self) - s)%2==1: # ensure that the compacted part has an even size
            if s > 0: s -= 1
            else: s += 1
        assert(s < len(self) - 1 and s >= cap // 2 - 1) # at least half of the buffer should remain unaffected by compaction
        
        # random offset for choosing odd/even items in the compacted part; random choice done every other time
        if (self.numCompactions%2==1):
            self.offset = 1 - self.offset
        else:
            self.offset = int(random() < 0.5)

        for i in range(s+self.offset, len(self), 2):
            yield self[i] # yield selected items
        debugPrint(f"compacting {s}:\tnumCompactions {self.numCompactions}\tsecsToComp {secsToCompact}\tcapacity {self.capacity()}\tsize {len(self)}\tsecSize {self.sectionSize}\tnumSecs {self.numSections}") #secSizeF {self.sectionSizeF}\t
        self[s:] = [] # delete items from the buffer part selected for compaction
        #debugPrint(f"compaction done: size {len(self)}")

        self.numCompactions += 1
        self.state += 1

    def capacity(self):
        cap = 2 * self.numSections * self.sectionSize
        assert(cap > 1 and cap % 1 == 0)
        return cap

    def rank(self, value):
        return sum(1 for v in self if v <= value)

    # merges RelativeCompactor other into self
    def mergeIntoSelf(self, other):
        self.state = self.state | other.state # bitwise OR to merge states of the deterministic compaction schedule
        self.numCompactions += other.numCompactions
        self.extend(other)

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
    parser.add_argument('-k', type=int, default=DEFAULT_K,
                        help=f'controls the accuracy of the sketch, default={DEFAULT_K}')
    parser.add_argument('-t', type=str, choices=["string", "int", "float"], default='int',
                        help='defines the type of stream items, default="int".')
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
    k = args.k
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
        sketch = RelativeErrorSketch(k=k)
    
        sketchesToMerge = [] # for testing merge operations
        for item in items:
            if testMerge == "none":
                sketch.update(item) # stream update
            else: # testing merge operations
                sketch.update(item)
                if sketch.size == sketch.compactors[0].capacity() / 10 - 1: # each sketch to be merged will be nearly full at level 0
                    sketchesToMerge.append(sketch)
                    sketch = RelativeErrorSketch(k=k)
        
    
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
            print(f"{n};determistic;{k};{r};{maxErr};{maxErrItem};{sketch.size};{sketch.maxSize};{sketch.H};{sizeInBytes}")
        else: # user friendly sketch statistics
            print(f"n={n}\nmax rel. error overall \t{maxErr}\nmax. err item \t{maxErrItem}\nfinal size\t{sketch.size}\nmaxSize\t{sketch.maxSize}\nlevels\t{sketch.H}\nsize in bytes\t{sizeInBytes}")
