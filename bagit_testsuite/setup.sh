#!/bin/bash

INPUT_DIR="./inputs"
EXPECTED_DIR="./expected"
mkdir -p "$EXPECTED_DIR"

for input_file in "$INPUT_DIR"/*.mfd; do
    base_name=$(basename "$input_file" .mfd)
    
    # Generate expected output
    python3 src/MEDFORD/medford.py -m BAGIT compile "$input_file"
    python3 src/MEDFORD/medford.py -m BAGIT validate "$input_file"

done



python3 src/MEDFORD/medford.py -m BAGIT compile --write_json bagit_testsuite/inputs/multiple_files.mfd
python3 src/MEDFORD/medford.py -m BAGIT compile --write_json bagit_testsuite/inputs/basic_copy.mfd
python3 src/MEDFORD/medford.py -m BAGIT compile --write_json bagit_testsuite/inputs/basic_ref.mfd
python3 src/MEDFORD/medford.py -m BAGIT compile --write_json bagit_testsuite/inputs/no_file.mfd