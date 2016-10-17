# streaming-quantiles

This code implements the simplest algorithm described in 
the paper [Optimal Quantile Approximation in Streams (FOCS 2016)](http://arxiv.org/abs/1603.05346) by Zohar Karnin, Kevin Lang and myself (Edo Liberty).

* It is distributed free and with no warranty of any kind.
* It should NOT be used for any commercial purposes.
* It is written as an academic tool for readers of the paper to reproduce our results.
* It is not optimized in any way.

### Usage

Main class in kll.py
              
    $ python kll.py -h
    
    usage: kll.py [-h] [-k K] [-t {string,int,float}]
		optional arguments:
	      -h, --help            show this help message and exit
          -k K                  controls the number of elements in the sketch which is
                                at most 3k+log2(n). n is the length of the stream.
          -t {string,int,float}
                                defines the type of stream items, default="string"
                    
For convenience, the class StreamMaker is also included.
     
    $ python streamMaker.py -h
    
	usage: streamMaker.py [-h] [-n N] [-o {sorted,zoomin,zoomout,sqrt,random}]
	optional arguments:
        -h, --help            show this help message and exit
		-n N                  the number of generated elements
		-o {sorted,zoomin,zoomout,sqrt,random}
                       		  the order of the streamed integers.
              
### Example
Try the following:
	
	python streamMaker.py -n 1000 -o zoomin | python kll.py -k 32 -t int
	
Or, if you want to save the files and look at the input-output do this: 
	
	
	python streamMaker.py -n 1000 -o zoomin > numbers.txt
	cat numbers.txt | python kll.py -k 32 -t int > cdf.csv

You should get an approximate CDF of the input stream. The file cdf.csv should look something like this:
	
	0.016000	7
	0.032000	23
	0.048000	39
	0.064000	55
	0.080000	72
	.
	.
	.
	0.936000	923
	0.952000	940
	0.968000	956
	0.984000	973
	1.000000	989 

You can also try something (admittedly odd) like this: 
    
    man grep | python kll.py
    
This will give approximate quantiles of the lines in the grep man page where the order of lines is lexicographic.


### Plotting
This requires having gnuplot installed. On macs you can install like this:

	brew install gnuplot
	
Assume you created a cdf.csv file like this:

	python streamMaker.py -n 1000 -o random > numbers.txt
	cat numbers.txt | python kll.py -k 32 -t int > cdf.csv
	
You can than plot the approximate quantiles the sketch holds. A single dot is plotted for each item stored by the sketch.

	cat cdf.csv | gnuplot plot.gp > plot.eps; open plot.eps

You can then increase k and see that the plot aligns better along a straight diagonal line. Since the streams created by the stream maker are consecutive numbers 1,...,n a straight diagonal is the optimal result.

	cat numbers.txt | python kll.py -k 16 -t int | gnuplot plot.gp > plot16.eps; open plot16.eps
	cat numbers.txt | python kll.py -k 32 -t int | gnuplot plot.gp > plot32.eps; open plot32.eps
	cat numbers.txt | python kll.py -k 64 -t int | gnuplot plot.gp > plot64.eps; open plot64.eps

Keep in mind that larger values of k also increase the size of the sketch.

