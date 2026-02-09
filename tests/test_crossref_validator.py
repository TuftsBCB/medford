"""Tests for cross-reference validation (stage 3)."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from MEDFORD import mfdglobals
from MEDFORD.objs.crossref_validator import CrossRefValidator
from MEDFORD.objs.linecollections import Block, Detail
from MEDFORD.objs.linereader import LineReader, Line
from MEDFORD.objs.linecollector import LineCollector
from MEDFORD.submodules.mfdvalidator.errors import MissingCrossReferenceError


def lines_to_named_blocks(lines: list[str]) -> dict:
    line_objs = []
    for idx, line in enumerate(lines):
        obj = LineReader.process_line(line, idx)
        if obj is not None:
            line_objs.append(obj)

    lc = LineCollector(line_objs)
    return lc.named_blocks


class TestCrossRefValidator:
    def setup_method(self):
        mfdglobals.ForceNewValidator()

    def test_valid_contributor_reference(self):
        lines = [
            "@Contributor John Smith",
            "@Contributor-Email john@example.com",
            "@Paper My Paper",
            "@Paper-Contributor John Smith",
        ]

        named_blocks = lines_to_named_blocks(lines)
        validator = CrossRefValidator(named_blocks)
        result = validator.validate()

        assert result is True
        assert not mfdglobals.validator.has_syntax_err()

    def test_invalid_contributor_reference(self):
        lines = [
            "@Paper My Paper",
            "@Paper-Contributor Jane Doe",
        ]

        named_blocks = lines_to_named_blocks(lines)
        validator = CrossRefValidator(named_blocks)
        result = validator.validate()

        assert result is False
        assert mfdglobals.validator.has_syntax_err()

    def test_local_override_no_error(self):
        # This test simulates a block that has local contributor details
        # In practice, the MEDFORD parser may not support @Paper-Contributor-Email syntax
        # but the validator logic handles it if those minor tokens exist
        validator = CrossRefValidator({})

        # Test the _has_local_subtags method directly
        minor_tokens = ["Contributor", "Contributor-Email"]
        result = validator._has_local_subtags(minor_tokens, "Contributor")

        assert result is True

    def test_valid_institution_reference(self):
        lines = [
            "@Institution Tufts",
            "@Institution-Address Medford, MA",
            "@Paper My Paper",
            "@Paper-Institution Tufts",
        ]

        named_blocks = lines_to_named_blocks(lines)
        validator = CrossRefValidator(named_blocks)
        result = validator.validate()

        assert result is True
        assert not mfdglobals.validator.has_syntax_err()

    def test_invalid_institution_reference(self):
        lines = [
            "@Paper My Paper",
            "@Paper-Institution Unknown University",
        ]

        named_blocks = lines_to_named_blocks(lines)
        validator = CrossRefValidator(named_blocks)
        result = validator.validate()

        assert result is False
        assert mfdglobals.validator.has_syntax_err()

    def test_institution_local_override(self):
        validator = CrossRefValidator({})

        # Test the _has_local_subtags method directly
        minor_tokens = ["Institution", "Institution-Address"]
        result = validator._has_local_subtags(minor_tokens, "Institution")

        assert result is True

    def test_skip_contributor_block_itself(self):
        lines = [
            "@Contributor John Smith",
            "@Contributor-Email john@example.com",
        ]

        named_blocks = lines_to_named_blocks(lines)
        validator = CrossRefValidator(named_blocks)
        result = validator.validate()

        assert result is True
        assert not mfdglobals.validator.has_syntax_err()

    def test_multiple_references_some_invalid(self):
        lines = [
            "@Contributor John Smith",
            "@Paper Paper 1",
            "@Paper-Contributor John Smith",
            "@Paper Paper 2",
            "@Paper-Contributor Jane Doe",
        ]

        named_blocks = lines_to_named_blocks(lines)
        validator = CrossRefValidator(named_blocks)
        result = validator.validate()

        assert result is False
        assert mfdglobals.validator.has_syntax_err()

    def test_collect_major_tags(self):
        lines = [
            "@Contributor John Smith",
            "@Contributor Jane Doe",
            "@Institution Tufts",
        ]

        named_blocks = lines_to_named_blocks(lines)
        validator = CrossRefValidator(named_blocks)
        validator._collect_major_tags()

        assert validator.defined_contributors == {"John Smith", "Jane Doe"}
        assert validator.defined_institutions == {"Tufts"}

    def test_has_local_subtags_true(self):
        validator = CrossRefValidator({})

        minor_tokens = ["Contributor", "Contributor-Email", "Link"]
        result = validator._has_local_subtags(minor_tokens, "Contributor")

        assert result is True

    def test_has_local_subtags_false(self):
        validator = CrossRefValidator({})

        minor_tokens = ["Contributor", "Link", "DOI"]
        result = validator._has_local_subtags(minor_tokens, "Contributor")

        assert result is False

    def test_empty_named_blocks(self):
        named_blocks = {}
        validator = CrossRefValidator(named_blocks)
        result = validator.validate()

        assert result is True
        assert not mfdglobals.validator.has_syntax_err()

    def test_no_minor_tokens_block(self):
        lines = [
            "@Paper My Paper",
        ]

        named_blocks = lines_to_named_blocks(lines)
        validator = CrossRefValidator(named_blocks)
        result = validator.validate()

        assert result is True
        assert not mfdglobals.validator.has_syntax_err()


class TestMissingCrossReferenceError:

    def setup_method(self):
        mfdglobals.ForceNewValidator()

    def test_error_message_with_available_names(self):
        lines = [
            "@Paper My Paper",
            "@Paper-Contributor Unknown Person",
        ]

        line_objs = []
        for idx, line in enumerate(lines):
            obj = LineReader.process_line(line, idx)
            if obj is not None:
                line_objs.append(obj)

        lc = LineCollector(line_objs)

        paper_block = lc.named_blocks["Paper"]["My Paper"]
        detail = paper_block.minor_tokens[0][1]  # (minor_token_name, detail)

        error = MissingCrossReferenceError(
            detail, "Contributor", "Unknown Person", ["John Smith", "Jane Doe"]
        )

        assert "Line 1" in error.msg
        assert "@Paper-Contributor" in error.msg
        assert "Unknown Person" in error.msg
        assert "@Contributor" in error.msg
        assert "John Smith" in error.helpmsg
        assert "Jane Doe" in error.helpmsg

    def test_error_message_without_available_names(self):
        lines = [
            "@Paper My Paper",
            "@Paper-Contributor Unknown Person",
        ]

        line_objs = []
        for idx, line in enumerate(lines):
            obj = LineReader.process_line(line, idx)
            if obj is not None:
                line_objs.append(obj)

        lc = LineCollector(line_objs)

        # Get the detail from the block
        paper_block = lc.named_blocks["Paper"]["My Paper"]
        detail = paper_block.minor_tokens[0][1]

        error = MissingCrossReferenceError(
            detail, "Contributor", "Unknown Person", []
        )

        assert "No @Contributor blocks are defined" in error.helpmsg

    def test_error_lineno_methods(self):
        lines = [
            "@Paper My Paper",
            "@Paper-Contributor Unknown Person",
        ]

        line_objs = []
        for idx, line in enumerate(lines):
            obj = LineReader.process_line(line, idx)
            if obj is not None:
                line_objs.append(obj)

        lc = LineCollector(line_objs)

        # Get the detail from the block
        paper_block = lc.named_blocks["Paper"]["My Paper"]
        detail = paper_block.minor_tokens[0][1]

        error = MissingCrossReferenceError(
            detail, "Contributor", "Unknown Person", []
        )

        assert error.get_head_lineno() == 1
        assert error.get_lineno_range() == (1, 1)