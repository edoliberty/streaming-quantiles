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
    
* streamLength is a positive integer that controls the length of the stream  
* streamType can be one of the following options [sorted, zoomin, zoomout, sqrt, random]

You can then pipe it into the sketcher like this:

    python streamMaker.py <streamLength> <streamType> | python kll.py <k> <itemType>

* k is a positive integer that controls the size of the sketch. It defaults to 32.
* itemType is the type of items in the stream. It could take the values [int,float,string]. It defaults to "string". 

For example, try: 
    
    python streamMaker.py 100000 random | python kll.py 32 int

Or alternatively you can save the input 
	
	python streamMaker.py 100000 random > numbers.txt
	cat numbers.txt | python kll.py 32 int

You should get a approximate CDF of input stream. Something like this

	1496	0.001280
	2286	0.011520
	2799	0.032000
	2952	0.032640
	4648	0.035200
	.
	.
	.
	50844	0.502710
	52002	0.512950
	52800	0.533430
	53015	0.535990
	55959	0.546230
	56917	0.566710
	58003	0.576950
	.
	.
	.
	97675	0.964160
	97685	0.966720
	98044	0.976960
	98679	0.997440
	98881	1.000000
    
You can also try something like 
    
    cat README.md | python kll.py 10 string
    
    