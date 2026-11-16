# Whitespace testing suite
# Each whitespace_testsuite/Input/<case>.mfd is compiled, then checked:
#   json       medford_output.json  == Json-expected/<case>.json
#   out        --out file           == Out-expected/<case>.mfd (exact, minus @__BUILD_DATE)
#   roundtrip  compiling the --out file again gives the same file
# A check without an answer key is left out; a case with no answer key at all is
# named <case>-roundtrip_only. All failing checks of a case are reported together.
# A case in EXPECTED_ERRORS (named <case>-error) must instead be rejected with an
# error message: MEDFORD exits with an error and does not crash with a traceback.
#
#   pytest tests/test_whitespace_suite.py
#   pytest tests/test_whitespace_suite.py -k ws03 -vv

import difflib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SUITE = ROOT / "whitespace_testsuite"

# Cases known to fail, with the reason. Remove an entry once it passes.
KNOWN_FAILURES = {}

# Cases MEDFORD must reject with an error message, with the rule that makes them errors
EXPECTED_ERRORS = {
    "ws10_text_after_empty_line": "an empty line ends the value; the text after it belongs to no tag",
    "ws11_macro_continuation": "a macro is one line; a line continuing it is an error",
    "ws12_macro_indented_continuation": "a macro is one line; an indented line continuing it is an error",
    "ws13_macro_comment_between": "a macro is one line; text after it (even past a comment) is an error",
    "ws14_macro_in_note": "a macro is one line, even when used in a Note",
    "ws18_space_after_at": "'@ Contributor' (space after @) is not a valid tag",
    "ws22_empty_value": "a tag with no value is an error",
    "ws23_spaces_only_value": "a tag with no value is an error",
    "ws33_braces_in_template_body": "a macro used inside a template body is an error (for now)",
    "ws37_digit_led_tag": "a line starting with @ and a digit is not a valid tag",
}

# One pytest param per case
def param(case):
    has_key = (SUITE / "Json-expected" / f"{case}.json").exists() or (SUITE / "Out-expected" / f"{case}.mfd").exists()
    marks = [pytest.mark.xfail(reason=KNOWN_FAILURES[case], strict=True)] if case in KNOWN_FAILURES else []
    if case in EXPECTED_ERRORS:
        name = f"{case}-error"
    else:
        name = case if has_key else f"{case}-roundtrip_only"
    return pytest.param(case, id=name, marks=marks)


CASES = [param(p.stem) for p in sorted((SUITE / "Input").glob("*.mfd"))]


# Reads a file as text, keeping \r for CRLF
def read(path):
    return path.read_bytes().decode("utf-8")


# Splits a --out file into lines, minus the @__BUILD_DATE line (changes every run)
def without_build_date(text):
    lines = text.splitlines(keepends=True)
    if lines and lines[0].startswith("@__BUILD_DATE"):
        lines = lines[1:]
        while lines and lines[0].strip() == "":
            lines = lines[1:]
    return lines


# Line-by-line diff for a failure message; repr() shows tabs, \r and trailing spaces
def diff(want, got, name):
    return "".join(difflib.unified_diff(
        [repr(line) + "\n" for line in want], [repr(line) + "\n" for line in got],
        f"{name} (expected)", f"{name} (actual)", lineterm="\n",
    ))


# Runs `medford --write_json compile <src> --out out.mfd` in the new folder `tmp`
def run_medford(src, tmp):
    tmp.mkdir()
    return subprocess.run(
        [sys.executable, "-m", "MEDFORD", "--write_json", "compile", str(src), "--out", "out.mfd"],
        cwd=tmp, capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )


# Compiles <src> and returns (json_data, out_text)
def compile_mfd(src, tmp):
    p = run_medford(src, tmp)
    assert p.returncode == 0, f"MEDFORD failed:\n{p.stderr or p.stdout}"
    return json.loads(read(tmp / "medford_output.json")), read(tmp / "out.mfd")


# Checks json and out against the answer keys that exist, then the roundtrip
@pytest.mark.parametrize("case", CASES)
def test_case(case, tmp_path):
    if case in EXPECTED_ERRORS:
        p = run_medford(SUITE / "Input" / f"{case}.mfd", tmp_path / "first")
        assert p.returncode != 0, f"expected an error ({EXPECTED_ERRORS[case]}), but it compiled"
        assert "Traceback" not in p.stderr, f"expected an error message, but MEDFORD crashed:\n{p.stderr}"
        return

    data, out = compile_mfd(SUITE / "Input" / f"{case}.mfd", tmp_path / "first")
    failures = []

    json_key = SUITE / "Json-expected" / f"{case}.json"
    if json_key.exists():
        want = json.loads(read(json_key))
        if data != want:
            dump = lambda d: json.dumps(d, indent=2, ensure_ascii=False).splitlines()
            failures.append("json:\n" + diff(dump(want), dump(data), json_key.name))

    out_key = SUITE / "Out-expected" / f"{case}.mfd"
    if out_key.exists():
        want, got = without_build_date(read(out_key)), without_build_date(out)
        if got != want:
            failures.append("out:\n" + diff(want, got, out_key.name))

    again = tmp_path / "again.mfd"
    again.write_bytes(out.encode("utf-8"))
    _, out2 = compile_mfd(again, tmp_path / "second")
    if without_build_date(out2) != without_build_date(out):
        failures.append("roundtrip:\n" + diff(without_build_date(out), without_build_date(out2), "again.mfd"))

    assert not failures, "\n\n".join(failures)
