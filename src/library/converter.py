import json
import sys
import argparse
from json2rdf import json2rdf


def main():

    parser = argparse.ArgumentParser(
        description="Convert MEDFORD JSON data to RDF/XML format"
    )
    parser.add_argument("--input", help="Path to the input JSON file (default stdin)")
    parser.add_argument(
        "--output", help="Path to the output RDF/XML file (default stdout)"
    )
    args = parser.parse_args()

    if args.input:
        try:
            # Read JSON data from the specified input file
            with open(args.input, "r") as json_file:
                json_data = json.load(json_file)
        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)
            exit(1)
        except FileNotFoundError:
            print("JSON file not found")
            exit(1)

    else:
        try:
            # Read JSON data from stdin if --input is not provided
            json_data = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)
            exit(1)

    # Convert json to RDF/XML
    test = json2rdf.jsonToRdf(json_data)
    test.json_to_graph()
    rdf_xml_data_bytes = test.graph_to_rdfxml()

    if args.output:
        try:
            # Write the RDF/XML data to the specified output file
            with open(args.output, "wb") as rdf_file:
                rdf_file.write(rdf_xml_data_bytes)
            print("RDF data written successfully.")
        except IOError as e:
            print("Error writing RDF data:", e)
            exit(1)

    else:
        # Write the RDF/XML data to stdout if --output is not provided
        # Convert bytes data to a string and remove the last newline character
        rdf_xml_data_str = rdf_xml_data_bytes.decode("utf-8").rstrip("\n")
        print(rdf_xml_data_str)


if __name__ == "__main__":
    main()
