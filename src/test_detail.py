import unittest

from medford_detail import *

class TestDetailMethods(unittest.TestCase) :
    def setUp(self) :
        detail._clear_cache()

    def test_detail_simple(self) :
        example_line = "@Date 02/24"
        is_detail, is_new, d = detail.FromLine(example_line, -1, None)
        self.assertListEqual(d.Major_Tokens, ["Date"])
        self.assertEqual(d.Minor_Token, "desc")
        self.assertEqual(d.Data, "02/24")

    def test_detail_ordinary(self) :
        example_line = "@Date-Note Samples Obtained"
        is_detail, is_new, d = detail.FromLine(example_line, -1, None)
        self.assertListEqual(d.Major_Tokens, ["Date"])
        self.assertEqual(d.Minor_Token, "Note")
        self.assertEqual(d.Data, "Samples Obtained")
    
    def test_detail_2_level_recursive(self) :
        example_line = "@Freeform_Date-Note Samples Obtained"
        is_detail, is_new, d = detail.FromLine(example_line, -1, None)
        self.assertListEqual(d.Major_Tokens, ["Freeform","Date"])
        self.assertEqual(d.Minor_Token, "Note")
        self.assertEqual(d.Data, "Samples Obtained")
    
    def test_recognizes_template(self) :
        example_line = "@Date-Note [...]"
        with self.assertRaises(ValueError) :
            detail.FromLine(example_line, -1, None)

    # Tests for Macro functionality.
    def test_add_macro(self) :
        example_line = "`@macro_name macro body"
        is_detail, is_new, d = detail.FromLine(example_line, -1, None)
        self.assertListEqual(list(detail.macro_dictionary.keys()), ["macro_name"])

    def test_add_multiple_macros(self) :
        example_line = "`@macro_name macro body"
        example_line_2 = "`@macro_name_2 macro body"
        detail.FromLine(example_line, -1, None)
        detail.FromLine(example_line_2, -1, None)
        self.assertListEqual(list(detail.macro_dictionary.keys()), ["macro_name", "macro_name_2"])

    def test_add_same_macro_name(self) :
        example_line = "`@macro_name macro body"
        example_line_2 = "`@macro_name macro body"
        with self.assertRaises(ValueError) :
            detail.FromLine(example_line, -1, None)
            detail.FromLine(example_line_2, -1, None)
    
    def test_correctly_substitutes_macro(self) :
        example_line = "`@macro_name macro body"
        example_line_2 = "@major-minor text `@macro_name"
        detail.FromLine(example_line, -1, None)
        _, _, d = detail.FromLine(example_line_2, -1, None)
        self.assertEqual(d.Data, "text macro body")

    def test_correctly_substitutes_macro_with_stuff_after(self) :
        example_line = "`@macro_name macro body"
        example_line_2 = "@major-minor text `@macro_name asdf asdf asdf"
        detail.FromLine(example_line, -1, None)
        _, _, d = detail.FromLine(example_line_2, -1, None)
        self.assertEqual(d.Data, "text macro body asdf asdf asdf")

if __name__ == '__main__':
    unittest.main()