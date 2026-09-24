# --out patameter testing file
# Author: Yaman Bosnali
# Date: 11/08/2025

import sys
import pytest
import subprocess
from pathlib import Path
import textwrap

# --- helpers -----------------------------------
def _run_medford_compile(input_path: Path, out_arg: str):
    """Run medford with 'medford compile <input.mfd> [--out <args>]
     and return (returncode, stdout, stderr)."""

    cmd = ["medford", "compile", str(input_path)]
    if out_arg is not None:
        cmd += ["--out", out_arg]

    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def _normalize(s: str) -> str:
    """Lenient text normalization for stable comparisons across runs."""
    lines = [ln.rstrip() for ln in s.strip().splitlines()]
    return "\n".join(lines)


def _normalize_no_builddate(s: str) -> str:
    """Like _normalize but strips @__BUILD_DATE lines so idempotency checks
    are not broken by the timestamp changing between runs."""
    lines = [ln.rstrip() for ln in s.strip().splitlines()
             if not ln.startswith("@__BUILD_DATE")]
    return "\n".join(lines)

# --- tests -----------------------------------------------------

# Test that --out creates a file with content
def test_out_writes_file(tmp_path):
    # create a minimal medford input file
    sample = textwrap.dedent("""\
        @MEDFORD description
        @MEDFORD-Version 1.0
        # comment to ensure comments don't break parsing

        @Title Tiny Example
        @Contributor Jane Doe
    """)

    input_path = tmp_path / "input.mfd"
    input_path.write_text(sample, encoding="utf-8")

    out_path = tmp_path / "out.mfd"

    # run the CLI
    code, stdout, stderr = _run_medford_compile(input_path, str(out_path))

    # Assert: program succeeded
    assert code == 0, f"expected success, got {code}\nstderr:\n{stderr}"

    # Assert: file exists and has content
    assert out_path.exists(), "output file was not created"
    text = out_path.read_text(encoding="utf-8")
    assert text.strip() != "", "output file is unexpectedly empty"

    # check: first line is the build date tag
    assert text.splitlines()[0].startswith("@__BUILD_DATE")


# Tests that --out is idempotent with a small file (compiling the output file again produces the same file)
def test_out_idempotent_smallfile(tmp_path):
    # create a minimal medford input file
    sample = textwrap.dedent("""\
        @MEDFORD description
        @MEDFORD-Version 1.0
        # comment to ensure comments don't break parsing

        @Title Tiny Example
        @Contributor Jane Doe
    """)

    input_path = tmp_path / "input.mfd"
    input_path.write_text(sample, encoding="utf-8")

    out_path = tmp_path / "out.mfd"

    # First run
    code1, stdout1, stderr1 = _run_medford_compile(input_path, str(out_path))
    assert code1 == 0, f"First run failed with code {code1}\nstderr:\n{stderr1}"

    first_run = out_path.read_text(encoding="utf-8")

    # Second run using the output of the first run as input
    code2, stdout2, stderr2 = _run_medford_compile(out_path, str(out_path))
    assert code2 == 0, f"Second run failed with code {code2}\nstderr:\n{stderr2}"

    # Read the output file after the second run
    final_text = out_path.read_text(encoding="utf-8")

    # Content (excluding the build date, which changes each run) is unchanged after the second run
    assert _normalize_no_builddate(first_run) == _normalize_no_builddate(final_text), \
        "Output file content changed after second run"

# Tests that --out is idempotent with a large file (compiling the output file again produces the same file)
def test_out_idempotent_largefile(tmp_path):
    # grab a large mfd file from samples directory
    sample = Path(__file__).parent.parent / "samples" / "Mayfield-2014.mfd"
    assert sample.exists(), "Sample large mfd file does not exist for testing"

    # put sample file in a temporary location
    input_path = tmp_path / sample.name
    input_path.write_text(sample.read_text(encoding="utf-8"), encoding="utf-8")

    out_path = tmp_path / "out.mfd"

    # First run
    code1, stdout1, stderr1 = _run_medford_compile(input_path, str(out_path))
    assert code1 == 0, f"First run failed with code {code1}\nstderr:\n{stderr1}"

    first_run = out_path.read_text(encoding="utf-8")

    # Second run using the output of the first run as input
    code2, stdout2, stderr2 = _run_medford_compile(out_path, str(out_path))
    assert code2 == 0, f"Second run failed with code {code2}\nstderr:\n{stderr2}"

    # Read the output file after the second run
    final_text = out_path.read_text(encoding="utf-8")

    # Content (excluding the build date, which changes each run) is unchanged after the second run
    assert _normalize_no_builddate(first_run) == _normalize_no_builddate(final_text), \
        "Output file content changed after second run"

# Tests for invalid --out path handling
def test_out_invalid_path(tmp_path):
    # create a minimal medford input file
    sample = textwrap.dedent("""\
        @MEDFORD description
        @MEDFORD-Version 1.0
        # comment to ensure comments don't break parsing

        @Title Tiny Example
        @Contributor Jane Doe
    """)

    input_path = tmp_path / "input.mfd"
    input_path.write_text(sample, encoding="utf-8")

    # Use an invalid path (e.g., a directory that doesn't exist)
    out_path = tmp_path / "nonexistent_dir" / "out.mfd"

    # run the CLI
    code, stdout, stderr = _run_medford_compile(input_path, str(out_path))

    # Assert: program failed
    assert code != 0, f"expected failure, got {code}\nstdout:\n{stdout}"

    # Assert: appropriate error message in stderr
    assert "[dev] Failed to write --out file" in stderr and "No such file or directory" in stderr, f"unexpected stderr:\n{stderr}"


