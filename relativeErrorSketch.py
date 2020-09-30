#!/usr/bin/python3
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
is initialized with a value set by the user via variable k (parameter -k).
When the number of sections doubles, we decrease sectionSize by a factor of sqrt(2)
(for which we use a float variable sectionSizeF). As in item 1), this is applied at each level separately.

Thus, when we double the number of section, the buffer size increases by a factor of sqrt(2) (up to +-1 after rounding).

3) The merge operation here does not perform "special compactions", which are used in the paper to allow for
a tight analysis of the sketch.

'''

import sys
from math import ceil,floor,sqrt,log
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
        self.N = 0 # size of the input summarized
        self.grow()
        
    def grow(self):
        self.compactors.append(self.Compactor(sectionSize=self.k, height=self.H))
        self.H = len(self.compactors)
        self.updateMaxNomSize()

    # computes a new bound for determining when to compress the sketch
    def updateMaxNomSize(self):
        self.maxNomSize = sum(c.nomCapacity() for c in self.compactors) 

    def update(self, item):
        self.compactors[0].append(item)
        self.size += 1
        self.N += 1
        if self.size >= self.maxNomSize:
            self.compress(True) # be lazy when compressing after adding a new item
        assert(self.size < self.maxNomSize)
    
    def compress(self, lazy):
        self.updateMaxNomSize() # update in case parameters have changed (perhaps, a more efficient way to do it is possible)
        if self.size < self.maxNomSize:
            return
        for h in range(len(self.compactors)):
            if len(self.compactors[h]) >= self.compactors[h].nomCapacity():
                if h+1 >= self.H: self.grow()
                self.compactors[h+1].extend(self.compactors[h].compact())
                self.size = sum(len(c) for c in self.compactors) # again, a speed-up of this may be possible (subtract items discarded during compaction)
                if(lazy and self.size < self.maxNomSize):
                    break
        #debugPrint(f"compression done: size {self.size}\t maxSize {self.maxNomSize}")

    # merges sketch other into sketch self; one should use it only if sketch other is "smaller" than sketch self
    def mergeIntoSelf(self, other):
        # Grow until self has at least as many compactors as other
        while self.H < other.H: self.grow()
        # Append the items in same height compactors 
        for h in range(other.H):
            self.compactors[h].mergeIntoSelf(other.compactors[h])
        self.N += other.N
        self.size = sum(len(c) for c in self.compactors)
        if self.size >= self.maxNomSize:
            self.compress(False) # after merging, we should not be lazy when compressing the sketch (as the capacity bound may be exceeded on many levels)
        assert(self.size < self.maxNomSize)
    
    # general merge operation; does NOT discard the input sketches;
    # tacitly assumes the sketches are created with the same parameters (but should not output an error if not, only the accuracy guanratees would be affected)
    def merge(one, two):
        if one.size >= two.size:
            one.mergeIntoSelf(two)
            return one
        else:
            two.mergeIntoSelf(one)
            return two

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
    
    
    # returns an approximate rank of value
    def rank(self, value):
        return sum(c.rank(value)*2**h for (h, c) in enumerate(self.compactors))
    
    # returns an approximate rank of value + numStdDev * standard deviation
    def getRankUpperBound(self, value, numStdDev):
        rank = self.rank(value)
        if rank <= self.k * INIT_NUMBER_OF_SECTIONS: # no error introduced for such items
            return rank
        else:
            return ceil((1 + numStdDev * RelativeErrorSketch.getMaximumRSE(self.k)) * rank)

    # returns an approximate rank of value - numStdDev * standard deviation
    def getRankLowerBound(self, value, numStdDev):
        rank = self.rank(value)
        if rank <= self.k * INIT_NUMBER_OF_SECTIONS: # no error introduced for such items
            return rank
        else:
            return floor((1 - numStdDev * RelativeErrorSketch.getMaximumRSE(self.k)) * rank)
        

    # returns an input item which is approx. q-quantile (i.e. has rank approx. q*self.N)
    def quantile(self, q):
        assert (q >= 0 and q <= 1), "parameter q must be in [0, 1], but q = %d" % q
        desiredRank = q*self.N
        ranks = self.ranks()
        i = 0
        j = len(ranks)
        while i < j:
            m = (i + j) // 2
            (item, rank) = ranks[m]
            if desiredRank > rank:
                i = m + 1
            else: j = m
        (item, rank) = ranks[i]
        return item

    def __repr__(self):
        lengths = reversed([len(c) for c in self.compactors])
        return '\n'.join(['*'*l for l in lengths])


    # STATIC METHODS

    # computes an approx. number of items stored by the sketch for a given parameter k after n (stream) updates
    # note 1: it might be possible to compute the exact bound, using a more sophisticated calculation
    # note 2: may be too loose when the sketch is built using merge operations
    @staticmethod
    def getMaxStoredItems(k, n):
        m = n 
        result = 0
        initBufferSize = RelativeCompactor(sectionSize=k).nomCapacity()
        while m > initBufferSize: # iterate over levels, m = UB on # of items inserted to the currently considered level
            numItems = m
            bufferSize = float(initBufferSize)
            secSize = float(k)
            numSections = INIT_NUMBER_OF_SECTIONS
            while True: # should be repeated at most log log (m) times
                numItems -= 2 * secSize * 2**numSections # approx. number of items removed with current parameters
                if numItems <= bufferSize or secSize < SMALLEST_MEANINGFUL_SECTION_SIZE:
                    break
                secSize /= sqrt(2)
                numSections *= 2
                bufferSize *= sqrt(2)
            #numBufferSizeIncreases = int(log(log(m / (2k), 2) / (INIT_NUMBER_OF_SECTIONS - 1), 2)) # m / k should be (m - bufferSize / 2) / k
            #bufferSize = 2 * int(initBufferSize * sqrt((log(numCompactions, 2) + 1) / INIT_NUMBER_OF_SECTIONS) / 2)
            #bufferSize = 2 * int(initBufferSize * sqrt(2)**numBufferSizeIncreases / 2 + 1)
            result += int(bufferSize) # we assume buffer is full at the end
            m = (m - int(bufferSize)) // 2 # UB on number of items at next level
        return result

    # Returns an a priori estimate of relative standard error (RSE, expressed as a number in [0,1]), calculated as sqrt(Var) / rank; note that it does not depend on the rank or n.
    # An upper bound on Var of the error is taken from Lemma 12 in https://arxiv.org/abs/2004.01668v2 (taking a possible improvement by a factor of 2 into account).
    # Still, this upper bound on RSE seems too pesimistic (by a factor of 3) and experiments suggest to replace the 8 below by approx. 1 (or even 0.9), at least when k is large enough (say, k >= 20; TODO: test this)
    @staticmethod
    def getMaximumRSE(k):
        return sqrt(8/INIT_NUMBER_OF_SECTIONS) / k



class RelativeCompactor(list):
    def __init__(self, sectionSize = DEFAULT_K, height = 0):
        self.numCompactions = 0 # number of compaction operations performed
        self.state = 0 # state of the deterministic compaction schedule; if there are no merge operations performed, state == numCompactions
        self.offset = 0 # 0 or 1 uniformly at random in each compaction
        self.sectionSize = sectionSize
        self.sectionSizeF = float(self.sectionSize) # allows for an accurate decrease of sectionSize by factor of sqrt(2); possibly, not really needed
        self.numSections = INIT_NUMBER_OF_SECTIONS
        self.height = height

    def compact(self):
        cap = self.nomCapacity()
        assert(len(self) >= cap)
        
        # sort the items in the buffer; use self.sort(reverse=True) for a better accuracy for higher-ranked items; TODO: test this reversed order
        # remark: it's actually not needed to sort the whole buffer, we just need to ensure that the compacted part of the buffer is sorted and contains largest items
        self.sort() 
        
        # choose a part of the buffer to compact
        if self.sectionSize < SMALLEST_MEANINGFUL_SECTION_SIZE: # too small sections => compact half of the buffer always
            s = cap // 2
            #TODO test: s = len(self) // 2
            secsToCompact = self.numSections # just for debugPrint below
        else: # choose according to the deterministic schedule, i.e., according to the number of trailing zeros in binary representation of the state (which is the number of compactions so far, unless there are merge operations)
            assert(self.numCompactions <= 2**(self.numSections - 1))
            assert(self.state <= 2**(self.numSections - 1))
            secsToCompact = trailing_ones_binary(self.state) + 1
            s = cap // 2 + (self.numSections - secsToCompact) * self.sectionSize
            self.ensureEnoughSections()
        
        if (len(self) - s)%2==1: # ensure that the compacted part has an even size
            if s > 0: s -= 1
            else: s += 1
        assert(s < len(self) - 1)
        assert(s >= cap // 2 - 1) # at least half of the nominal capacity of the buffer should remain unaffected by compaction
            
        # random offset for choosing odd/even items in the compacted part; random choice done every other time
        if (self.numCompactions%2==1):
            self.offset = 1 - self.offset
        else:
            self.offset = int(random() < 0.5)

        for i in range(s+self.offset, len(self), 2):
            yield self[i] # yield selected items
        #debugPrint(f"h={self.height}\tcompacting {s}:\tnumCompactions {self.numCompactions}\tsecsToComp {secsToCompact}\tcapacity {self.nomCapacity()}\tsize {len(self)}\tsecSize {self.sectionSize}\tnumSecs {self.numSections}") #secSizeF {self.sectionSizeF}\t
        self[s:] = [] # delete items from the buffer part selected for compaction
        #debugPrint(f"compaction done: size {len(self)}")

        self.numCompactions += 1
        self.state += 1
    
    def ensureEnoughSections(self):
        if self.numCompactions >= 2**(self.numSections - 1): # make the number of sections larger 
            self.numSections *= 2 # basically, a doubling strategy on log_2(number of compactions)
            self.sectionSizeF = self.sectionSizeF / sqrt(2) # decreasing section size so that it equals roughly initial size / sqrt(log_2 (number of compactions)
            self.sectionSize = int(self.sectionSizeF)

    def nomCapacity(self):
        cap = 2 * self.numSections * self.sectionSize
        assert(cap > 1)
        return cap

    def rank(self, value):
        return sum(1 for v in self if v <= value)

    # merges RelativeCompactor other into self
    def mergeIntoSelf(self, other):
        self.state = self.state | other.state # bitwise OR to merge states of the deterministic compaction schedule
        self.numCompactions += other.numCompactions
        self.ensureEnoughSections()
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
                if sketch.size == sketch.compactors[0].nomCapacity() / 10 - 1: # each sketch to be merged will be nearly full at level 0
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
        j = 0
        for i in range(0, len(sortedItems)):
            item = sortedItems[i]
            if i < len(sortedItems) - 1 and sortedItems[i] == sortedItems[i+1]:
                continue
            tr = i + 1
            while j < len(ranks) - 1 and item == ranks[j+1][0]:
                j += 1
            (stored, rank) = ranks[j]
            err = abs(rank - tr) / tr
            if err > maxErr:
                maxErr = err
                maxErrItem = item
            #print(f"item {item}\t stored {stored}\t rank {rank}\t trueRank {tr}\t{err}")
            i += 1
          
        sizeInBytes = sys.getsizeof(sketch) + sum(sys.getsizeof(c) for (h, c) in enumerate(sketch.compactors))
        maxStoredItems = RelativeErrorSketch.getMaxStoredItems(k, n)
        if csv: # print sketch statistics as one csv line
            print(f"{n};determistic;{k};{r};{maxErr};{maxErrItem};{sketch.size};{sketch.maxNomSize};{maxStoredItems};{sketch.H};{sizeInBytes}")
        else: # user friendly sketch statistics
            print(f"n={n}\nmax rel. error overall \t{maxErr}\nmax. err item \t{maxErrItem}\nfinal size\t{sketch.size}\nmaxSize\t{sketch.maxNomSize}\ngetMaxStoredItems\t{maxStoredItems}\nlevels\t{sketch.H}\nsize in bytes\t{sizeInBytes}")
        
        # SOME COMMENTED OUT CODE FOR TESTING VARIOUS FUNCTIONS
        #maxRSE = RelativeErrorSketch.getMaximumRSE(k)
        #print(f"max RSE = {maxRSE}")
        #estRank = sketch.rank(sortedItems[n // 2])
        #ub1 = sketch.getRankUpperBound(sortedItems[n // 2], 1.0)
        #ub2 = sketch.getRankUpperBound(sortedItems[n // 2], 2.0)
        #ub15 = sketch.getRankUpperBound(sortedItems[n // 2], 1.5)
        #lb1 = sketch.getRankLowerBound(sortedItems[n // 2], 1.0)
        #lb2 = sketch.getRankLowerBound(sortedItems[n // 2], 2.0)
        #lb15 = sketch.getRankLowerBound(sortedItems[n // 2], 1.5)
        #print(f"item of rank {n // 2 + 1}, estRank = {estRank}")
        #print(f"ub1\t{ub1}\tlb1\t{lb1}")
        #print(f"ub15\t{ub15}\tlb15\t{lb15}")
        #print(f"ub2\t{ub2}\tlb2\t{lb2}")
        #for q in [0, 0.0001, 0.001, 0.1, 0.2, 0.33, 0.5, 0.7, 0.9, 0.95, 0.99, 0.9999, 1]:
        #    item = sketch.quantile(q)
        #    print(f"q {q} = {item}")
