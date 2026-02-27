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

    # (Optional) sanity check: first line still looks MEDFORD-y
    assert text.splitlines()[0].startswith("@MEDFORD")


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

    # Assert: The content remains unchanged after the second run
    assert _normalize(first_run) == _normalize(final_text), "Output file content changed after second run"

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

    # Assert: The content remains unchanged after the second run
    assert _normalize(first_run) == _normalize(final_text), "Output file content changed after second run"

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
        @Photo `@{reef_photo}01

        @Photo `@{reef_photo}02

        @Photo `@{reef_photo}03
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
        @Photo `@{reef_photo}01

        @Photo `@{reef_photo}02

        @Photo `@{reef_photo}03
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

    # Assert: The content remains unchanged after the second run
    assert _normalize(first_run) == _normalize(final_text), "Output file content changed after second run with macros"