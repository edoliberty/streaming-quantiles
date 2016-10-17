set terminal postscript eps size 11.0,7.0 enhanced color font 'Helvetica,20';
set ylabel "Approximated quantile";
set xlabel "Value";
plot '<cat' using 2:1 pt 7 ps 3;