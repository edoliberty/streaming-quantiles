import sys
import numpy as no

from gde import GDE

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
    parser.add_argument('-q', '--queries', type=str)

    args = parser.parse_args()

    if(args.k < 2 or args.dimension < 1):
        raise ValueError("baaaaad inputs :)")
    

    queries = []
    with open(args.queries) as queries_file:
        for line in queries_file:
            try:
                query = np.array(json.loads(line))
                assert(len(query) == args.dimension)
            except:
                raise ValueError(f"Could not parse json of dimension missmatch for input line \n{line}")

            queries.append(query)
    
    gde = GDE(args.k, args.dimension)

    densities = np.zeros(len(queries))

    for line in sys.stdin:
        try:
            vector = np.array(json.loads(line))
            assert(len(vector) == args.dimension)
        except:
            raise ValueError(f"Could not parse json of dimension missmatch for input line \n{line}")

        for i, query in enumerate(queries):
            densities[i] += gde.kernel(vector, query)

        gde.update(vector)
        
    approx_densities = np.array([gde.query(query) for query in queries])
    
    for i, (density, approx_density) in enumerate(zip(densities, approx_densities)):
        print(i, density, approx_density)



    