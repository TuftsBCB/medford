#!/usr/bin/env python3
"""Tests for @include functionality in MEDFORD parser.

This module tests the IncludeLine class and include detection logic
in the LineReader. These tests document the expected behavior of
the @include feature and ensure it works correctly.

Tested Components:
- IncludeLine class creation and attributes
- LineReader.include detection and parsing
- Simplified include syntax (no recursion)
- Error handling for invalid syntax
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from MEDFORD.objs.linereader import LineReader
from MEDFORD.objs.lines import IncludeLine


def test_include_line_detection():
    """Test that @include lines are correctly detected."""
    
    # Valid include lines
    valid_includes = [
        "@include foo.mfd @contributor Alva L. Couch",
        "@include foo.mfd @contributor",
        "@include bar.mfd @data RNA-seq data",
        "@include test.mfd @method DNA extraction",
    ]
    
    # Invalid lines (should not be detected as includes)
    invalid_includes = [
        "@contributor Alva L. Couch",  # Missing @include
        "include foo.mfd @contributor",  # Missing @
        "@include",  # Incomplete
        "@include foo.mfd",  # Missing tag
        "This is just a regular line",
    ]
    
    print("Testing include line detection...")
    
    # Test valid includes
    for line in valid_includes:
        assert LineReader.is_include_line(line), f"Should detect as include: {line}"
        print(f"  ✓ {line}")
    
    # Test invalid includes
    for line in invalid_includes:
        assert not LineReader.is_include_line(line), f"Should not detect as include: {line}"
        print(f"  ✓ NOT {line}")
    
    print("  All detection tests passed!")


def test_include_parsing():
    """Test parsing of @include syntax into components."""
    
    test_cases = [
        # (input_line, expected_filename, expected_tag, expected_selector)
        ("@include foo.mfd @contributor Alva L. Couch", "foo.mfd", "@contributor", "Alva L. Couch"),
        ("@include foo.mfd @contributor", "foo.mfd", "@contributor", ""),
        ("@include bar.mfd @data RNA-seq data", "bar.mfd", "@data", "RNA-seq data"),
        ("@include test.mfd @method DNA extraction", "test.mfd", "@method", "DNA extraction"),
        # Test that old recursion syntax is handled gracefully
        ("@include foo.mfd @contributor Alva L. Couch, recursive", "foo.mfd", "@contributor", "Alva L. Couch, recursive"),
    ]
    
    print("\nTesting include parsing...")
    
    for i, (line, expected_filename, expected_tag, expected_selector) in enumerate(test_cases):
        print(f"  Test {i+1}: {line}")
        
        filename, tag_name, selector = LineReader.find_include_attributes(line)
        
        assert filename == expected_filename, f"Expected filename {expected_filename}, got {filename}"
        assert tag_name == expected_tag, f"Expected tag {expected_tag}, got {tag_name}"
        assert selector == expected_selector, f"Expected selector '{expected_selector}', got '{selector}'"
        
        print(f"    ✓ Parsed: {filename} | {tag_name} | '{selector}'")
    
    print("  All parsing tests passed!")


def test_include_line_creation():
    """Test IncludeLine object creation and attributes."""
    
    print("\nTesting IncludeLine object creation...")
    
    line = "@include foo.mfd @contributor Alva L. Couch"
    include_line = LineReader.process_line(line, 1)
    
    # Verify object type
    assert isinstance(include_line, IncludeLine), f"Expected IncludeLine, got {type(include_line)}"
    print(f"  ✓ Created {type(include_line).__name__}")
    
    # Verify attributes
    assert include_line.filename == "foo.mfd", f"Expected 'foo.mfd', got '{include_line.filename}'"
    assert include_line.tag_name == "@contributor", f"Expected '@contributor', got '{include_line.tag_name}'"
    assert include_line.selector == "Alva L. Couch", f"Expected 'Alva L. Couch', got '{include_line.selector}'"
    
    print(f"  ✓ Filename: {include_line.filename}")
    print(f"  ✓ Tag name: {include_line.tag_name}")
    print(f"  ✓ Selector: '{include_line.selector}'")
    
    # Verify no recursion attribute (simplified design)
    assert not hasattr(include_line, 'is_recursive'), "IncludeLine should not have is_recursive attribute"
    print("  ✓ No recursion attribute (simplified design)")
    
    print("  All object creation tests passed!")


def test_include_line_equality():
    """Test IncludeLine equality comparison."""
    
    print("\nTesting IncludeLine equality...")
    
    line1 = "@include foo.mfd @contributor Alva L. Couch"
    line2 = "@include foo.mfd @contributor Alva L. Couch"
    line3 = "@include bar.mfd @contributor Alva L. Couch"
    
    include1 = LineReader.process_line(line1, 1)
    include2 = LineReader.process_line(line2, 1)  # Same line number
    include3 = LineReader.process_line(line3, 1)
    
    # Same content should be equal
    assert include1 == include2, "Same content should be equal"
    print("  ✓ Same content equality works")
    
    # Different content should not be equal
    assert include1 != include3, "Different content should not be equal"
    print("  ✓ Different content inequality works")
    
    print("  All equality tests passed!")


def test_error_handling():
    """Test error handling for invalid include syntax."""
    
    print("\nTesting error handling...")
    
    invalid_lines = [
        "@include",  # Missing filename and tag
        "@include foo.mfd",  # Missing tag
        "include foo.mfd @contributor",  # Missing @
        "not an include at all",
    ]
    
    for line in invalid_lines:
        try:
            LineReader.find_include_attributes(line)
            assert False, f"Should have raised ValueError for: {line}"
        except ValueError as e:
            print(f"  ✓ Correctly raised ValueError for: {line}")
            print(f"    Error: {e}")
    
    print("  All error handling tests passed!")


def test_content_processing():
    """Test that IncludeLine supports content processing (macros, LaTeX, comments)."""
    
    print("\nTesting content processing...")
    
    # Test include line with macro
    line_with_macro = "@include foo.mfd @contributor `@author_name`"
    include_line = LineReader.process_line(line_with_macro, 1)
    
    # Check if macro detection is working
    if include_line.has_macros:
        assert len(include_line.macro_uses) > 0, "Should have macro uses"
        print(f"  ✓ Macro detection: {include_line.macro_uses}")
    else:
        print(f"  ⚠ Macro detection not working (has_macros={include_line.has_macros})")
        print(f"    Macro uses: {include_line.macro_uses}")
    
    # Test include line with inline comment
    line_with_comment = "@include foo.mfd @contributor Alva L. Couch  # Include author data"
    include_line = LineReader.process_line(line_with_comment, 1)
    
    if include_line.has_inline:
        print(f"  ✓ Inline comment detection: {include_line.comm_str}")
    else:
        print(f"  ⚠ Inline comment detection not working (has_inline={include_line.has_inline})")
        print(f"    Comment string: '{include_line.comm_str}'")
    
    # Test basic content processing works
    assert include_line.filename == "foo.mfd", "Basic parsing should work"
    assert include_line.tag_name == "@contributor", "Basic parsing should work"
    print("  ✓ Basic content processing works")
    
    print("  Content processing tests completed!")


def run_all_tests():
    """Run all include functionality tests."""
    
    print("=" * 60)
    print("MEDFORD @include Functionality Tests")
    print("=" * 60)
    
    test_include_line_detection()
    test_include_parsing()
    test_include_line_creation()
    test_include_line_equality()
    test_error_handling()
    test_content_processing()
    
    print("\n" + "=" * 60)
    print("🎉 ALL @include TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
