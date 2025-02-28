import subprocess
import json
import os
import sys
import shutil

def run_medford(input_file):
    result = subprocess.run(
        ["python3", "src/MEDFORD/medford.py", "-m", "BAGIT", "--write_json", "validate", input_file],
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stdout, result.stderr

def compare(expected_file, actual_file):
    try:
        with open(expected_file) as f:
            expected = json.load(f)
        with open(actual_file) as f:
            actual = json.load(f)
            
        # Simple check for now -TODO deep comparison later
        return expected == actual, ["JSON objects differ"]
    except Exception as e:
        return False, [f"Error comparing files: {str(e)}"]

def main():
    input_dir = "./inputs"
    expected_dir = "./expected"
    output_dir = "./outputs"
    
    os.makedirs(output_dir, exist_ok=True)
    
    passed = 0
    failed = 0
    
    input_files = [f for f in os.listdir(input_dir) if f.endswith(".mfd")]
        
    for input_file in input_files:
        base_name = os.path.splitext(input_file)[0]
        input_path = os.path.join(input_dir, input_file)
        expected_path = os.path.join(expected_dir, f"{base_name}.json")
        output_path = os.path.join(output_dir, f"{base_name}.json")
        
        print(f"Testing {base_name}: ", end="", flush=True)
        
        success, stdout, stderr = run_medford(input_path)
        if not success:
            print("FAILED")
            print(f"  Error: {stderr}")
            failed += 1
            continue
        
        if os.path.exists("medford_output.json"):
            shutil.copy("medford_output.json", output_path)
        else:
            print("FAILED - Output file not generated")
            failed += 1
            continue
            
        if not os.path.exists(expected_path):
            print("SKIPPED - No expected output")
            continue
            
        is_equal, differences = compare(expected_path, output_path)
        if is_equal:
            print("PASSED")
            passed += 1
        else:
            print("FAILED - Output differs")
            for diff in differences:
                print(f"  {diff}")
            failed += 1
    
    print("-" * 40)
    print(f"Tests completed: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())