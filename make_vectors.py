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

if __name__ == '__main__':
    import argparse
    import json
    import numpy as np

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', type=int, default=128, 
                        help='''The number of vectors''')
    parser.add_argument('-d', '--dimension', type=int, default=3, 
                        help='The number of dimensions in the vector to sketch.')
    args = parser.parse_args()

    for i in range(args.n):
        vector = np.random.randn(args.dimension)
        print(f"{json.dumps(list(vector))}")