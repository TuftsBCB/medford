import unittest

from helpers_file import *

class TestFilenameMethods(unittest.TestCase) :
    def test_generated_name_wslash(self) :
        dirname = "test/"
        filename = "file.txt"
        output = generate_output_name(dirname, filename)
        self.assertEqual("test/file.txt", output)
    
    def test_generated_name_woslash(self) :
        dirname = "test"
        filename = "file.txt"
        output = generate_output_name(dirname, filename)
        self.assertEqual("test/file.txt", output)

    def test_valid_validate_bagit(self) :
        self.assertTrue(valid_filename_bagit("testFile.TxT")[0])

    def test_invalid_space_validate_bagit(self) :
        self.assertFalse(valid_filename_bagit("test File.TxT")[0])

    def test_invalid_percent_validate_bagit(self) :
        self.assertFalse(valid_filename_bagit("test%File.TxT")[0])

    def test_invalid_newline_validate_bagit(self) :
        self.assertFalse(valid_filename_bagit("test\nFile.TxT")[0])

    def test_invalid_empty_validate_bagit(self) :
        self.assertFalse(valid_filename_bagit("")[0])

if __name__ == '__main__':
    unittest.main()