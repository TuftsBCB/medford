import pytest
from MEDFORD.objs import lines

class TestReferenceLineCreation() :
    def test_basic(self) :
        test_str = "@Major-minor @RefMajor ref name"
        test_majors = ["Major"]
        test_minor = "minor"

        test_ref_majors = ["RefMajor"]
        test_ref_name = "ref name"

        test_poss_inline = []

        test_line = lines.ReferenceLine(0, test_str, test_majors, test_minor, test_ref_majors, test_ref_name, test_poss_inline)
        assert test_line is not None
        # test ReferenceLine specific functionality
        assert test_line.referenced_majors == ["RefMajor"]
        assert test_line.referenced_name == "ref name"

        # test NovelDetailLine functionality
        assert test_line.major_tokens == ["Major"]
        assert test_line.minor_token == "minor"
        assert test_line.raw_content == "@RefMajor ref name"

        assert not test_line.has_inline
        assert not test_line.has_macros
        assert not test_line.has_tex

        # TODO : returns None? Why does this fxn exist again
        #assert test_line._get_raw_content_offset() == len(test_majors[0]) + 1 + len(test_minor) + 1


    def test_has_inline(self) :
        from MEDFORD.objs.linereader import LineReader
        test_header = "@Major-minor"
        test_content = "@RefMajor ref name # inline comment"
        test_str = test_header + " " + test_content
        test_majors = ["Major"]
        test_minor = "minor"

        test_ref_majors = ["RefMajor"]
        test_ref_name = "ref name"

        # TODO : don't use a different fxn here somehow?
        test_poss_inline = LineReader.find_possible_inline_comments(test_str)

        test_line = lines.ReferenceLine(0, test_str, test_majors, test_minor, test_ref_majors, test_ref_name, test_poss_inline)
        assert test_line is not None
        # test ReferenceLine specific functionality
        assert test_line.referenced_majors == ["RefMajor"]
        assert test_line.referenced_name == "ref name"

        # test NovelDetailLine functionality
        assert test_line.major_tokens == ["Major"]
        assert test_line.minor_token == "minor"
        assert test_line.raw_content == "@RefMajor ref name"

        assert test_line.has_inline
        assert test_line.get_content({}) == test_content.split("#")[0].strip()
        assert not test_line.has_macros
        assert not test_line.has_tex