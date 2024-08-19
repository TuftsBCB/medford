import re
import pytest
from MEDFORD.objs.linereader import DetailStatics
from MEDFORD.objs.linereader import LineReader

# resources?
# https://github.com/rust-lang/regex/tree/master/tests
# https://github.com/BurntSushi/ripgrep/tree/master/tests

# Let's test some of these affronts to god I've written.
class TestTokenRegexStrings:
    def test_name_line(self) :
        major = "Major"
        test_str = f"@{major} asdf"
        res = re.search(f"{DetailStatics.major_minor_reg}", test_str)

        assert res is not None
        groups = res.groupdict()

        assert "major" in groups.keys()
        assert groups["major"] == major
        assert "minor" in groups.keys()
        assert groups["minor"] is None
    
    def test_no_noname_line(self) :
        major = "Major"
        test_str = f"@{major}"
        res = re.search(f"{DetailStatics.major_minor_reg}", test_str)

        assert res is None
    
    # TODO : decide how to handle this case. Technically failing later makes it easier to make a MFD validator error out of it.
    def test_no_noname_trailing_space_line(self) :
        major = "Major"
        test_str = f"@{major} "
        res = re.search(f"{DetailStatics.major_minor_reg}", test_str)

        assert res is not None

    def test_multilevel_name_line(self) :
        major = "Major_MajorTwo"
        test_str = f"@{major} asdf"
        res = re.search(f"{DetailStatics.major_minor_reg}", test_str)

        assert res is not None
        groups = res.groupdict()

        assert "major" in groups.keys()
        assert groups["major"] == major
        assert "minor" in groups.keys()
        assert groups["minor"] is None

    def test_detail_line(self) :
        major = "Major"
        minor = "minor"
        test_str = f"@{major}-{minor} asdf"
        res = re.search(f"{DetailStatics.major_minor_reg}", test_str)

        assert res is not None
        groups = res.groupdict()

        assert "major" in groups.keys()
        assert groups["major"] == major
        assert "minor" in groups.keys()
        assert groups["minor"] == minor
    
    def test_no_multilevel_minor_line(self) :
        major = "Major"
        minor = "minor_minortwo"
        test_str = f"@{major}-{minor} asdf"
        res = re.search(f"{DetailStatics.major_minor_reg}", test_str)

        assert res is None
    
    def test_no_multi_minor_line(self) :
        major = "Major"
        minor = "minor-minortwo"
        test_str = f"@{major}-{minor} asdf"
        res = re.search(f"{DetailStatics.major_minor_reg}", test_str)

        assert res is None

@pytest.mark.parametrize(
    ("macroname"),
    [
        ("macroname"),
        ("MacroName"),
        ("Macro_Name"),
        ("MacroName123"),
        ("Macro_Name_123"),
    ]
)
class TestStandardMacroRegexStrings:
    def test_open_macro(self, macroname:str) :
        test_str = f"`@{macroname}"

        res = re.search(f"{DetailStatics.macro_use_regex}", test_str)
        assert res is not None
        
        groups = res.groupdict()
        assert "r1" in groups.keys()
        assert "r2" in groups.keys()
        assert "mname_closed" in groups.keys()
        assert "mname_open" in groups.keys()
        assert groups["r1"] is None
        assert groups["mname_closed"] is None
        assert groups["r2"] == test_str
        assert groups["mname_open"] == macroname

    def test_closed_macro(self, macroname:str) :
        test_str = fr"`@{{{macroname}}}"

        res = re.search(f"{DetailStatics.macro_use_regex}", test_str)
        assert res is not None
        
        groups = res.groupdict()
        assert "r1" in groups.keys()
        assert "r2" in groups.keys()
        assert "mname_closed" in groups.keys()
        assert "mname_open" in groups.keys()
        assert groups["r1"] == test_str
        assert groups["mname_closed"] == macroname
        assert groups["r2"] is None
        assert groups["mname_open"] is None

class TestNoMacrosWithSpaces:
    def test_open_macro(self) :
        test_str = "`@Macro Name"
        
        res = re.search(f"{DetailStatics.macro_use_regex}", test_str)
        assert res is not None

        groups = res.groupdict()
        assert "r2" in groups.keys()
        assert "mname_open" in groups.keys()
        assert groups["mname_open"] == "Macro"

    def test_open_macro_two(self) :
        test_str = "`@Macro Name Two"
        
        res = re.search(f"{DetailStatics.macro_use_regex}", test_str)
        assert res is not None

        groups = res.groupdict()
        assert "r2" in groups.keys()
        assert "mname_open" in groups.keys()
        assert groups["mname_open"] == "Macro"

    def test_open_macro_three(self) :
        test_str = "three `@Macro Name Two"
        
        res = re.search(f"{DetailStatics.macro_use_regex}", test_str)
        assert res is not None

        groups = res.groupdict()
        assert "r2" in groups.keys()
        assert "mname_open" in groups.keys()
        assert groups["mname_open"] == "Macro"
    
    def test_closed_macro(self) :
        test_str = "`@{Macro Name}"
        
        res = re.search(f"{DetailStatics.macro_use_regex}", test_str)
        assert res is None

class TestReferenceRegex:
    def test_case_1(self) :
        # don't bother testing spaces at the end of the test_str,
        #   regex doesn't care about it, it'll be something that
        #   the linereader object creation stuff deals with
        test_str = "@Major-minor @RefMajor ref major name"

        res = re.search(DetailStatics.ref_use_regex,test_str)
        assert res is not None

        groups = res.groupdict()
        assert "ref_major" in groups.keys()
        assert groups["ref_major"] is not None
        assert groups["ref_major"] == "RefMajor"

        assert "ref_name" in groups.keys()
        assert groups["ref_name"] is not None
        assert groups["ref_name"] == "ref major name"
        
    def test_case_noname(self) :
        # test that it still captures if there's no name, so we can throw a smart error
        test_str = "@Major-minor @RefMajor"

        res = re.search(DetailStatics.ref_use_regex, test_str)
        assert res is not None

        groups = res.groupdict()
        assert "ref_major" in groups.keys()
        assert "ref_name" in groups.keys()
        assert groups["ref_major"] == "RefMajor"
        assert groups["ref_name"] is None

    # strange edge case:
    # @Major-minor
    #   @ReferenceMajor reference_minor
    # Throw an error? Might have to manually code some smart logic to catch this
    # and force references to be in 1 line

class TestReferenceMethods:
    import mfdglobals
    def test_is_reference_method_1(self) :
        test_str = "@Major-minor @RefMajor ref major name"
        is_ref, ref_err = LineReader.is_reference_line(test_str, 0)
        assert is_ref
        assert ref_err is None

    def test_is_reference_method_no_name(self) :
        from MEDFORD.submodules.mfdvalidator.errors import MissingReferenceName

        # A reference with no name should still be recognized as a reference
        #   (so that it doesn't get treated as a new Detail), but should
        #   add an error to the validator to show to the user later.
        self.mfdglobals.init()
        test_str = "@Major-minor @RefMajor"

        is_ref, ref_err = LineReader.is_reference_line(test_str, 0)
        assert is_ref is True
        assert isinstance(ref_err, MissingReferenceName)