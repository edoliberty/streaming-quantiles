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

import numpy as np
import json

class  GDE:
    def __init__(self, k=128, d=None):
        self.k = k
        self.d = d
        self.n = 0
        self.size = 0
        self.compactors = [[]]
        self.max_size = self.k * len(self.compactors)
        self.compress = self.first_large_compress
    
    def merge(self, other):
        if other.d == None: # other is empty
            assert(other.n == 0)
            return 
        if self.d == None: # self is empty
            assert(self.n == 0)
            self.d = other.d
        elif self.d != other.d:
            raise ValueError("Dimension mismatch between two sketches")

        while len(self.compactors) < len(other.compactors):
            self.compactors.append([])
        for c1, c2 in zip(self.compactors, other.compactors):
            c1.extend(c2)

        self.size = np.sum([len(c) for c in self.compactors])
        self.n += other.n
        
        while self.size >= self.max_size:
            self.compress()
            self.max_size = self.k * len(self.compactors)
            self.size = np.sum([len(c) for c in self.compactors])
        
    def to_string(self):
        json_values = {"d":self.d, "k":self.k, "n":self.n}
        json_values["compactors"] = [[v.tolist() for v in c] for c in self.compactors]
        return json.dumps(json_values)

    def from_string(self, json_string):
        json_values = json.loads(json_string)
        self.k = json_values["k"]
        self.d = json_values["d"]
        self.n = json_values["n"]
        self.compactors = [[np.array(v) for v in c] for c in json_values["compactors"]]
        self.size = np.sum([len(c) for c in self.compactors])
        self.max_size = self.k * len(self.compactors)
        self.compress = self.first_large_compress    

    def update(self, vector):
        if self.d == None:
            self.d = len(vector)
        elif len(vector) != self.d:
            raise ValueError(f"Dimension mismatch, updated vector of dimention {len(vector)} does not fit sketch dimension {self.d}")

        while self.size >= self.max_size:
            self.compress()
            self.max_size = self.k * len(self.compactors)
            self.size = np.sum([len(c) for c in self.compactors])
        self.n += 1
        self.size += 1
        self.compactors[0].append(np.array(vector))
        
            
    def get_coreset(self):
        for height, compactor in enumerate(self.compactors):
            for vector in compactor:
                yield (2**height/self.n, vector)

    def kernel(self, vector_1, vector_2):
        return np.exp(-np.linalg.norm(vector_1 - vector_2)**2)

    def query(self, query):
        query = np.array(query)
        density = 0.0
        for height, compactor in enumerate(self.compactors):
            for vector in compactor:
                density += (2**height)*self.kernel(vector, query)/self.n
        return density

            
    def largest_buffer_compress(self):
        h = np.argmax([len(c) for c in self.compactors])
        if h >= len(self.compactors) -1:
            self.compactors.append([])
        self.compactors[h+1].extend(self.compact(self.compactors[h]))
    
    def first_large_compress(self):
        for h in range(len(self.compactors)):
            if len(self.compactors[h]) >= self.k:
                if h >= len(self.compactors)-1: 
                    self.compactors.append([])
                self.compactors[h+1].extend(self.compact(self.compactors[h]))
                break
            
    def all_large_compress(self):
        for h in range(len(self.compactors)):
            if len(self.compactors[h]) >= self.k:
                if h >= len(self.compactors)-1: 
                    self.compactors.append([])
                self.compactors[h+1].extend(self.compact(self.compactors[h]))
        
    def compact(self, compactor):        
        signs = np.random.choice([1.0,-1.0], len(compactor))
        np.random.shuffle(compactor)
        for i in range(1,len(compactor)):
            delta = 0.0
            for j in range(i):
                delta += signs[j]*self.kernel(compactor[i], compactor[j])
            signs[i] = -np.sign(delta)
        
        for i, sign in enumerate(signs):
            if sign >= 0:
                yield compactor[i]

        compactor.clear()

if __name__ == '__main__':
    import sys
    import argparse
    import json
    import numpy as np

    parser = argparse.ArgumentParser()
    parser.add_argument('-k', type=int, default=128, 
                        help='''controls the number of elements in the sketch which is 
                        at most k*log2(n/k) where n is the length of the stream.''')
    parser.add_argument('-d', '--dimension', type=int,
                        help='The number of dimensions in the vector to sketch.')

    args = parser.parse_args()
    
    if(args.k < 2 or args.dimension < 1):
        raise ValueError("k and d must be at least 2")
    
    gde = GDE(args.k, args.dimension)

    for line in sys.stdin:
        try:
            vec = np.array(json.loads(line))
            assert(len(vec) == args.dimension)
        except:
            raise ValueError(f"Could not parse json of dimension missmatch for input line \n{line}")

        gde.update(vec)
        
    for (weight, vector) in gde.get_coreset():
        print(json.dumps({"weight":weight, "vector":vector.tolist()}))

