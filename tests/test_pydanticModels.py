import unittest

from MEDFORD.medford_models import *

class TestModelMethods(unittest.TestCase) :
    def test_freeform_simple(self) :
        # Ensures we properly retain all fields in a simple freeform tag.
        freeform_example_dict = {'desc':'05-22', 'Note':"Hello World"}
        t = Freeform(**freeform_example_dict)
        self.assertEqual(t.dict()['Note'], "Hello World")
        self.assertEqual(t.dict()['desc'], '05-22')

    def test_freeform_complex(self):
        # Now does it still work if we use freeform as a prefix?
        freeform_example_dict = {'Date':[{'desc':'05-22', 'Note': "Hello World"}]}
        t = Freeform(**freeform_example_dict)
        self.assertIn('Date', t.dict())
        self.assertEqual(t.dict()['Date'][0]['desc'], '05-22')
        self.assertEqual(t.dict()['Date'][0]['Note'], 'Hello World')

if __name__ == '__main__':
    unittest.main()