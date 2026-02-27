# Test file for include + macro interaction
# Author: Yaman Bosnali
# Date: 01/17/2026

import subprocess
from pathlib import Path
import textwrap
import pytest

def _normalize(s: str) -> str:
    """ text normalization helper function for stable comparisons across runs."""
    lines = [ln.rstrip() for ln in s.strip().splitlines()]
    return "\n".join(lines)


def _run_medford_compile(input_path: Path, out_path: Path, cwd: Path):
    """Run: medford compile <input> --out <out_path> from cwd, return (code, stdout, stderr)."""

    cmd = ["medford", "compile", str(input_path), "--out", str(out_path)]
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr

# DEPRECIATED TEST - The new intention is that macro definitions
# and usage scopes should be contained within the same file.
#@pytest.mark.xfail(reason="DEPRECIATED TEST.")
#def test_macro_used_inside_included_file(tmp_path):
    """
    Macro defined in main file is used inside an included file.
    Expectation: include is expanded and macro references inside included content are expanded too.
    """

    # Included file that uses macro (but doesn't define it)
    inc_content = textwrap.dedent("""\
        @Photo `@{reef_photo}01
        @Photo `@{reef_photo}02
        @Photo `@{reef_photo}03
    """)
    inc_path = tmp_path / "inc.mfd"
    inc_path.write_text(inc_content, encoding="utf-8")

    # Main file that defines macro, includes the photo blocks from inc.mfd
    main_content = textwrap.dedent("""\
        @MEDFORD description
        @MEDFORD-Version 1.0

        `@reef_photo REEF_X_PHOTO_

        @include inc.mfd @Photo
    """)
    main_path = tmp_path / "main.mfd"
    main_path.write_text(main_content, encoding="utf-8")

    out_path = tmp_path / "out.mfd"

    code, out, err = _run_medford_compile(main_path, out_path, cwd=tmp_path)
    assert code == 0, f"compile failed:\n{err}"

    output_text = out_path.read_text(encoding="utf-8")

    # Included blocks should be present AND expanded
    assert "@Photo REEF_X_PHOTO_01" in output_text
    assert "@Photo REEF_X_PHOTO_02" in output_text
    assert "@Photo REEF_X_PHOTO_03" in output_text

    # Macro syntax should dissapear
    assert "`@reef_photo" not in output_text
    assert "`@{reef_photo}" not in output_text

@pytest.mark.xfail(reason="Macros are file-scoped: macros defined in included files are not visible to main file.")
def test_macro_defined_in_included_file_used_in_main(tmp_path):
    """
    Macro is defined inside an included file, then used in the main file.
    Expectation: macro definitions inside included content are collected and usable by main.
    """

    # Included file that defines the macro
    inc_content = textwrap.dedent("""\
        `@reef_photo REEF_X_PHOTO_
    """)
    inc_path = tmp_path / "inc.mfd"
    inc_path.write_text(inc_content, encoding="utf-8")

    # Main file that includes inc.mfd, then uses the macro
    main_content = textwrap.dedent("""\
        @MEDFORD description
        @MEDFORD-Version 1.0

        @include inc.mfd *

        @Photo `@{reef_photo}01
        @Photo `@{reef_photo}02
        @Photo `@{reef_photo}03
    """)
    main_path = tmp_path / "main.mfd"
    main_path.write_text(main_content, encoding="utf-8")

    out_path = tmp_path / "out.mfd"

    code, out, err = _run_medford_compile(main_path, out_path, cwd=tmp_path)
    assert code == 0, f"compile failed:\n{err}"

    output_text = out_path.read_text(encoding="utf-8")

    # Macro should expand in main
    assert "@Photo REEF_X_PHOTO_01" in output_text
    assert "@Photo REEF_X_PHOTO_02" in output_text
    assert "@Photo REEF_X_PHOTO_03" in output_text

    # Macro syntax should dissapear
    assert "`@reef_photo" not in output_text
    assert "`@{reef_photo}" not in output_text

