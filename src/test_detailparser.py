import unittest

from medford_detail import *
from medford_detailparser import *

class TestDetailMethods(unittest.TestCase) :
    def test_single_line(self) :
        line = "@Date 02/24"
        d = detail.FromLine(line, -1)
        p = detailparser([d])
        out_dict = p.export()
        self.assertListEqual(list(out_dict.keys()), ["Date"])
        self.assertEqual(len(out_dict["Date"]), 1) # There should only be one full Date object

        self.assertListEqual(list(out_dict["Date"][0].keys()), ["desc"])
        self.assertEqual(len(out_dict["Date"][0]["desc"]), 1) # Only should be 1 desc line

        self.assertEqual(out_dict["Date"][0]["desc"][0], "02/24")

    def test_multiple_details_one_instance(self):
        lines = "@Date 02/24\n@Date-note Hello World"
        ds = [detail.FromLine(line, -1) for line in lines.split("\n")]
        p = detailparser(ds)
        out_dict = p.export()
        self.assertListEqual(list(out_dict.keys()), ["Date"])
        self.assertEqual(len(out_dict["Date"]), 1) # There should only be one full Date object

        self.assertListEqual(list(out_dict["Date"][0].keys()), ["desc","note"])
        self.assertEqual(len(out_dict["Date"][0]["desc"]), 1) # Only should be 1 desc line
        self.assertEqual(len(out_dict["Date"][0]["note"]), 1) # Only should be 1 note line

        self.assertEqual(out_dict["Date"][0]["desc"][0], "02/24")
        self.assertEqual(out_dict["Date"][0]["note"][0], "Hello World")

    def test_multiple_notes_one_instance(self):
        lines = "@Date 02/24\n@Date-note Hello World\n@Date-note 42"
        ds = [detail.FromLine(line, -1) for line in lines.split("\n")]
        p = detailparser(ds)
        out_dict = p.export()
        self.assertListEqual(list(out_dict["Date"][0].keys()), ["desc","note"])
        self.assertEqual(len(out_dict["Date"][0]["note"]), 2) # Should be 2 note lines

        self.assertEqual(out_dict["Date"][0]["desc"][0], "02/24")
        self.assertEqual(out_dict["Date"][0]["note"][0], "Hello World")
        self.assertEqual(out_dict["Date"][0]["note"][1], "42")

if __name__ == '__main__':
    unittest.main()