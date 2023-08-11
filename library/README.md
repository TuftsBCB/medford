# MEDFORD JSON TO RDF Converter json2rdf
Introduction
------------------
MEDFORD JSON to RDF Converter is a Python script that converts MEDFORD JSON data to RDF/XML format using the rdflib library. It provides a simple way to transform MEDFORD JSON-based metadata into RDF triples, making it easier to work with Linked Data and semantic web applications.

Installing
------------------
To use json2rdf, you need to have the following Python libraries installed:

    rdflib: The library to work with RDF data.

You can install this library using pip:

    pip install rdflib

How to Use
------------------
To use the JSON to RDF Converter, follow the steps below:

1. Clone the repository to your local machine.
2. Prepare your JSON data: Create or obtain the JSON data that you want to convert to RDF.
3. Run the script: Execute the "converter.py" script from the command line, providing the appropriate parameters.
4. Command-line Arguments

    --input: Path to the input JSON file (default is stdin). 

    --output: Path to the output RDF/XML file (default is stdout).

5. Example

    a. Convert JSON data from "input.json" to RDF/XML and save it to "output.rdf":

        python3 converter.py --input input.json --output output.rdf

    b. Convert JSON data from stdin to RDF/XML and print the output to the terminal:

        python3 converter.py < input.json

Design Principles
------------------
The json2rdf library follows the following design principles:
1. Validity: Ensure that the RDF/XML adheres to the RDF specifications and is a valid XML document. Use proper namespace declarations and well-formed XML syntax.
2. Use namespaces: Utilize namespaces to uniquely identify resources and properties. This helps avoid conflicts and ensures clarity in the RDF data.
3. Clear subject-predicate-object structure: Represent triples (subject-predicate-object) clearly in the RDF/XML. Use appropriate XML elements and attributes to express this structure.
4. Reusability: Reuse existing vocabularies (e.g., Dublin Core, BIBO, VCARD) when appropriate instead of reinventing terms. This enhances interoperability and consistency.
5. Avoid deep nesting: Keep the RDF/XML structure simple and avoid excessive nesting of elements. 
6. Avoid using the “about” or “id” attributes in RDF descriptions due to the local scope of RDF generation and the lack of global identifiers for “about”. Using a local ID is not much better; it can hinder interoperability with other RDF dataset. It is preferable to adhere to the standard RDF triple structure, which ensures consistency and clarity in RDF data modeling, omitting fields that can cause confusion due to the lack of a global space of “about” fields.

    This is controversial. If we were to conform to the true “about” standard, we would have to maintain a stateful database that remembers every label we have ever used in an “about”, and avoid using anything twice. The fact that this is stateful means that we would need to generate the rdf on a website rather than in an application, where the website would track the global ids. 

    This is much more “expensive” than writing an app. The basic question is whether the expense is worth the trouble. In our case, it doesn’t seem to be. 

    Meanwhile, external opinions are also split on whether an ID should be tracked even though it is a local key that is not universal. Some say it’s useful, others say it’s a waste of space. We have erred on the side of not including IDs, which are not considered useful by a subset of the RDF community. 

Theory of Operation
------------------
The json2Rdf library works by traversing the MEDFORD JSON data recursively and mapping JSON properties to appropriate RDF terms using predefined namespaces. It identifies major tokens, such as "code," "data," "journal," etc., and creates RDF triples accordingly. It also handles minor tokens, such as "ref," "primary," and "copy," to provide additional information about the triples.

The library follows a two-step process:

Conversion: The MEDFORD JSON data is traversed, and RDF triples are generated based on the mapping of JSON properties to RDF terms.

Serialization: The generated RDF triples are serialized into RDF/XML format using the rdflib library.

RDF/XML Validation
------------------ 
You can utilize the online RDF/XML validator available at https://www.w3.org/RDF/Validator/. This tool allows you to check the correctness and conformance of your RDF/XML data with the RDF specifications provided by the World Wide Web Consortium (W3C)."

References
------------------
MEDFORD specs: https://github.com/TuftsBCB/MEDFORD-Spec/blob/master/main.pdf

rdflib library documentation: https://rdflib.readthedocs.io/en/stable/

RDF/XML specification: https://www.w3.org/TR/rdf-syntax-grammar/

DublinCore RDF/XML examples: https://www.dublincore.org/specifications/dublin-core/dcmes-xml/

Qualified DC: https://www.dublincore.org/specifications/dublin-core/dcq-rdf-xml/

Feel free to contribute to the project by submitting issues or pull requests on the repository page. If you have any questions or need further assistance, please don't hesitate to reach out. Happy converting!

