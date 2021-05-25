import unittest

from medford_detail import *

class TestDetailMethods(unittest.TestCase) :
    def test_detail_simple(self) :
        example_line = "@Date 02/24"
        d = detail.FromLine(example_line, -1)
        self.assertListEqual(d.Major_Tokens, ["Date"])
        self.assertEqual(d.Minor_Token, "desc")
        self.assertEqual(d.Data, "02/24")

    def test_detail_ordinary(self) :
        example_line = "@Date-Note Samples Obtained"
        d = detail.FromLine(example_line, -1)
        self.assertListEqual(d.Major_Tokens, ["Date"])
        self.assertEqual(d.Minor_Token, "Note")
        self.assertEqual(d.Data, "Samples Obtained")
    
    def test_detail_2_level_recursive(self) :
        example_line = "@Freeform_Date-Note Samples Obtained"
        d = detail.FromLine(example_line, -1)
        self.assertListEqual(d.Major_Tokens, ["Freeform","Date"])
        self.assertEqual(d.Minor_Token, "Note")
        self.assertEqual(d.Data, "Samples Obtained")

if __name__ == '__main__':
    unittest.main()