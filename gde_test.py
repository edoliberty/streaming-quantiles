import unittest
import numpy as np

from gde import GDE


class TestGDE(unittest.TestCase):
    
    def test_one_update(self):
        k = 10
        gde = GDE(k, 3);
        gde.update([0, 0, 0]);
        self.assertTrue(gde.query([0, 0, 0]) == 1);
        self.assertTrue(gde.query([0.01, 0.01, 0.01]) > 0.95);
        self.assertTrue(gde.query([1, 1, 1]) < 0.05);


    def test_to_string(self):
        gde1 = GDE(10, 4);
        gde1.update([0, 0, 0, 0.0]);
        gde1.update([-1.5, 123.4, 1.4e12,-5]);
        gde1_serialized = gde1.to_string()

        gde2 = GDE();
        gde2.from_string(gde1_serialized)
        self.assertTrue(gde1.d == gde2.d)
        self.assertTrue(gde1.k == gde2.k)
        self.assertTrue(gde1.n == gde2.n)
        self.assertTrue(gde1.size == gde2.size)
        self.assertTrue(gde1.max_size == gde2.max_size)

        for c1, c2 in zip(gde1.compactors,gde2.compactors):
            for v1, v2 in zip(c1, c2):
                self.assertTrue(np.all(np.isclose(v1, v2)))


    def test_merge(self):
        gde1 = GDE();
        gde1.update([0, 0, 0, 0.0]);
        gde1.update([-1.5, 123.4, 1.4e12,-5]);
        
        gde2 = GDE();
        gde2.update([0.66, -10, 123, 0.0]);
        
        gde1.merge(gde2)

        self.assertTrue(gde1.n == 3)
        self.assertTrue(gde1.size == 3)


    def test_merge_size(self):
        k, d, n  = 17, 25, 200
        gde1 = GDE(k, d);
        gde2 = GDE(k, d);
        for i in range(int(n/2)):
            gde1.update(np.random.randn(d))
            gde2.update(np.random.randn(d))
    
        gde1.merge(gde2)
        self.assertTrue(gde1.size <= n*np.log(n/k))

    def test_size(self):
        k, d, n  = 171, 13, 2000
        gde = GDE(k, d);
        for i in range(n):
            gde.update(np.random.randn(d))
        self.assertTrue(gde.size <= n*np.log(n/k))

if __name__ == '__main__':
    unittest.main()    


    



    