"""
Integration tests for @include functionality.

Tests the complete include pipeline from parsing to JSON output.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from typing import List

from MEDFORD.objs.linereader import LineReader as LR
from MEDFORD.objs.includeCollector import IncludeCollector
from MEDFORD.objs.lines import IncludeLine
from MEDFORD import MFD, ParserMode, OutputMode


class TestIncludeIntegration:
    """Integration tests for @include functionality."""
    
    def setup_method(self, test_method):
        """Set up test fixtures before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_dir = Path(self.temp_dir)
    
    def teardown_method(self, test_method):
        """Clean up test fixtures after each test."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, filename: str, content: str):
        """Helper to create test .mfd files."""
        filepath = self.base_dir / filename
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    def test_include_collector_basic(self):
        """Test basic IncludeCollector functionality."""
        source_content = """@Contributor Alice Smith
@Contributor-Email alice@example.com

@Contributor Bob Jones
@Contributor-Email bob@example.com"""
        
        source_file = self.create_test_file("source.mfd", source_content)
        
        include_line = IncludeLine(
            1, "@include source.mfd @Contributor Alice Smith",
            "source.mfd", "@Contributor", "Alice Smith",
            [], [], []
        )
        
        collector = IncludeCollector(str(self.base_dir))
        blocks = collector.process_include(include_line)
        
        assert len(blocks) == 1
        assert blocks[0].name == "Alice Smith"
    
    def test_include_collector_wildcard(self):
        """Test wildcard includes all blocks."""
        source_content = """@Contributor Alice
@Data Dataset1
@Method PCR"""
        
        self.create_test_file("source.mfd", source_content)
        
        include_line = IncludeLine(
            1, "@include source.mfd *",
            "source.mfd", "*", "",
            [], [], []
        )
        
        collector = IncludeCollector(str(self.base_dir))
        blocks = collector.process_include(include_line)
        
        assert len(blocks) == 3
    
    def test_include_collector_all_of_type(self):
        """Test including all blocks of a type."""
        source_content = """@Contributor Alice
@Contributor Bob
@Contributor Charlie
@Data SomeData"""
        
        self.create_test_file("source.mfd", source_content)
        
        include_line = IncludeLine(
            1, "@include source.mfd @Contributor",
            "source.mfd", "@Contributor", "",
            [], [], []
        )
        
        collector = IncludeCollector(str(self.base_dir))
        blocks = collector.process_include(include_line)
        
        assert len(blocks) == 3
        majors = [b.get_str_major() for b in blocks]
        assert all(m == "Contributor" for m in majors)
    
    def test_single_reference_to_file(self):
        """Test single reference to an include file."""
        source_content = "@Contributor TestUser\n@Contributor-Email test@example.com"
        main_content = """@MEDFORD description
@MEDFORD-Version 1.0
@Paper TestPaper
@include source.mfd @Contributor TestUser
@Data TestData"""
        
        self.create_test_file("source.mfd", source_content)
        main_file = self.create_test_file("main.mfd", main_content)
        
        mfd = MFD(
            str(main_file),
            mode=OutputMode.OTHER,
            action=ParserMode.VALIDATE,
            base_dir=str(self.base_dir),
            write_json=False
        )
        mfd.run_medford()
        
        assert len(mfd.blocks) == 4
        contributors = [b for b in mfd.blocks if b.get_str_major() == "Contributor"]
        assert len(contributors) == 1
        assert contributors[0].name == "TestUser"
    
    def test_two_references_to_same_file(self):
        """Test two references to the same file."""
        source_content = """@Contributor Alice
@Contributor-Role PI

@Contributor Bob
@Contributor-Role Co-PI"""

        main_content = """@MEDFORD description
@MEDFORD-Version 1.0
@Paper Paper1
@include source.mfd @Contributor Alice
@Data Data1
@include source.mfd @Contributor Bob
@Paper Paper2"""

        self.create_test_file("source.mfd", source_content)
        main_file = self.create_test_file("main.mfd", main_content)

        mfd = MFD(
            str(main_file),
            mode=OutputMode.OTHER,
            action=ParserMode.VALIDATE,
            base_dir=str(self.base_dir),
            write_json=False
        )
        mfd.run_medford()

        contributors = [b for b in mfd.blocks if b.get_str_major() == "Contributor"]
        assert len(contributors) == 2
        names = sorted([c.name for c in contributors])
        assert names == ["Alice", "Bob"]
    
    def test_json_output_with_includes(self):
        """Test that included blocks appear correctly in JSON output."""
        source_content = """@Contributor JsonTest
@Contributor-Email json@test.com
@Contributor-Role Tester"""

        main_content = """@MEDFORD description
