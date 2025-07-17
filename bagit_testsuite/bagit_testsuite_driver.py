import subprocess
import json
import os
import sys
import shutil
import tempfile
import zipfile
import filecmp
from pathlib import Path
from collections import OrderedDict


def run_bagit_compiler(input_file):
    try:
        
        cmd = [
            "python3", "src/MEDFORD/medford.py", "-m", "BAGIT", "compile", 
            input_file
        ]
        print(f"cmd is {cmd}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        success = result.returncode == 0
        return success, result.stdout, result.stderr
    
    except Exception as e:
        return False, "", str(e)

def compare_zip_files(expected_bag_path, generated_bag):
    results = {
        'identical': False,
        'file_differences': [],
        'directory_differences': [],
        'missing_in_zip1': [],
        'missing_in_zip2': [],
        'content_differences': []
    }
    with tempfile.TemporaryDirectory() as temp_dir:
        temp1 = Path(temp_dir) / "zip1"
        temp2 = Path(temp_dir) / "zip2"

        temp1.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(expected_bag_path, 'r') as zf:
            zf.extractall(temp1)

        temp2.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(generated_bag, 'r') as zf:
            zf.extractall(temp2)
        
        comparison = compare_directories(temp1, temp2)
        results.update(comparison)
        
        
    results['identical'] = (
        len(results['file_differences']) == 0 and
        len(results['directory_differences']) == 0 and
        len(results['missing_in_zip1']) == 0 and
        len(results['missing_in_zip2']) == 0 and
        len(results['content_differences']) == 0
    )

    return results

def compare_directories(dir1, dir2):
    results = {
        'file_differences': [],
        'directory_differences': [],
        'missing_in_zip1': [],
        'missing_in_zip2': [],
        'content_differences': []
    }
    
    files1 = get_all_paths(dir1)
    files2 = get_all_paths(dir2)
    
    only_in_1 = files1 - files2
    only_in_2 = files2 - files1
    common = files1 & files2

    for item in only_in_1:
        results['missing_in_zip2'].append(item)
    
    for item in only_in_2:
        results['missing_in_zip1'].append(item)
        
    for item in common:
        path1 = dir1 / item
        path2 = dir2 / item
        
        if path1.is_file() != path2.is_file():
            results['file_differences'].append(
                f"Type mismatch: {item}"
            )
            continue
        
        if path1.is_file() and path2.is_file():
            if not filecmp.cmp(path1, path2, shallow=False):
                results['content_differences'].append(str(item))
    return results

def get_all_paths(directory):
    paths = set()
    for item in directory.rglob("*"):
        if item.name == "manifest.txt": continue
        if item.is_file():  
            relative_path = item.relative_to(directory)
            paths.add(str(relative_path))
    return paths

def main():
    input_dir = "bagit_testsuite/inputs"
    expected_dir = "bagit_testsuite/expected"
    output_dir = "."
    
    passed = 0
    failed = 0
    skipped = 0

    input_files = [f for f in os.listdir(input_dir) if f.endswith(".mfd")]

    print(f"Running BagIt tests on {len(input_files)} input files...\n")

    for input_file in input_files:
        base_name = os.path.splitext(input_file)[0]
        
        input_path = os.path.join(input_dir, input_file)
        expected_bag_path = os.path.join(expected_dir, f"exp_{base_name}.zip")

        print(f"\nTesting {base_name}: ", end="", flush=True)

        success, stdout, stderr = run_bagit_compiler(input_path)
        
        if base_name.endswith("_err"):
            if ("BagIt package created at: None" in stdout) and ("Error creating" in stdout):
                print("PASSED (expected error)")
                passed += 1
            else:
                print("FAILED (expected error but compilation succeeded)")
                failed += 1
            continue  # Skip bag comparison for error cases
        
        # Handle normal test cases
        if not success:
            print("FAILED (compilation error)")
            print(f"  Error: {stderr}")
            failed += 1
            continue
        
        # Check if output directory exists before listing
        if not os.path.exists(output_dir):
            print("FAILED (no output directory)")
            print("  Error: Output directory was not created")
            failed += 1
            continue
        
        generated_bag = None
        for file in os.listdir(output_dir):
            if file.endswith(".zip"):
                generated_bag = os.path.join(output_dir, file)
                break

        if not generated_bag or not os.path.exists(generated_bag):
            print("FAILED (no bag generated)")
            print("  Error: No .zip file found in output directory")
            failed += 1
            continue

        # Check if expected bag exists
        if not os.path.exists(expected_bag_path):
            print("SKIPPED (no expected bag)")
            print(f"  Expected: {expected_bag_path}")
            skipped += 1
            # Clean up generated bag for skipped test
            try:
                if os.path.exists(generated_bag):
                    os.remove(generated_bag)
            except OSError as e:
                print(f"  Warning: Could not remove {generated_bag}: {e}")
            continue

        results = compare_zip_files(expected_bag_path, generated_bag)
        
        if results['identical']:
            print("PASSED")
            passed += 1
        else:
            print("FAILED (bag contents differ)")
            print("  Differences found:")
            if results['missing_in_zip1']:
                print(f"    Missing in actual: {results['missing_in_zip1'][:3]}")
            if results['missing_in_zip2']:
                print(f"    Missing in expected: {results['missing_in_zip2'][:3]}")
            if results['content_differences']:
                print(f"    Content differs: {results['content_differences'][:3]}")
            failed += 1
        
        # Clean up generated bag after comparison
        try:
            if os.path.exists(generated_bag):
                os.remove(generated_bag)
        except OSError as e:
            print(f"  Warning: Could not remove {generated_bag}: {e}")
        
    print(f"\nTests completed: {passed + failed + skipped}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())