#@pytest.mark.xfail(reason="Macros defined in included files are not collected/expanded (current behavior).")
def test_macro_defined_and_used_within_included_file(tmp_path):
    """
    Macro is defined and used inside the included file itself.
    Main file only includes that file.
    """

    inc_content = textwrap.dedent("""\
        `@reef_photo REEF_X_PHOTO_
        @Photo `@{reef_photo}01
        @Photo `@{reef_photo}02
        @Photo `@{reef_photo}03
    """)
    inc_path = tmp_path / "inc.mfd"
    inc_path.write_text(inc_content, encoding="utf-8")

    main_content = textwrap.dedent("""\
        @MEDFORD description
        @MEDFORD-Version 1.0

        @include inc.mfd @Photo
    """)
    main_path = tmp_path / "main.mfd"
    main_path.write_text(main_content, encoding="utf-8")

    out_path = tmp_path / "out.mfd"

    code, out, err = _run_medford_compile(main_path, out_path, cwd=tmp_path)
    assert code == 0, f"compile failed:\nSTDOUT:\n{out}\nSTDERR:\n{err}"


    output_text = out_path.read_text(encoding="utf-8")

    assert "@Photo REEF_X_PHOTO_01" in output_text
    assert "@Photo REEF_X_PHOTO_02" in output_text
    assert "@Photo REEF_X_PHOTO_03" in output_text

    # Macro syntax should dissapear
    assert "`@reef_photo" not in output_text
    assert "`@{reef_photo}" not in output_text

def test_out_idempotent_with_include_and_macro(tmp_path):
    """
    --out idempotence when both include expansion and macro expansion occur.
    Macro is defined in main, used in included file, output should stabilize after recompile.
    """

    inc_content = textwrap.dedent("""\
        @Photo `@{reef_photo}01
        @Photo `@{reef_photo}02
        @Photo `@{reef_photo}03
    """)
    inc_path = tmp_path / "inc.mfd"
    inc_path.write_text(inc_content, encoding="utf-8")

    main_content = textwrap.dedent("""\
        @MEDFORD description
        @MEDFORD-Version 1.0

        `@reef_photo REEF_X_PHOTO_

        @include inc.mfd @Photo
    """)
    main_path = tmp_path / "main.mfd"
    main_path.write_text(main_content, encoding="utf-8")

    out_path = tmp_path / "out.mfd"

    # First compile: from main -> out
    code1, out1, err1 = _run_medford_compile(main_path, out_path, cwd=tmp_path)
    assert code1 == 0, f"first compile failed:\n{err1}"
    first_run = out_path.read_text(encoding="utf-8")

    # expanded output exists
    assert "@Photo REEF_X_PHOTO_01" in first_run
    assert "`@{reef_photo}" not in first_run
    assert "`@reef_photo" not in first_run

    # Second compile: compile the output again
    code2, out2, err2 = _run_medford_compile(out_path, out_path, cwd=tmp_path)
    assert code2 == 0, f"second compile failed:\n{err2}"
    second_run = out_path.read_text(encoding="utf-8")

    # Idempotence check
    assert _normalize(first_run) == _normalize(second_run), "Output changed after second compile"

def test_macro_expands_to_include_behavior(tmp_path):
    """
    a macro expands to an '@include ...' directive.

    Trying to document two behaviors:
      (A) A standalone macro-only line may be dropped (producing no output).
      (B) If embedded in a normal tag line, the expansion should appear in output
          either as literal '@include ...' text OR trigger include processing .
    """

    # File that would be included if @include gets executed
    (tmp_path / "source.mfd").write_text(
        "@Contributor Ada Lovelace\n", encoding="utf-8"
    )

    main_content = textwrap.dedent("""\
        @MEDFORD description
        @MEDFORD-Version 1.0

        `@make_include @include source.mfd @Contributor Ada Lovelace

        # Case 1: macro-only line
        `@{make_include}

        # Case 2: embedded inside a normal tag line
        @Note `@{make_include}
    """)
    main_path = tmp_path / "main.mfd"
    main_path.write_text(main_content, encoding="utf-8")

    out_path = tmp_path / "out.mfd"
    code, out, err = _run_medford_compile(main_path, out_path, cwd=tmp_path)
    assert code == 0, f"compile failed (macro->include):\n{err}"

    output_text = out_path.read_text(encoding="utf-8")

    # --- Case 1: macro-only line behavior

    # --- Case 2: embedded behavior 
    included_effect_happened = "@Contributor Ada Lovelace" in output_text
    include_literal_remained = "@include source.mfd @Contributor Ada Lovelace" in output_text

    # Documenting current observed behavior:
    # - The include does execute since we see the included block
    # - The literal include directive also remains in output (leaks through)
    assert included_effect_happened, (
        "Expected the macro-generated @include to execute (include content should appear), "
        "but it did not."
    )
    assert include_literal_remained, (
        "Expected the literal '@include ...' directive to remain in output (current behavior), "
        "but it did not."
    )

