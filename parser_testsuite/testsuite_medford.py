import subprocess
import json
import os
import sys
import shutil


def run_medford(input_file):
    result = subprocess.run(
        [
            "python3",
            "src/MEDFORD/medford.py",
            "-m",
            "BAGIT",
            "--write_json",
            "validate",
            input_file,
        ],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stdout, result.stderr


def deep_compare(expected, actual, path="root"):
    differences = []

    # Compare dictionaries
    if isinstance(expected, dict):
        expected_keys = set(expected.keys())
        actual_keys = set(actual.keys())

        for key in expected_keys - actual_keys:
            differences.append(f"{path}.{key}: Missing in actual")

        for key in actual_keys - expected_keys:
            differences.append(f"{path}.{key}: Extra in actual")

        for key in expected_keys & actual_keys:
            if key in expected and key in actual:
                nested_diffs = deep_compare(expected[key], actual[key], f"{path}.{key}")
                differences.extend(nested_diffs)

    # Compare lists
    elif isinstance(expected, list):
        if len(expected) != len(actual):
            differences.append(
                f"{path}: Length mismatch. expected {len(expected)}, got {len(actual)}"
            )

        for i in range(min(len(expected), len(actual))):
            nested_diffs = deep_compare(expected[i], actual[i], f"{path}[{i}]")
            differences.extend(nested_diffs)

    elif expected != actual:
        differences.append(
            f"{path}: Value mismatch - expected '{expected}', got '{actual}'"
        )

    return differences


def main():
    input_dir = "testsuite/inputs"
    expected_dir = "testsuite/expected"
    output_dir = "testsuite/outputs"

    os.makedirs(output_dir, exist_ok=True)

    passed = 0
    failed = 0
    skipped = 0

    input_files = [f for f in os.listdir(input_dir) if f.endswith(".mfd")]

    print(f"Running tests on {len(input_files)} input files...\n")

    for input_file in input_files:
        base_name = os.path.splitext(input_file)[0]
        input_path = os.path.join(input_dir, input_file)
        expected_path = os.path.join(expected_dir, f"{base_name}.json")
        output_path = os.path.join(output_dir, f"{base_name}.json")

        # print(f"Testing {base_name}: ", end="", flush=True)

        success, stdout, stderr = run_medford(input_path)
        if not success:
            print(f"  Error: {stderr}")
            failed += 1
            continue

        if os.path.exists("medford_output.json"):
            shutil.copy("medford_output.json", output_path)
        else:
            print("FAILED (no output)")
            print("  Error: Output file 'medford_output.json' not generated")
            failed += 1
            continue

        if os.path.exists(expected_path) and os.path.exists(output_path):
            with open(expected_path, "r") as f:
                expected_data = json.load(f)

            with open(output_path, "r") as f:
                actual_data = json.load(f)

            differences = deep_compare(expected_data, actual_data)
        else:
            print(f"FAILED (missing expected or output file)")
            differences = ["Missing expected or output file"]

        if len(differences) == 0:
            passed += 1
        else:
            print("FAILED (output differs)")
            print("  Differences found:")
            for diff in differences[
                :10
            ]:  # Limit to first 10 diffs to avoid overwhelming output
                print(f"    - {diff}")
            if len(differences) > 10:
                print(f"    ... and {len(differences) - 10} more differences")
            failed += 1

    print(f"Tests completed: {passed + failed + skipped}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
