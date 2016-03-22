# streaming-quantiles

This code implements the simplest algorithm described in 
the paper [Almost Optimal Streaming Quantiles Algorithms](http://arxiv.org/abs/1603.05346) by Zohar Karnin, Kevin Lang and myself.

* It is distributed free and with no warranty of any kind
* It should not be used of any commercial purposes
* It is written as an academic tool to readers of the paper to reproduce our results
* It is not optimized in any way
* It should only resemble the pseudo-code in the paper


### Example usage
 
For convenience, the class StreamMaker is included. To use it try:
     
    python streamMaker.py <streamLength> <streamType> 
    
* streamLength is a positive integer that controles the length of the stream  
* streamType can be one of the following options [sorted, zoomin, zoomout, sqrt, random]

You can then pipe it into the sketcher like this:

    python streamMaker.py <streamLength> <streamType> | python quantilesSketch.py <k>

* k is a positive integer that controls the size of the sketch.

For example, try: 
    
    python streamMaker.py 10000 random | python quantilesSketch.py 64
