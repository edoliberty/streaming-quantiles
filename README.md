# streaming-quantiles

This code implements the simplest algorithm described in 
the paper [Almost Optimal Streaming Quantiles Algorithms](http://arxiv.org/abs/1603.05346) by Zohar Karnin, Kevin Lang and myself (Edo Liberty).

* It is distributed free and with no warranty of any kind.
* It should NOT be used of any commercial purposes.
* It is written as an academic tool for readers of the paper to reproduce our results.
* It is not optimized in any way.

### Usage

Main class in kll.py
              
    $ ./kll.py -h
    
	usage: kll.py [-h] [-k K] [-t {int,string,float}]
	optional arguments:
        -h, --help            show this help message and exit
        -k K                  controls the size of the sketch which is 3k+log(n),
                              where n is the length of the stream.
        -t {int,string,float}
                              defines the type of stream items.
                    
For convenience, the class StreamMaker is also included.
     
    $ ./streamMaker.py -h
    
	usage: streamMaker.py [-h] [-n N] [-o {sorted,zoomin,zoomout,sqrt,random}]
	optional arguments:
        -h, --help            show this help message and exit
		-n N                  the number of generated elements
		-o {sorted,zoomin,zoomout,sqrt,random}
                       		  the order of the streamed integers.
              
### Example
Try the following 
	
	./streamMaker.py -n 1000 -o zoomin > numbers.txt
	cat numbers.txt | ./kll.py -k 32 -t int > cdf.csv

You should get an approximate CDF of the input stream. The file cdf.csv should look something like this:
	
	0.016000,7
	0.032000,23
	0.048000,39
	0.064000,55
	0.080000,72
	.
	.
	.
	0.936000,923
	0.952000,940
	0.968000,956
	0.984000,973
	1.000000,989 

You can also try something (admittedly odd) like this: 
    
    man grep | ./kll.py
    
This will give approximate quantiles of the lines in the grep man page where the order of lines is lexicographic.