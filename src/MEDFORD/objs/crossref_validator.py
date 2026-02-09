"""Cross-tag reference validation for MEDFORD files."""

from typing import Dict, List, Set
from .linecollections import Block, Detail
from .. import mfdglobals
from ..submodules.mfdvalidator.errors import MissingCrossReferenceError


class CrossRefValidator:
    """Validates that subtags reference existing major tags."""

    REFERENCE_TYPES = ["Contributor", "Institution"]

    # Subtags that may have a local definition (override global requirement)
    LOCAL_SUBTAGS = {
        "Contributor": ["Email", "ORCID", "Association", "Role"],
        "Institution": ["Address", "Department", "Country", "URL"],
    }

    def __init__(self, named_blocks: Dict[str, Dict[str, Block]]):
        self.named_blocks = named_blocks
        self.defined_contributors: Set[str] = set()
        self.defined_institutions: Set[str] = set()

    def validate(self) -> bool:
        """Run two-pass validation. Returns True if valid, False if errors found."""
        self._collect_major_tags()
        return not self._validate_references()

    def _collect_major_tags(self) -> None:
        """Pass 1: Collect all @Contributor and @Institution major tags."""
        # Hard coded right now but could change later
        if "Contributor" in self.named_blocks:
            self.defined_contributors = set(self.named_blocks["Contributor"].keys())
        if "Institution" in self.named_blocks:
            self.defined_institutions = set(self.named_blocks["Institution"].keys())

    def _validate_references(self) -> bool:
        """Pass 2: Check all -Contributor and -Institution subtags. Returns True if errors found."""
        has_errors = False

        for major_token, blocks_by_name in self.named_blocks.items():
            if major_token in self.REFERENCE_TYPES:
                continue  # Skip Contributor/Institution blocks themselves

            for block_name, block in blocks_by_name.items():
                if self._validate_block(block):
                    has_errors = True

        return has_errors

    def _validate_block(self, block: Block) -> bool:
        """Validate cross-references in a single block. Returns True if errors found."""
        if not block.minor_tokens:
            return False

        has_errors = False
        minor_token_names = [mt[0] for mt in block.minor_tokens]

        for ref_type in self.REFERENCE_TYPES:
            for minor_token, detail in block.minor_tokens:
                if minor_token == ref_type:
                    # Check for local override (has local subtags like -Contributor-Email)
                    if self._has_local_subtags(minor_token_names, ref_type):
                        continue

                    # Validate the reference exists
                    referenced_value = detail.get_raw_content().strip()
                    if not self._reference_exists(ref_type, referenced_value):
                        self._report_error(detail, ref_type, referenced_value)
                        has_errors = True

        return has_errors

    def _has_local_subtags(self, minor_tokens: List[str], ref_type: str) -> bool:
        """Check if local subtags exist (e.g., Contributor-Email means no global needed)."""
        local_subtags = self.LOCAL_SUBTAGS.get(ref_type, [])
        for subtag in local_subtags:
            compound = f"{ref_type}-{subtag}"
            if compound in minor_tokens:
                return True
        return False

    def _reference_exists(self, ref_type: str, value: str) -> bool:
        """Check if a referenced major tag exists."""
        if ref_type == "Contributor":
            return value in self.defined_contributors
        elif ref_type == "Institution":
            return value in self.defined_institutions
        return True

    def _report_error(self, detail: Detail, ref_type: str, referenced_value: str) -> None:
        """Report missing cross-reference error."""
        if ref_type == "Contributor":
            available = list(self.defined_contributors)
        else:
            available = list(self.defined_institutions)

        error = MissingCrossReferenceError(detail, ref_type, referenced_value, available)
        mfdglobals.validator.add_error(error)
