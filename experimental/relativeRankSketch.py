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

class RelativeRankSketch:
    def __init__(self, k= 128):
        if k <= 0: raise ValueError("k must be a positive integer.")
        self.k = k
        self.compactors = [Compactor()]
        self.H = 1
        self.size = 0

    def grow(self):
        self.compactors.append(Compactor())
        self.H = len(self.compactors)

    def update(self, update_item):
        self.compactors[0].append(update_item)
        self.size += 1
        if len(self.compactors[0]) > self.k:
            self.compress()

    def compress(self):
        for h in range(self.H):
            if len(self.compactors[h]) >= self.k:
                if h+1 >= self.H:
                    self.compactors.append(Compactor())
                    self.H += 1
                self.compactors[h+1].extend(self.compactors[h].compact())

    def rank(self, value):
        r = 0
        for (h, c) in enumerate(self.compactors):
            for item in c:
                if item <= value:
                    r += 2**h
        return r

    def cdf(self):
        items_and_weights = []
        for (h, items) in enumerate(self.compactors):
            items_and_weights.extend( (item, 2**h) for item in items )
        total_weight = sum(w for (_, w) in items_and_weights)
        items_and_weights.sort()
        cum_weight = 0
        cdf = []
        for (item, weight) in items_and_weights:
            cum_weight += weight
            cdf.append( (item, float(cum_weight)/float(total_weight) ) )
        return cdf

    def ranks(self):
        ranks_list = []
        items_and_weights = []
        for (h, items) in enumerate(self.compactors):
            items_and_weights.extend((it, 2**h) for it in items)
        items_and_weights.sort()
        cum_weight = 0
        for (it, w) in items_and_weights:
            cum_weight += w
            ranks_list.append((it, cum_weight))
        return ranks_list

    def __repr__(self):
        lengths = reversed([len(c) for c in self.compactors])
        return '\n'.join(['*'*l for l in lengths])


class Compactor(list):
    def compact(self):
        m = len(self)//2
        self.sort()
        for i in range(m, len(self), 2):
            yield self[i]
        self[m:] = []



if __name__ == '__main__':
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', type=int, default=128,
                        help='''controls the number of elements in the sketch which is 
                        at most 3k+log2(n). n is the length of the stream.''')
    parser.add_argument('-t', type=str, choices=["string", "int", "float"], default='string',
                        help='defines the type of stream items, default="string".')
    args = parser.parse_args()

    k = args.k if args.k > 0 else 128
    conversion_dictionary = {'int': int, 'string': str, 'float': float}
    conversion_function = conversion_dictionary[args.t]

    rrs = RelativeRankSketch(k)
    for line in sys.stdin:
        item = conversion_function(line.strip('\n\r'))
        rrs.update(item)

    for (item, rank) in rrs.ranks():
        print('%i\t%s' % (rank, str(item)))
