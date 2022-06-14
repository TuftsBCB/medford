import unittest

from MEDFORD.medford import *

class TestModelMethods(unittest.TestCase) :
    def test_pdam_cunning(self) :
        runMedford("samples/pdam_cunning.MFD", True, MFDMode.OTHER)
        self.assertTrue(True)
    
    def test_freeform(self) :
        runMedford("samples/made_up_Freeform.MFD", True, MFDMode.OTHER)
        self.assertTrue(True)
    
    def test_bcodmo(self) :
        runMedford("samples/made_up_BCODMO.MFD", True, MFDMode.BCODMO)
        self.assertTrue(True)
    
    def test_bagit(self) :
        runMedford("samples/made_up_BAGIT.MFD", True, MFDMode.BAGIT)
        self.assertTrue(True)
    
if __name__ == '__main__':
    unittest.main()