@MEDFORD-Version 1.0
@Paper JsonPaper
@Paper-Title Test JSON
@include source.mfd @Contributor JsonTest"""

        self.create_test_file("source.mfd", source_content)
        main_file = self.create_test_file("main.mfd", main_content)

        old_cwd = os.getcwd()
        os.chdir(str(self.base_dir))
        try:
            mfd = MFD(
                str(main_file),
                mode=OutputMode.OTHER,
                action=ParserMode.COMPILE,
                base_dir=str(self.base_dir),
                write_json=True,
                output_path="."
            )
            mfd.run_medford()
            json_file = self.base_dir / "medford_output.json"
            assert json_file.exists()
            with open(json_file) as f:
                data = json.load(f)
            assert "Contributor" in data and len(data["Contributor"]) == 1
            contributor = data["Contributor"][0]
            assert contributor["value"] == "JsonTest"
            assert contributor["Email"][0] == "json@test.com"
            assert contributor["Role"][0] == "Tester"
        finally:
            os.chdir(old_cwd)
    
    def test_duplicate_same_include_twice(self):
        """Test that same include twice is detected and ignored."""
        source_content = "@Contributor DuplicatePerson"
        main_content = """@MEDFORD description
@MEDFORD-Version 1.0
@Paper Paper1
@include source.mfd @Contributor DuplicatePerson
@Data Data1
@include source.mfd @Contributor DuplicatePerson"""

        self.create_test_file("source.mfd", source_content)
        main_file = self.create_test_file("main.mfd", main_content)

        mfd = MFD(
            str(main_file),
            mode=OutputMode.OTHER,
            action=ParserMode.VALIDATE,
            base_dir=str(self.base_dir),
            write_json=False
        )
        mfd.run_medford()
        contributors = [b for b in mfd.blocks if b.get_str_major() == "Contributor"]
        assert len(contributors) == 1
    
    def test_missing_file_handling(self):
        """Test graceful handling of missing include file."""
        main_content = """@MEDFORD description
@MEDFORD-Version 1.0
@Paper TestPaper
@include nonexistent.mfd @Contributor Someone
@Data TestData"""

        main_file = self.create_test_file("main.mfd", main_content)

        mfd = MFD(
            str(main_file),
            mode=OutputMode.OTHER,
            action=ParserMode.VALIDATE,
            base_dir=str(self.base_dir),
            write_json=False
        )
        mfd.run_medford()
        contributors = [b for b in mfd.blocks if b.get_str_major() == "Contributor"]
        assert len(contributors) == 0
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive matching for includes."""
        source_content = "@Contributor CasePerson"
        main_content = """@MEDFORD description
@MEDFORD-Version 1.0
@Paper TestPaper
@include source.mfd @contributor caseperson"""

        self.create_test_file("source.mfd", source_content)
        main_file = self.create_test_file("main.mfd", main_content)

        mfd = MFD(
            str(main_file),
            mode=OutputMode.OTHER,
            action=ParserMode.VALIDATE,
            base_dir=str(self.base_dir),
            write_json=False
        )
        mfd.run_medford()
        contributors = [b for b in mfd.blocks if b.get_str_major() == "Contributor"]
        assert len(contributors) == 1 and contributors[0].name == "CasePerson"
    
    def test_circular_include_indirect(self):
        """Test detection of indirect circular includes (A includes B, B includes A)."""
        file_a_content = """@Contributor PersonA
@include file_b.mfd @Method Method1"""
        
        file_b_content = """@Method Method1
@include file_a.mfd @Contributor PersonA"""
        
        self.create_test_file("file_a.mfd", file_a_content)
        self.create_test_file("file_b.mfd", file_b_content)
        
        main_content = """@MEDFORD description
@MEDFORD-Version 1.0
@Paper TestPaper
@include file_a.mfd @Contributor PersonA"""
        
        main_file = self.create_test_file("main.mfd", main_content)
        
        mfd = MFD(
            str(main_file),
            mode=OutputMode.OTHER,
            action=ParserMode.VALIDATE,
            base_dir=str(self.base_dir),
            write_json=False
        )
        mfd.run_medford()
    
    def test_relative_path_resolution(self):
        """Test relative path resolution with base_dir."""
        subdir = self.base_dir / "subdir"
        subdir.mkdir()
        
        source_content = "@Contributor RelativePerson"
        self.create_test_file("subdir/source.mfd", source_content)
        
        main_content = """@MEDFORD description
@MEDFORD-Version 1.0
@Paper TestPaper
@include subdir/source.mfd @Contributor RelativePerson"""
        
        main_file = self.create_test_file("main.mfd", main_content)
        
        mfd = MFD(
            str(main_file),
            mode=OutputMode.OTHER,
            action=ParserMode.VALIDATE,
            base_dir=str(self.base_dir),
            write_json=False
        )
        mfd.run_medford()
        contributors = [b for b in mfd.blocks if b.get_str_major() == "Contributor"]
        assert len(contributors) == 1
        assert contributors[0].name == "RelativePerson"
