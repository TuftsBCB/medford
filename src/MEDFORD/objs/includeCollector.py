"""Module for handling @include functionality.

Reads .mfd files, extracts matching content, and caches parsed files.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from .lines import IncludeLine
from .linecollector import LineCollector
from .linereader import LineReader


class IncludeCollector:
    """Handles @include functionality.
    
    Reads .mfd files, parses them into blocks, and returns matching content.
    Supports file caching, path resolution, and error handling.
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize with optional base directory for resolving relative paths."""
        self.base_dir = Path(base_dir) if base_dir else None
        self.file_cache: Dict[str, Dict] = {}
        self.circular_includes: set = set()
        self.included_blocks: Dict[str, str] = {}
        self.duplicate_warnings: List[str] = []
    
    def resolve_file_path(self, filename: str) -> Path:
        """Resolve file path (relative or absolute).
        
        Raises FileNotFoundError if file doesn't exist.
        """
        if os.path.isabs(filename):
            file_path = Path(filename)
        else:
            if self.base_dir:
                file_path = self.base_dir / filename
            else:
                file_path = Path(filename)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Include file not found: {file_path}")
        
        return file_path
    
    def parse_file(self, file_path: Path) -> Dict:
        """Parse a .mfd file and return its structure (blocks, macros, includes).
        
        Uses cache if file was already parsed.
        """
        file_str = str(file_path)
        
        if file_str in self.file_cache:
            return self.file_cache[file_str]
        
        lines = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line_content in enumerate(f.readlines()):
                line = LineReader.process_line(line_content, i + 1)
                if line is not None:
                    lines.append(line)
        
        collector = LineCollector(lines)
        file_structure = {
            'blocks': collector.get_flat_blocks(),
            'macros': collector.get_macros(),
            'include_lines': collector.get_include_lines(),
            'file_path': file_path
        }
        
        self.file_cache[file_str] = file_structure
        
        return file_structure
    
    def find_matching_blocks(self, file_structure: Dict, tag_name: str, selector: str) -> List:
        """Find blocks matching the include criteria.
        
        tag_name: Tag type (e.g., "@contributor") or "*" for all
        selector: Specific value, "*" for all, or empty for all of tag type
        """
        matching_blocks = []
        blocks = file_structure['blocks']
        
        if selector.strip() == "*" or tag_name.strip() == "*":
            return blocks
        
        clean_tag_name = tag_name.lstrip('@').strip()
        
        for block in blocks:
            block_name = block.name.strip()
            block_major = block.get_str_major().strip()
            
            if block_major.lower() == clean_tag_name.lower():
                if not selector or selector.strip() == "":
                    matching_blocks.append(block)
                else:
                    if block_name.lower() == selector.strip().lower():
                        matching_blocks.append(block)
        
        return matching_blocks
    
    def process_include(self, include_line: IncludeLine) -> List:
        """Process a single include and return matching blocks (no duplicates).
        
        Raises FileNotFoundError if file missing, ValueError if circular include.
        """
        file_path = self.resolve_file_path(include_line.filename)
        file_str = str(file_path.resolve())
        
        if file_str in self.circular_includes:
            raise ValueError(f"Circular include detected: {file_str}")
        
        self.circular_includes.add(file_str)
        
        try:
            file_structure = self.parse_file(file_path)
            matching_blocks = self.find_matching_blocks(
                file_structure, 
                include_line.tag_name, 
                include_line.selector
            )
            
            filtered_blocks = []
            for block in matching_blocks:
                block_key = f"{block.get_str_major()}@{block.name.strip()}"
                
                if block_key in self.included_blocks:
                    prev_source = self.included_blocks[block_key]
                    if prev_source == file_str:
                        warning = f"Warning: Duplicate include of '{block_key}' from {file_str} - ignoring duplicate"
                        if warning not in self.duplicate_warnings:
                            self.duplicate_warnings.append(warning)
                            print(warning)
                    else:
                        error = f"Error: Block '{block_key}' already included from {prev_source}, cannot include again from {file_str}"
                        self.duplicate_warnings.append(error)
                        print(error)
                    continue
                
                self.included_blocks[block_key] = file_str
                filtered_blocks.append(block)
            
            return filtered_blocks
        finally:
            self.circular_includes.discard(file_str)
    
    def process_includes(self, include_lines: List[IncludeLine]) -> List:
        """Process multiple includes and return all matching blocks."""
        all_blocks = []
        
        for include_line in include_lines:
            try:
                matching_blocks = self.process_include(include_line)
                all_blocks.extend(matching_blocks)
            except FileNotFoundError as e:
                print(f"Warning: {e}")
                continue
            except ValueError as e:
                print(f"Warning: {e}")
                continue
        
        return all_blocks
    
    def clear_cache(self):
        """Clear file cache and all tracking data."""
        self.file_cache.clear()
        self.circular_includes.clear()
        self.included_blocks.clear()
        self.duplicate_warnings.clear()
    
    def expand_macros_in_includes(self, include_lines: List[IncludeLine]) -> List:
        """Process includes and return blocks.
        
        Note: Macro expansion is handled by Dictionizer later in the pipeline.
        """
        return self.process_includes(include_lines)
    
    def handle_circular_includes(self, include_lines: List[IncludeLine]) -> List:
        """Process includes with automatic circular dependency detection.
        
        Note: Circular detection is built into process_include().
        """
        return self.process_includes(include_lines)
    
    def check_conflicts_with_main_blocks(self, main_blocks: List) -> List[str]:
        """Check if included blocks conflict with main file blocks.
        
        Call after processing includes. Returns list of conflict messages.
        """
        conflicts = []
        for block in main_blocks:
            block_key = f"{block.get_str_major()}@{block.name.strip()}"
            if block_key in self.included_blocks:
                source_file = self.included_blocks[block_key]
                conflict_msg = f"Error: Block '{block_key}' is defined in main file but was already included from {source_file}"
                conflicts.append(conflict_msg)
                print(conflict_msg)
        
        return conflicts
    
    def get_duplicate_warnings(self) -> List[str]:
        """Get all duplicate warnings collected during processing."""
        return self.duplicate_warnings.copy()
