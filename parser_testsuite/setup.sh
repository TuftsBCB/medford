#!/bin/bash
INPUT_DIR="./inputs"
EXPECTED_DIR="./expected"
mkdir -p "$EXPECTED_DIR"

for input_file in "$INPUT_DIR"/*.mfd; do
    base_name=$(basename "$input_file" .mfd)
    
    # Generate expected output

    PYTHONPATH=../src python3 -m MEDFORD -m BAGIT --write_json validate "$input_file"
    cp medford_output.json "$EXPECTED_DIR/${base_name}.json"

    echo "Created expected output for $base_name"
done
