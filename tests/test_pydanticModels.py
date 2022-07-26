import pytest

from MEDFORD.medford_models import *

def test_freeform_simple() :
    # Ensures we properly retain all fields in a simple freeform tag.
    freeform_example_dict = {'desc':'05-22', 'Note':"Hello World"}
    t = Freeform(**freeform_example_dict)
    assert t.dict()['Note'] == "Hello World"
    assert t.dict()['desc'] == '05-22'

def test_freeform_complex():
    # Now does it still work if we use freeform as a prefix?
    freeform_example_dict = {'Date':[{'desc':'05-22', 'Note': "Hello World"}]}
    t = Freeform(**freeform_example_dict)
    assert 'Date' in t.dict().keys()
    assert t.dict()['Date'][0]['desc'] == '05-22'
    assert t.dict()['Date'][0]['Note'] == 'Hello World'
