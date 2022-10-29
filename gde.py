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
import numpy as np

class  GDE:
    def __init__(self, k, d):
        self.k = k
        self.d = d
        self.compactors = [[]]

    def update(self, vector):
        vector = np.array(vector)
        self.compactors[0].append(np.array(vector))
        if len(self.compactors[0]) > self.k:
            self.compress()
            
    def get_coreset(self):
        for height, compactor in enumerate(self.compactors):
            for vector in compactor:
                yield (2**height, vector)

    def kernel(self, vector_1, vector_2):
        return np.exp(-np.linalg.norm(vector_1 - vector_2)**2)

    def query(self, query):
        query = np.array(query)
        density = 0.0
        for height, compactor in enumerate(self.compactors):
            for vector in compactor:
                density += (2**height)* self.kernel(vector, query)
        return density

    def compress(self):
        for h in range(len(self.compactors)):
            if len(self.compactors[h]) > self.k:
                if h >= len(self.compactors)-1: 
                    self.compactors.append([])
                self.compactors[h+1].extend(self.compact(self.compactors[h]))

    def compact(self, compactor):
        signs = [np.random.choice([1.0,-1.0])]
        for i in range(1,len(compactor)):
            delta = 0.0
            for j in range(i):
                delta += signs[j]*self.kernel(compactor[i], compactor[j])
            
            sign = -np.sign(delta)
            signs.append(sign)
            if sign >= 0:
                yield compactor[i]

        compactor.clear()

if __name__ == '__main__':
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
        raise ValueError("baaaaad inputs :)")
    
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

