from json2rdf import json2rdf
import difflib
import unittest
import sys

sys.path.append("..")  # Add the parent directory to the Python path


class TestJsonToRdf(unittest.TestCase):

    # find the difference between the two strings
    def find_string_diff(self, string1, string2):
        # Create a SequenceMatcher object
        seq_matcher = difflib.SequenceMatcher(None, string1, string2)

        # Get the differences between the strings
        diff = seq_matcher.get_opcodes()

        # Create a list to store the differences
        differences = []

        for opcode, i1, i2, j1, j2 in diff:
            if opcode == "equal":
                continue
            elif opcode == "insert":
                differences.append(f"Insert: '{string2[j1:j2]}' at position {i1}")
            elif opcode == "delete":
                differences.append(f"Delete: '{string1[i1:i2]}' from position {i1}")
            elif opcode == "replace":
                differences.append(
                    f"Replace: '{string1[i1:i2]}' with '{string2[j1:j2]}' at position {i1}"
                )

        return differences

    # The order of the XML namespaces (xmlns) listed in the RDF is arbitrary,
    # and it may vary between different serializations.
    # To compare the converted RDF/XML with the expected RDF/XML,
    # we should disregard the order of the xmlns declarations.
    # We can remove the xmlns prefixes from the RDF/XML to make the
    # comparison more straightforward.

    def remove_rdfxmlns(self, rdfxml):

        # Split the string into lines
        lines = rdfxml.splitlines()

        # Remove the first and last lines
        lines = lines[1:-1]

        # Join the remaining lines back into a single string
        result_rdfxml = "\n".join(lines)

        return result_rdfxml

    # Convert json to RFD/XML and remove the XML namespaces
    def convert(self, json_input):
        test = json2rdf.jsonToRdf(json_input)
        test.json_to_graph()
        rdf_xml_data_bytes = test.graph_to_rdfxml()
        rdfxml = rdf_xml_data_bytes.decode("utf-8")
        rdfxml2 = self.remove_rdfxmlns(rdfxml)
        return rdfxml2

    ###############################################################
    # Test for code

    def test_case1(self):
        json_input = {
            "Code": [
                [
                    200,
                    {
                        "Ref": [
                            [
                                90,
                                {
                                    "desc": [[90, "HiRise"]],
                                    "Type": [[91, "Assembly of genome scaffolds"]],
                                },
                            ]
                        ]
                    },
                ]
            ]
        }
        expected_rdfxml = """  <rdf:Description>
    <rdf:type rdf:resource="https://www.eecs.tufts.edu/~wlou01/mf/elements/code" />
    <mfterms:isRef>true</mfterms:isRef>
    <dcterms:title>HiRise</dcterms:title>
    <dcterms:subject>Assembly of genome scaffolds</dcterms:subject>
  </rdf:Description>"""
        converted_rdfxml = self.convert(json_input)
        diff = self.find_string_diff(expected_rdfxml, converted_rdfxml)

        assert converted_rdfxml == expected_rdfxml, "\n".join(diff)

    ###############################################################
    # Test for contributor

    def test_case2(self):
        json_input = {
            "Contributor": [
                [
                    1,
                    {
                        "desc": [[1, "Polina Shpilker"]],
                        "Association": [
                            [
                                2,
                                "Department of Computer Science, Tufts University, 1XX College Ave, 02155, MA, USA",
                            ]
                        ],
                        "Role": [[3, "First Author"], [4, "Corresponding Author"]],
                    },
                ]
            ]
        }
        expected_rdfxml = """  <dc:contributor>
    <vcard:fn>Polina Shpilker</vcard:fn>
    <dcterms:publisher>Department of Computer Science, Tufts University, 1XX College Ave, 02155, MA, USA</dcterms:publisher>
    <vcard:role>First Author, Corresponding Author</vcard:role>
  </dc:contributor>"""
        converted_rdfxml = self.convert(json_input)
        diff = self.find_string_diff(expected_rdfxml, converted_rdfxml)
        assert converted_rdfxml == expected_rdfxml, "\n".join(diff)

    ###############################################################
    # Test for data

    def test_case3(self):
        json_input = {
            "Data": [
                [
                    4,
                    {
                        "Ref": [
                            [
                                4,
                                {
                                    "desc": [
                                        [4, "Reef Genomics Pocillopora damicornis"]
                                    ],
                                    "URI": [[5, "http://pdam.reefgenomics.org"]],
                                    "Type": [[6, "Website"]],
                                },
                            ]
                        ]
                    },
                ]
            ]
        }
        expected_rdfxml = """  <rdf:Description>
    <dcterms:type>dataset</dcterms:type>
    <mfterms:isRef>true</mfterms:isRef>
    <dcterms:title>Reef Genomics Pocillopora damicornis</dcterms:title>
    <dcterms:source rdf:resource="http://pdam.reefgenomics.org" />
    <dcterms:format>Website</dcterms:format>
  </rdf:Description>"""
        converted_rdfxml = self.convert(json_input)
        diff = self.find_string_diff(expected_rdfxml, converted_rdfxml)
        assert converted_rdfxml == expected_rdfxml, "\n".join(diff)

    ###############################################################
    # Test for date

    def test_case4(self):
        json_input = {
            "Date": [[12, {"desc": [[12, "2018-05-09"]], "Note": [[15, "Received"]]}]]
        }
        expected_rdfxml = """  <dc:date>
    <dcterms:date rdf:datatype="http://www.w3.org/2001/XMLSchema#date">2018-05-09</dcterms:date>
    <dcterms:description>Received</dcterms:description>
  </dc:date>"""
        converted_rdfxml = self.convert(json_input)
        diff = self.find_string_diff(expected_rdfxml, converted_rdfxml)
        assert converted_rdfxml == expected_rdfxml, "\n".join(diff)

    ###############################################################
    # Test for expedition
    def test_case5(self):
        json_input = {
            "Expedition": [
                [
                    15,
                    {
                        "desc": [[15, "Coral cruise"]],
                        "ShipName": [[16, "Ship"]],
                        "CruiseID": [[17, "39849"]],
                        "MooringID": [[18, "A78324"]],
                    },
                ]
            ]
        }
        expected_rdfxml = """  <rdf:Description>
    <rdf:type rdf:resource="https://www.eecs.tufts.edu/~wlou01/mf/elements/expedition" />
    <dcterms:title>Coral cruise</dcterms:title>
    <mfterms:shipName>Ship</mfterms:shipName>
    <mfterms:cruiseID>39849</mfterms:cruiseID>
    <mfterms:mooringID>A78324</mfterms:mooringID>
  </rdf:Description>"""
        converted_rdfxml = self.convert(json_input)
        diff = self.find_string_diff(expected_rdfxml, converted_rdfxml)
        assert converted_rdfxml == expected_rdfxml, "\n".join(diff)

    ###############################################################
    # Test for freeform
    def test_case6(self):
        json_input = {
            "Freeform": [
                [
                    19,
                    {
                        "Date": [
                            [
                                19,
                                {
                                    "desc": [[19, "05-22"]],
                                    "Note": [[20, "Hello Workd"]],
                                },
                            ]
                        ]
                    },
                ]
            ]
        }
        expected_rdfxml = """  <dc:date>
    <rdf:type rdf:resource="https://www.eecs.tufts.edu/~wlou01/mf/elements/freeform" />
    <dcterms:date>05-22</dcterms:date>
    <dcterms:description>Hello Workd</dcterms:description>
  </dc:date>"""
        converted_rdfxml = self.convert(json_input)
        diff = self.find_string_diff(expected_rdfxml, converted_rdfxml)
        assert converted_rdfxml == expected_rdfxml, "\n".join(diff)

        ###############################################################
        # Test for Funding

    def test_case7(self):
        json_input = {
            "Funding": [
                [
                    55,
                    {
                        "desc": [[55, "National Science Foundation"]],
                        "ID": [[56, "OCE-1358699"]],
                    },
                ]
            ]
        }
        expected_rdfxml = """  <rdf:Description>
    <rdf:type rdf:resource="https://www.eecs.tufts.edu/~wlou01/mf/elements/funding" />
    <dcterms:title>National Science Foundation</dcterms:title>
    <dcterms:identifier>OCE-1358699</dcterms:identifier>
  </rdf:Description>"""
        converted_rdfxml = self.convert(json_input)
        diff = self.find_string_diff(expected_rdfxml, converted_rdfxml)
        assert converted_rdfxml == expected_rdfxml, "\n".join(diff)

    ###############################################################
    # Test for Journal
    def test_case8(self):
        json_input = {
            "Journal": [
                [
                    7,
                    {
                        "desc": [[7, "Nature Scientific Reports"]],
                        "Volume": [[8, "8"]],
                        "Issue": [[9, "1"]],
                        "Pages": [[10, "1-10"]],
                    },
                ]
            ]
        }
        expected_rdfxml = """  <rdf:Description>
    <dcterms:type>text</dcterms:type>
    <dcterms:title>Nature Scientific Reports</dcterms:title>
    <bibo:volume>8</bibo:volume>
    <bibo:issue>1</bibo:issue>
    <bibo:pageStart>1</bibo:pageStart>
    <bibo:pageEnd>10</bibo:pageEnd>
  </rdf:Description>"""
        converted_rdfxml = self.convert(json_input)
        diff = self.find_string_diff(expected_rdfxml, converted_rdfxml)
        assert converted_rdfxml == expected_rdfxml, "\n".join(diff)

    ###############################################################
    # Test for Keyword
    def test_case9(self):
        json_input = {"Keyword": [[59, {"desc": [[59, "Coral"]]}]]}
        expected_rdfxml = """  <dc:subject>
    <dcterms:title>Coral</dcterms:title>
  </dc:subject>"""
        converted_rdfxml = self.convert(json_input)
        diff = self.find_string_diff(expected_rdfxml, converted_rdfxml)
        assert converted_rdfxml == expected_rdfxml, "\n".join(diff)

    ###############################################################
    # Test for MEDFORD
    def test_case10(self):
        json_input = {
            "MEDFORD": [[1, {"desc": [[1, "description"]], "Version": [[2, "1.0"]]}]]
        }
        expected_rdfxml = """  <rdf:Description>
    <rdf:type rdf:resource="https://www.eecs.tufts.edu/~wlou01/mf/elements/medford" />
    <dcterms:title>description</dcterms:title>
    <dcterms:hasVersion>1.0</dcterms:hasVersion>
  </rdf:Description>"""
        converted_rdfxml = self.convert(json_input)
        diff = self.find_string_diff(expected_rdfxml, converted_rdfxml)
        assert converted_rdfxml == expected_rdfxml, "\n".join(diff)

    ###############################################################
    # Test for Method
    def test_case11(self):
        json_input = {
            "Method": [
                [
                    73,
                    {
                        "desc": [[73, "Qiagen DNAeasy Midi kit"]],
                        "Type": [[74, "DNA extraction"]],
                    },
                ]
            ]
        }
        expected_rdfxml = """  <rdf:Description>
    <rdf:type rdf:resource="https://www.eecs.tufts.edu/~wlou01/mf/elements/method" />
    <dcterms:title>Qiagen DNAeasy Midi kit</dcterms:title>
    <dcterms:type>DNA extraction</dcterms:type>
  </rdf:Description>"""
        converted_rdfxml = self.convert(json_input)
        diff = self.find_string_diff(expected_rdfxml, converted_rdfxml)
        assert converted_rdfxml == expected_rdfxml, "\n".join(diff)

    ###############################################################
    # Test for Paper
    def test_case12(self):
        json_input = {
            "Paper": [
                [
                    5,
                    {
                        "Primary": [
                            [
                                5,
                                {
                                    "desc": [
                                        [
                                            5,
                                            "MEDFORD: A human and machine readable markup language to facilitate FAIR coral metadata",
                                        ]
                                    ],
                                    "Note": [
                                        [
                                            6,
                                            "A paper describing the implementation of the MEDFORD file format, which has a parser that can take a provided MEDFORD file and additional arbitrary files and put them into a bag. A MEDFORD file can also be translated into other formats, such as the BCODMO submission format.",
                                        ]
                                    ],
                                },
                            ]
                        ]
                    },
                ]
            ]
        }
        expected_rdfxml = """  <rdf:Description>
    <dcterms:type>text</dcterms:type>
    <mfterms:isPrimary>true</mfterms:isPrimary>
    <dcterms:title>MEDFORD: A human and machine readable markup language to facilitate FAIR coral metadata</dcterms:title>
    <dcterms:description>A paper describing the implementation of the MEDFORD file format, which has a parser that can take a provided MEDFORD file and additional arbitrary files and put them into a bag. A MEDFORD file can also be translated into other formats, such as the BCODMO submission format.</dcterms:description>
  </rdf:Description>"""
        converted_rdfxml = self.convert(json_input)
        diff = self.find_string_diff(expected_rdfxml, converted_rdfxml)
        assert converted_rdfxml == expected_rdfxml, "\n".join(diff)

    ###############################################################
    # Test for Project

    def test_case13(self):
        json_input = {"Project": [[1, {"desc": [[1, "ABC project"]]}]]}

        expected_rdfxml = """  <rdf:Description>
    <rdf:type rdf:resource="https://www.eecs.tufts.edu/~wlou01/mf/elements/project" />
    <dcterms:title>ABC project</dcterms:title>
  </rdf:Description>"""
        converted_rdfxml = self.convert(json_input)
        diff = self.find_string_diff(expected_rdfxml, converted_rdfxml)
        assert converted_rdfxml == expected_rdfxml, "\n".join(diff)

    ###############################################################
    # Test for Software
    def test_case14(self):
        json_input = {
            "Software": [
                [
                    100,
                    {
                        "Primary": [
                            [60, {"desc": [[10, "Testing"]], "Type": [[20, "Python"]]}]
                        ]
                    },
                ]
            ]
        }
        expected_rdfxml = """  <rdf:Description>
    <dcterms:type>software</dcterms:type>
    <mfterms:isPrimary>true</mfterms:isPrimary>
    <dcterms:title>Testing</dcterms:title>
    <dcterms:format>Python</dcterms:format>
  </rdf:Description>"""
        converted_rdfxml = self.convert(json_input)
        diff = self.find_string_diff(expected_rdfxml, converted_rdfxml)
        assert converted_rdfxml == expected_rdfxml, "\n".join(diff)

    ###############################################################
    # Test for Species
    def test_case15(self):
        json_input = {
            "Species": [
                [
                    65,
                    {
                        "desc": [[65, "Pocillopora damicornis"]],
                        "Loc": [[66, "Sabago Isthmus, Panama"]],
                        "ReefCollection": [[67, "March 2005"]],
                        "Cultured": [
                            [68, "University of Miami Coral Resource Facility"]
                        ],
                        "CultureCollection": [[69, "Sept. 2016"]],
                        "Note": [
                            [
                                71,
                                "study used two healthy fragments and two bleached fragments",
                            ]
                        ],
                    },
                ]
            ]
        }
        expected_rdfxml = """  <rdf:Description>
    <rdf:type rdf:resource="https://www.eecs.tufts.edu/~wlou01/mf/elements/species" />
    <dcterms:title>Pocillopora damicornis</dcterms:title>
    <mfterms:loc>Sabago Isthmus, Panama</mfterms:loc>
    <mfterms:reefcollection>March 2005</mfterms:reefcollection>
    <mfterms:cultured>University of Miami Coral Resource Facility</mfterms:cultured>
    <mfterms:culturecollection>Sept. 2016</mfterms:culturecollection>
    <dcterms:description>study used two healthy fragments and two bleached fragments</dcterms:description>
  </rdf:Description>"""
        converted_rdfxml = self.convert(json_input)
        diff = self.find_string_diff(expected_rdfxml, converted_rdfxml)
        assert converted_rdfxml == expected_rdfxml, "\n".join(diff)


if __name__ == "__main__":
    unittest.main()
