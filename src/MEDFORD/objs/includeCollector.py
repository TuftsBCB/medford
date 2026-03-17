"""Module for handling @include functionality.

Reads .mfd files, extracts matching content, and caches parsed files.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from .lines import IncludeLine
from .linecollector import LineCollector
from .linereader import LineReader, DetailStatics


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
    
    def _expand_macros_in_text(self, text: str, resolved: Dict[str, str]) -> str:
        """
        Expand macro uses in a single line of text using local resolved macros.
        The purpose of this function is to expand macros BEFORE building blocks
        coming from included files

        Important: This function only expands macros that are defined in the 
        same file (file-scoped rule).

        Args:
            text: The line of text to process coming from the included file.
            resolved: A dictionary mapping macro names to their resolved values.

        Returns:
            The text with macros expanded where possible.
        """

        # Reusing the macro regex from LineReader
        macro_pat = re.compile(DetailStatics.macro_use_regex)

        # Find all macro occurrences in this line
        matches = list(macro_pat.finditer(text))
        if not matches:
            return text  # if no macros exist, return original text


        # Build output by replacing matches from right to left because
        # otherwise the indices shift later.
        out = text
        for m in reversed(matches):
            # The regex supports two forms of macros. it stores the name in one of these groups.
            # UPDATE THIS WHEN MACRO SYNTAX IS FINALIZED
            name = m.group("mname_closed") or m.group("mname_open")
            if not name:
                continue  

            # File-scoped rule: only expand if this file defines the macro
            replacement = resolved.get(name)
            if replacement is None:
                continue 

            # Replace the substring corresponding to the macro expansion
            out = out[: m.start()] + replacement + out[m.end() :]

        return out
    
    def parse_file(self, file_path: Path) -> Dict:
        """
        Parses an included .mfd file into blocks, includes, and macros.
        Performs a two-pass parse of the included file:
            1. Collect macros defined in the file.
            2. Expand those macros in the raw lines, then re-parse into blocks.

        The results are cached to avoid redundant work on multiple includes of the same file.

        Args:
            file_path: Path to the .mfd file to parse.

        Returns:
            A dictionary containing:
                - 'blocks': List of parsed blocks from the file.
                - 'macros': Dictionary of macros defined in the file.
                - 'include_lines': List of IncludeLine objects found in the file.
                - 'file_path': The Path object of the file (for reference).
        """
        file_str = str(file_path)
        
        if file_str in self.file_cache:
            return self.file_cache[file_str]
        
        # Collect raw lines of the included files
        raw_lines: List[str] = []
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_lines = f.readlines()

        # Pass #1: parse to collect macros for THIS file (file-scoped rule)
        lines1 = []
        for i, line_content in enumerate(raw_lines):
            line = LineReader.process_line(line_content, i + 1)
            if line is not None:
                lines1.append(line)

        collector1 = LineCollector(lines1)
        macros = collector1.get_macros()

        # temporary debug print
        # if macros:
            # print(f"[include debug] {file_path.name}: found macros: {list(macros.keys())}")

        # Resolve macros locally (file-scoped)
        resolved: Dict[str, str] = {}
        for name, macro in macros.items():
            resolved[name] = macro.resolve(macros)

        # Pass #2: expand macro uses locally, then re-parse into blocks so that
        # we can return macro-free blocks
        lines2 = []
        for i, line_content in enumerate(raw_lines):
            expanded = self._expand_macros_in_text(line_content, resolved)
            line2 = LineReader.process_line(expanded, i + 1)
            if line2 is not None:
                lines2.append(line2)

        collector2 = LineCollector(lines2)

        file_structure = {
            'blocks': collector2.get_flat_blocks(),
            'macros': macros,  # keep original macro objs (mostly for debugging)
            'include_lines': collector2.get_include_lines(),
            'file_path': file_path
        }

        self.file_cache[file_str] = file_structure
        
        return file_structure
    
    def find_matching_blocks(self, file_structure: Dict, tag_name: str, selector: str) -> List:
        """
        Select blocks from a parsed included file that satisfy an include query.

        Matching rules:
            - If tag_name == "*" OR selector == "*": return *all* blocks.
            - Otherwise, match blocks where block.get_str_major() equals tag_name
            (case-insensitive, with optional leading '@' removed).
            - If selector is empty: include all blocks with that major.
            - If selector is non-empty: include only blocks whose header name equals
            selector (case-insensitive).

        Args:
            file_structure: Dict returned by parse_file().
            tag_name: Major tag filter from @include (e.g. "@Contributor" or "*").
            selector: Optional name filter from @include (specific name, "*" or "").

        Returns:
            A list of blocks satisfying the selection criteria.
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
    
    def process_include(self, include_line: IncludeLine, _register: bool = True) -> List:
        """Process a single include and return matching blocks (no duplicates).
        This function takes an @include line, reads the target file to be included,
        and recursively expands any nested @include statements found withing
        that file.

        _register=True (default): Used in the outermost call from the main file.
                Each block is checked against included_blocks to avoid duplicate includes.
        _register=False: Used for nested/recursive calls when expanding includes within includes.
                In this mode, included_blocks tracking is skpeed entirely to allow all blocks to
                be returned without filtering, and let the outermost call handle deduplication.

        Raises FileNotFoundError if file missing, ValueError if circular include.
        """
        file_path = self.resolve_file_path(include_line.filename)
        file_str = str(file_path.resolve())

        # Check if the file to process is already in the current include stack
        if file_str in self.circular_includes:
            raise ValueError(f"Circular include detected: {file_str}")

        self.circular_includes.add(file_str)

        try:
            # This parsing returns 'blocks' and 'include_lines'
            file_structure = self.parse_file(file_path)

            # Recursively expand any @include statements found inside this file
            # before filtering, so that nested blocks are visible to find_matching_blocks.
            # Use _register=False so nested blocks are not pre-registered in included_blocks.
            nested_includes = file_structure.get('include_lines', [])
            if nested_includes:

                # Pass _register=False here so that the recursive calls
                # do not apply dedup tracking to the nested blocks.
                expanded_blocks = self.insert_blocks_at_include_positions(
                    file_structure['blocks'], nested_includes, _register=False
                )
                expanded_structure = dict(file_structure)
                expanded_structure['blocks'] = expanded_blocks
            else:
                # If no nested includes exist, then the original file_structure
                # is already fully expanded and can be used as-is.
                expanded_structure = file_structure

            # Filter the blocks according to the tag_name and selector in the @include line
            matching_blocks = self.find_matching_blocks(
                expanded_structure,
                include_line.tag_name,
                include_line.selector
            )

            # When called for nested expansion, skip dedup tracking
            if not _register:
                return list(matching_blocks)

            # For the outermost call, check each block against included_blocks
            # to avoid duplicates across the final output.
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

                # if block is new, record it in included_blocks and include it in the output
                self.included_blocks[block_key] = file_str
                filtered_blocks.append(block)

            return filtered_blocks
        finally:
            # Remove the current file from the circular_includes set to allow
            # it to be included again in a different context without falsely 
            # triggering circular detection.
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

    def _obj_lineno(self, obj, default_if_missing: int) -> int:
        for name in ("line_number", "lineno", "lineNo", "line_index", "idx"):
            v = getattr(obj, name, None)
            if isinstance(v, int):
                return v
        for holder in ("line", "source", "src", "origin"):
            sub = getattr(obj, holder, None)
            if sub is None:
                continue
            for name in ("line_number", "lineno", "lineNo", "line_index", "idx"):
                v = getattr(sub, name, None)
                if isinstance(v, int):
                    return v
        return default_if_missing

    def _block_start_lineno(self, block) -> int:
        # Prefer Detail.get_linenos()[0] if available
        if getattr(block, "details", None) and block.details:
            d0 = block.details[0]
            if hasattr(d0, "get_linenos") and callable(d0.get_linenos):
                try:
                    lns = d0.get_linenos()
                    if isinstance(lns, (list, tuple)) and lns and isinstance(lns[0], int):
                        return lns[0]
                except Exception:
                    pass

            h = getattr(d0, "headline", None)
            if h is not None:
                ln = self._obj_lineno(h, None)
                if isinstance(ln, int):
                    return ln

        return self._obj_lineno(block, 10**9)

    def insert_blocks_at_include_positions(self, main_blocks: List, include_lines: List[IncludeLine], _register: bool = True) -> List:
        """
        For each IncludeLine (in main-file order):
        - expands it into blocks (via process_include)
        - inserts those blocks into the block list where the @include appeared
        Returns a NEW list of blocks.

        _register is forwarded to process_include. Pass False for nested/recursive
        calls so that included_blocks dedup tracking is not applied prematurely.
        """
        if not include_lines:
            return list(main_blocks)

        blocks = list(main_blocks)

        # Make sure includes are handled in main file order
        include_lines_sorted = sorted(include_lines, key=lambda il: il.lineno)

        for il in include_lines_sorted:
            try:
                new_blocks = self.process_include(il, _register=_register)
            except Exception as e:
                print(f"Warning: {e}")
                continue

            if not new_blocks:
                continue

            # Insert before the first block whose start line is AFTER the include line
            insert_at = len(blocks)
            for idx, b in enumerate(blocks):
                if self._block_start_lineno(b) > il.lineno:
                    insert_at = idx
                    break

            blocks[insert_at:insert_at] = new_blocks

        return blocks