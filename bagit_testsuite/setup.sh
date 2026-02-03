#!/bin/bash

INPUT_DIR="./inputs"
EXPECTED_DIR="./expected"
mkdir -p "$EXPECTED_DIR"

for input_file in "$INPUT_DIR"/*.mfd; do
    base_name=$(basename "$input_file" .mfd)
    echo "processing "
    echo $input_file
    # Generate expected output
    python3 -m MEDFORD -m BAGIT compile "$input_file"
    #PYTHONPATH=../src python3 -m MEDFORD -m BAGIT validate "$input_file"
    #python3 src/MEDFORD/medford.py -m BAGIT compile "$input_file"
    #python3 src/MEDFORD/medford.py -m BAGIT validate "$input_file"

done

#python3 src/MEDFORD/medford.py -m BAGIT compile bagit_testsuite/inputs/curr_directory.mfd
#python3 src/MEDFORD/medford.py -m BAGIT validate bagit_testsuite/inputs/curr_directory.mfd
#python3 src/MEDFORD/medford.py -m BAGIT compile bagit_testsuite/inputs/multiple_files.mfd
#python3 src/MEDFORD/medford.py -m BAGIT validate bagit_testsuite/inputs/multiple_files.mfd