# Tests that --out correctly expands macros in the output file
def test_out_with_macros(tmp_path):
    MACRO_SAMPLE = """\
        @MEDFORD description
        @MEDFORD-Version 1.0

        # Define an in-line macro
        `@reef_photo REEF_X_PHOTO_

        # Call the macros
        @Photo `{reef_photo}01

        @Photo `{reef_photo}02

        @Photo `{reef_photo}03
        """

    input_path = tmp_path / "input_with_macros.mfd"
    input_path.write_text(MACRO_SAMPLE, encoding="utf-8")

    out_path = tmp_path / "out_with_macros.mfd"

    # compile to stdout (no file writes needed)
    code, out, err = _run_medford_compile(input_path, str(out_path))
    assert code == 0, f"compile failed:\n{err}"

    # Read the output file
    output_text = out_path.read_text(encoding="utf-8")

    # Assert: inlined macro expanded to concrete text
    assert "@Photo REEF_X_PHOTO_01" in output_text
    assert "@Photo REEF_X_PHOTO_02" in output_text
    assert "@Photo REEF_X_PHOTO_03" in output_text

    # Assert: macro definition and calls should not remain as tags
    assert "`@reef_photo" not in output_text
    assert "`@{reef_photo}" not in output_text

def test_out_with_macros_idempotent(tmp_path):
    MACRO_SAMPLE = """\
        @MEDFORD description
        @MEDFORD-Version 1.0

        # Define an in-line macro
        `@reef_photo REEF_X_PHOTO_

        # Call the macros
        @Photo `{reef_photo}01

        @Photo `{reef_photo}02

        @Photo `{reef_photo}03
        """

    input_path = tmp_path / "input_with_macros.mfd"
    input_path.write_text(MACRO_SAMPLE, encoding="utf-8")

    out_path = tmp_path / "out_with_macros.mfd"

    # First compile
    code1, out1, err1 = _run_medford_compile(input_path, str(out_path))
    assert code1 == 0, f"first compile failed:\n{err1}"
    
    first_run = out_path.read_text(encoding="utf-8")
    assert "@Photo REEF_X_PHOTO_01" in first_run, "Macro did not expand correctly"
    assert "`@reef_photo" not in first_run, "Macro definition remained in output"

    # Second compile using the output of the first run as input
    code2, out2, err2 = _run_medford_compile(out_path, str(out_path))
    assert code2 == 0, f"second compile failed:\n{err2}"

    final_text = out_path.read_text(encoding="utf-8")

    # Content (excluding the build date, which changes each run) is unchanged after the second run
    assert _normalize_no_builddate(first_run) == _normalize_no_builddate(final_text), \
        "Output file content changed after second run with macros"


# Tests that --out writes @__BUILD_DATE as the first line with a UTC timestamp
def test_out_build_date_present(tmp_path):
    sample = textwrap.dedent("""\
        @MEDFORD description
        @MEDFORD-Version 1.0

        @Title Build Date Test
        @Contributor Jane Doe
    """)

    input_path = tmp_path / "input.mfd"
    input_path.write_text(sample, encoding="utf-8")
    out_path = tmp_path / "out.mfd"

    code, _, stderr = _run_medford_compile(input_path, str(out_path))
    assert code == 0, f"compile failed:\n{stderr}"

    lines = out_path.read_text(encoding="utf-8").splitlines()

    # First line must be the build date tag
    assert lines[0].startswith("@__BUILD_DATE"), \
        f"Expected @__BUILD_DATE as first line, got: {lines[0]!r}"

    # The build date line must end with " UTC"
    assert lines[0].endswith("UTC"), \
        f"Build date line does not end with UTC: {lines[0]!r}"


# Tests that re-compiling an --out file replaces the old build date rather than duplicating it
def test_out_build_date_overwritten(tmp_path):
    import time

    sample = textwrap.dedent("""\
        @MEDFORD description
        @MEDFORD-Version 1.0

        @Title Overwrite Test
        @Contributor Jane Doe
    """)

    input_path = tmp_path / "input.mfd"
    input_path.write_text(sample, encoding="utf-8")
    out_path = tmp_path / "out.mfd"

    # First compile
    code1, _, stderr1 = _run_medford_compile(input_path, str(out_path))
    assert code1 == 0, f"first compile failed:\n{stderr1}"
    first_date_line = out_path.read_text(encoding="utf-8").splitlines()[0]

    # Adding some delay so the timestamp is guaranteed to differ
    time.sleep(1.1)

    # Second compile using the output of the first compile as input
    code2, _, stderr2 = _run_medford_compile(out_path, str(out_path))
    assert code2 == 0, f"second compile failed:\n{stderr2}"

    text = out_path.read_text(encoding="utf-8")
    build_date_lines = [ln for ln in text.splitlines() if ln.startswith("@__BUILD_DATE")]

    # Only one build date tag must exist
    assert len(build_date_lines) == 1, \
        f"Expected exactly 1 @__BUILD_DATE line, found {len(build_date_lines)}: {build_date_lines}"

    # The date must have been updated
    assert build_date_lines[0] != first_date_line, \
        "Build date was not updated on recompilation"