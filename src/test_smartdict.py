import unittest

from medford_smartdict import *
from medford_token import *
import os

class TestSmartDictMethods(unittest.TestCase) :
    def test_generate_simple_token(self) :
        self.assertTrue(True)
    
    def test_generate_complex_token(self) :
        example_string = "@Freeform-Date 05-22\n" +\
                            "@Freeform-Date-Note Hello World"
        with open("tmp.txt", 'w') as f:
            f.write(example_string)
        tokens = Token.generate_tokens("tmp.txt")
        os.remove("tmp.txt")
        for token in tokens:
            print(token)
        
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()