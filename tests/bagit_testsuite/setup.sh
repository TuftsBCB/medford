#!/bin/bash

INPUT_DIR="bagit_testsuite/inputs"
EXPECTED_DIR="bagit_testsuite/expected"
mkdir -p "$EXPECTED_DIR"

for input_file in "$INPUT_DIR"/*.mfd; do
    base_name=$(basename "$input_file" .mfd)
    
    # Generate expected output
    
    python3 src/MEDFORD/medford.py -m BAGIT validate "$input_file"
    python3 src/MEDFORD/medford.py -m BAGIT compile "$input_file"

done

python3 src/MEDFORD/medford.py -m BAGIT validate bagit_testsuite/inputs/basic_primary.mfd
python3 src/MEDFORD/medford.py -m BAGIT compile bagit_testsuite/inputs/basic_primary.mfd