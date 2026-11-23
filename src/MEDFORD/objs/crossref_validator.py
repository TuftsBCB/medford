"""Cross-tag reference validation for MEDFORD files."""

import yaml
from typing import Dict, List, Optional, Set
from .linecollections import Block, Detail
from .. import mfdglobals
from ..submodules.mfdvalidator.errors import (
    MissingCrossReferenceError,
    MissingRequiredCrossRefSubtag,
    MissingDesirableCrossRefSubtag,
)

# Capitalized type names in the YAML that are primitive validators, not block references.
_YAML_PRIMITIVE_TYPES = {"String", "Text", "Email", "URI", "Phone", "Number", "Integer", "Date"}


def _parse_crossref_config(yaml_path: str) -> Dict[str, Dict[str, Dict[str, str]]]:
    """Parse medford.yaml and extract cross-reference subtag config.

    Returns Dict[major_token, Dict[subtag_name, {"type": str, "status": str}]]
    where type is a cross-reference type (e.g. "Contributor", "Institution")
    and status is "Required", "Desirable", or "Optional".
    """
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    if not data:
        return {}

    config: Dict[str, Dict[str, Dict[str, str]]] = {}
    STATUSES = {"Required", "Desirable", "Optional"}

    for major_tag, rules_list in data.items():
        if not isinstance(rules_list, list):
            continue
        for item in rules_list:
            if not isinstance(item, dict) or "Contents" not in item:
                continue
            for subtag_entry in item["Contents"]:
                if not isinstance(subtag_entry, dict):
                    continue
                for subtag_name, subtag_rules in subtag_entry.items():
                    if not isinstance(subtag_rules, list):
                        continue
                    # Find cross-reference type (capitalized, not a primitive)
                    ref_type = None
                    for rule in subtag_rules:
                        if isinstance(rule, dict) and "Type" in rule:
                            t = rule["Type"]
                            if t and t[0].isupper() and t not in _YAML_PRIMITIVE_TYPES:
                                ref_type = t
                    if ref_type is None:
                        continue
                    # Find status string; default to Optional if not listed
                    status = "Optional"
                    for rule in subtag_rules:
                        if isinstance(rule, str) and rule in STATUSES:
                            status = rule
                            break
                    if major_tag not in config:
                        config[major_tag] = {}
                    config[major_tag][subtag_name] = {"type": ref_type, "status": status}

    return config


class CrossRefValidator:
    """Validates that subtags reference existing major tags."""

    # Subtags that may have a local definition (override global reference requirement)
    LOCAL_SUBTAGS = {
        "Contributor": ["Email", "ORCID", "Association", "Role"],
        "Institution": ["Address", "Department", "Country", "URL"],
    }

    def __init__(self, named_blocks: Dict[str, Dict[str, Block]],
                 yaml_path: Optional[str] = None):
        self.named_blocks = named_blocks
        self.defined_contributors: Set[str] = set()
        self.defined_institutions: Set[str] = set()

        if yaml_path is not None:
            try:
                self.config = _parse_crossref_config(yaml_path)
            except Exception:
                self.config = {}
        else:
            self.config = {}

        # Get which subtag names are cross-reference types from config,
        # with fallback to hard-coded defaults.
        config_ref_types: Set[str] = set()
        for subtags in self.config.values():
            for info in subtags.values():
                config_ref_types.add(info["type"])
        self._reference_types = config_ref_types if config_ref_types else {"Contributor", "Institution"}

    def validate(self) -> bool:
        """Run two-pass validation. Returns True if valid, False if errors found."""
        self._collect_major_tags()
        return not self._validate_references()

    def _collect_major_tags(self) -> None:
        """Pass 1: Collect all @Contributor and @Institution major tags."""
        if "Contributor" in self.named_blocks:
            self.defined_contributors = set(self.named_blocks["Contributor"].keys())
        if "Institution" in self.named_blocks:
            self.defined_institutions = set(self.named_blocks["Institution"].keys())

    def _validate_references(self) -> bool:
        """Pass 2: Check cross-ref subtags. Returns True if hard errors found."""
        has_errors = False

        for major_token, blocks_by_name in self.named_blocks.items():
            for block_name, block in blocks_by_name.items():
                # Case B: existing cross-ref subtags must point to valid blocks.
                # Skip self-validation for reference types (e.g. don't check
                # @Contributor-Contributor, which doesn't exist by design).
                if major_token not in self._reference_types:
                    if self._validate_block(block):
                        has_errors = True

                # Case A: required/desirable cross-ref subtags must be present.
                # Runs on ALL blocks including Contributor/Institution themselves.
                self._check_missing_subtags(block, major_token)

        return has_errors

    def _validate_block(self, block: Block) -> bool:
        """Case B: check existing cross-ref subtags point to valid blocks.
        Returns True if hard errors found."""
        if not block.minor_tokens:
            return False

        has_errors = False
        minor_token_names = [mt[0] for mt in block.minor_tokens]

        for ref_type in self._reference_types:
            for minor_token, detail in block.minor_tokens:
                if minor_token == ref_type:
                    if self._has_local_subtags(minor_token_names, ref_type):
                        continue
                    referenced_value = detail.get_raw_content().strip()
                    if not self._reference_exists(ref_type, referenced_value):
                        self._report_bad_reference(detail, ref_type, referenced_value)
                        has_errors = True

        return has_errors

    def _check_missing_subtags(self, block: Block, major_token: str) -> None:
        """Case A: emit errors/warnings for absent required/desirable cross-ref subtags."""
        if major_token not in self.config:
            return

        present_minor_tokens = {mt[0] for mt in block.minor_tokens} if block.minor_tokens else set()

        for subtag_name, subtag_info in self.config[major_token].items():
            if subtag_name in present_minor_tokens:
                continue

            status = subtag_info["status"]
            ref_type = subtag_info["type"]
            available = list(self.named_blocks.get(ref_type, {}).keys())

            if status == "Required":
                error = MissingRequiredCrossRefSubtag(
                    block, major_token, subtag_name, ref_type, available
                )
                mfdglobals.validator.add_error(error)
            elif status == "Desirable":
                warning = MissingDesirableCrossRefSubtag(
                    block, major_token, subtag_name, ref_type, available
                )
                mfdglobals.validator.add_error(warning)

    def _has_local_subtags(self, minor_tokens: List[str], ref_type: str) -> bool:
        """Check if local subtags exist (e.g., Contributor-Email means no global needed)."""
        local_subtags = self.LOCAL_SUBTAGS.get(ref_type, [])
        for subtag in local_subtags:
            compound = f"{ref_type}-{subtag}"
            if compound in minor_tokens:
                return True
        return False

    def _reference_exists(self, ref_type: str, value: str) -> bool:
        """Check if a referenced major tag block exists."""
        if ref_type == "Contributor":
            return value in self.defined_contributors
        elif ref_type == "Institution":
            return value in self.defined_institutions
        return True

    def _report_bad_reference(self, detail: Detail, ref_type: str, referenced_value: str) -> None:
        """Report case B: cross-ref subtag points to a nonexistent block."""
        if ref_type == "Contributor":
            available = list(self.defined_contributors)
        else:
            available = list(self.defined_institutions)

        error = MissingCrossReferenceError(detail, ref_type, referenced_value, available)
        mfdglobals.validator.add_error(error)
