'''
Written by Edo Liberty. All rights reserved.
Intended for academic use only. No commercial use is allowed.
'''

import random
from math import sqrt

class StreamMaker():
    def __init__(self):
        self.types = ['sorted','zoomin','zoomout','sqrt','random'] 
        
    def make(self, n, streamType=''):
        assert(streamType in self.types)
        
        if streamType == 'sorted': # sorted order
            for item in xrange(n):
                yield item
        elif streamType == 'zoomin': # zoom1
            for item in xrange(n/2):
                yield item
                yield n-item
        elif streamType == 'zoomout': # zoom1
            for item in xrange(1,n/2):
                yield n/2 + item
                yield n/2 - item
        
        elif streamType == 'sqrt': # zoom1
            t = int(sqrt(2*n))
            item = 0
            initialItem = 0
            initialSkip = 1
            for i in range(t):
                item = initialItem
                skip = initialSkip
                for j in range(t-i):
                    yield item
                    item+=skip
                    skip+=1 
                initialSkip+=1
                initialItem+=initialSkip
        else: # streamType == 'random':
            items = range(n)
            random.shuffle(items)
            for item in items:
                yield item
        
if __name__ == '__main__':
    import sys
    streamer = StreamMaker()
    n = int(sys.argv[1])
    streamType = sys.argv[2]
    for item in streamer.make(n, streamType):
        sys.stdout.write('%d\n'%item)