

import unittest



class MyTestCase(unittest.TestCase):
    def test_my_first_test(self):
        self.assertEqual(1, 1)

    def test_my_second_test(self):
        self.assertEqual(2, 2)

if __name__ == '__main__':
    unittest.main()


