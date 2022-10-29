import sys
import unittest
from gde import GDE

class TestGDE(unittest.TestCase):
    def test_one_update(self):
        k = 10
        gde = GDE(k, 3);
        gde.update([0, 0, 0]);
        self.assertTrue(gde.query([0, 0, 0]) == 1);
        self.assertTrue(gde.query([0.01, 0.01, 0.01]) > 0.95);
        self.assertTrue(gde.query([1, 1, 1]) < 0.05);

if __name__ == '__main__':
    unittest.main()    


    



    