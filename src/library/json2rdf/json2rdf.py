from rdflib import Graph, Literal, Namespace, RDF, URIRef, DC
import xml.etree.ElementTree as ET
from datetime import datetime
import sys


sys.path.append("..")
# MFTERMS = Namespace("https://mf.cs.tufts.edu/mf/terms/")
# MF=Namespace("https://mf.cs.tufts.edu/mf/elements/")
MFTERMS = Namespace("https://www.eecs.tufts.edu/~wlou01/mf/terms/")
MF = Namespace("https://www.eecs.tufts.edu/~wlou01/mf/elements/")
BIBO = Namespace("http://purl.org/ontology/bibo/")
DCTERMS = Namespace("http://purl.org/dc/terms/")
IMS = Namespace("http://www.imsglobal.org/xsd/imsmd_v1p2/")
VCARD = Namespace("https://www.w3.org/2006/vcard/ns#")


class jsonToRdf:
    # initialize graph and read json data
    def __init__(self, json_data):
        self.json_data = json_data
        self.G = Graph()

    # mapping MEDFORD tags
    def checkSubject(self, prop, parent):
        term = prop.lower()

        sub = ""
        if term == "association":
            sub = getattr(DCTERMS, "publisher")
        elif term == "cruiseid":
            sub = getattr(MFTERMS, "cruiseID")
        elif term == "desc":
            if parent == getattr(MF, "date"):
                sub = getattr(DCTERMS, "date")
            elif parent == getattr(MF, "contributor"):
                sub = getattr(VCARD, "fn")
            else:
                sub = getattr(DCTERMS, "title")
        elif term == "divenumber":
            sub = getattr(MFTERMS, "diveNumber")
        elif term == "doi":
            sub = getattr(DCTERMS, "identifier")
        elif term == "email":
            sub = getattr(VCARD, "email")
        elif term == "id":
            sub = getattr(DCTERMS, "identifier")
        elif term == "issue":
            sub = getattr(BIBO, "issue")
        elif term == "link":
            sub = getattr(DCTERMS, "source")
        elif term == "note":
            sub = getattr(DCTERMS, "description")
        elif term == "orcid":
            sub = getattr(DCTERMS, "identifier")
        elif term == "mooringid":
            sub = getattr(MFTERMS, "mooringID")
        elif term == "pages":
            sub = getattr(BIBO, "pageStart")
        elif term == "pmid":
            sub = getattr(BIBO, "pmid")
        elif term == "version":
            sub = getattr(DCTERMS, "hasVersion")
        elif term == "volume":
            sub = getattr(BIBO, "volume")
        elif term == "role":
            sub = getattr(VCARD, "role")
        elif term == "shipname":
            sub = getattr(MFTERMS, "shipName")
        elif term == "size":
            sub = getattr(DCTERMS, "extent")
        elif term == "type":
            if "code" in parent:
                sub = getattr(DCTERMS, "subject")
            elif "data" in parent:
                sub = DCTERMS["format"]
            elif "software" in parent:
                sub = DCTERMS["format"]
            else:
                sub = getattr(DCTERMS, "type")
        elif term == "uri":
            sub = getattr(DCTERMS, "source")
        else:
            sub = getattr(MFTERMS, term)

        return sub

    # add properties for mf major tokens
    def add_majorToken_to_graph(self, mfword, subject_url):
        # add dc properties for all undecided mf terms
        predicate = ""
        obj = ""
        # print(mfword)
        if mfword == "code":
            self.G.add((subject_url, RDF.type, MF["code"]))
            predicate = RDF.type
            obj = MF["code"]
        elif mfword == "data":
            self.G.add((subject_url, DCTERMS.type, Literal("dataset")))
            predicate = DCTERMS.type
            obj = Literal("dataset")
        elif mfword == "expedition":
            self.G.add((subject_url, RDF.type, MF["expedition"]))
            predicate = RDF.type
            obj = MF["expedition"]
        elif mfword == "file":
            self.G.add((subject_url, DCTERMS.type, Literal("format")))
            predicate = DCTERMS.type
            obj = Literal("format")
        elif mfword == "freeform":
            self.G.add((subject_url, RDF.type, MF["freeform"]))
            predicate = RDF.type
            obj = MF["freeform"]
        elif mfword == "funding":
            self.G.add((subject_url, RDF.type, MF["funding"]))
            predicate = RDF.type
            obj = MF["funding"]
        elif mfword == "journal":
            self.G.add((subject_url, DCTERMS.type, Literal("text")))
            predicate = DCTERMS.type
            obj = Literal("text")
        elif mfword == "medford":
            self.G.add((subject_url, RDF.type, MF["medford"]))
            predicate = RDF.type
            obj = Literal("text")
        elif mfword == "method":
            self.G.add((subject_url, RDF.type, MF["method"]))
            predicate = RDF.type
            obj = Literal("text")
        elif mfword == "paper":
            self.G.add((subject_url, DCTERMS.type, Literal("text")))
            predicate = DCTERMS.type
            obj = Literal("text")
        elif mfword == "project":
            self.G.add((subject_url, RDF.type, MF["project"]))
            predicate = RDF.type
            obj = Literal("project")
        elif mfword == "species":
            self.G.add((subject_url, RDF.type, MF["species"]))
            predicate = RDF.type
            obj = MF["species"]
        elif mfword == "software":
            self.G.add((subject_url, DCTERMS.type, Literal("software")))
            predicate = DCTERMS.type
            obj = Literal("software")
        return predicate, obj

    # add properties for mf sub tokens
    def add_minorToken_to_graph(self, second, subject_url):
        # add ref, primary, copy as properties too
        if second == "ref":

            self.G.add((subject_url, MFTERMS["isRef"], Literal("true")))
        elif second == "primary":

            self.G.add((subject_url, MFTERMS["isPrimary"], Literal("true")))
        elif second == "copy":

            self.G.add((subject_url, MFTERMS["isCopy"], Literal("true")))
        elif second == "freeform":
            self.G.add((subject_url, RDF.type, MF["freeform"]))

    # Function to convert nested JSON data to RDF triples in graph

    def json_to_graph(self):

        # Read the json data
        for key, value in self.json_data.items():
            subject = None

            subject = getattr(MF, key.lower())
            self.helper(value, subject, "none")

    # helper function for json_to_graph
    def helper(self, value, psubject, second):

        mfword = ""
        # get the mf terms from the resource
        for word in [
            "code",
            "data",
            "expedition",
            "file",
            "freeform",
            "funding",
            "journal",
            "medford",
            "method",
            "paper",
            "project",
            "software",
            "species",
        ]:
            if word in psubject:
                # print("word:"+word)
                mfword = word

        for item in value:

            # id
            if not isinstance(item[0], int):
                print("Invalid BEDFORD JSON format.")
                sys.exit(1)
            item_id = item[0]
            # item
            item_data = item[1]

            subject_url = psubject + "/" + str(item_id)
            # print(subject_url)

            predicate, obj = self.add_majorToken_to_graph(mfword, subject_url)

            self.add_minorToken_to_graph(second, subject_url)

            # add the triple to the graph
            for prop, prop_value in item_data.items():

                length_of_multipro = len(prop_value)

                prop_val = ""

                # if one tag has more than one value and there is no dictionary
                # data inside the list,concatenate the values together
                if length_of_multipro > 1 and type(prop_value[0][1]) != dict:
                    for i in range(length_of_multipro):
                        prop_id = prop_value[i][0]
                        if not isinstance(prop_id, int):
                            print("Invalid BEDFORD JSON format.")
                            sys.exit(1)
                        prop_val = prop_val + prop_value[i][1] + ", "
                    prop_val = prop_val[:-2]

                else:
                    if not isinstance(prop_value[0][0], int):
                        print("Invalid BEDFORD JSON format.")
                        sys.exit(1)
                    prop_val = prop_value[0][1]

                sub_subject = ""

                # if the data is value only
                if type(prop_val) != dict:

                    sub_subject = self.checkSubject(prop, psubject)
                    # adjust predicates
                    if "date" in sub_subject:
                        try:
                            datetime.strptime(prop_val, "%Y-%m-%d")
                            dcdate = datetime.strptime(prop_val, "%Y-%m-%d").date()

                            self.G.add((subject_url, DCTERMS["date"], Literal(dcdate)))
                        except ValueError:

                            try:
                                datetime.strptime(prop_val, "%Y-%m-%d %H:%M:%S")
                                imsdatetime = datetime.strptime(
                                    prop_val, "%Y-%m-%d %H:%M:%S"
                                )
                                self.G.add(
                                    (subject_url, IMS["datetime"], Literal(imsdatetime))
                                )
                            except ValueError:
                                self.G.add(
                                    (subject_url, DCTERMS["date"], Literal(prop_val))
                                )
                    # retrived pageStart and pageEnd from pages
                    elif "pageStart" in sub_subject:
                        start, end = prop_val.split("-")
                        self.G.add((subject_url, BIBO["pageStart"], Literal(start)))
                        self.G.add((subject_url, BIBO["pageEnd"], Literal(end)))
                    elif "source" in sub_subject:
                        # Add the dcterms:source property with the URI value
                        source_uri = URIRef(prop_val)
                        self.G.add((subject_url, DCTERMS["source"], source_uri))
                    else:
                        self.G.add((subject_url, sub_subject, Literal(prop_val)))

                else:

                    # when there is a minor token,we need to remove the latest
                    # added triple first and add it in the next level
                    self.G.remove((subject_url, predicate, obj))
                    temp = list(item_data.keys())[0].lower()
                    if mfword == "freeform":
                        psubject = getattr(MF, temp)
                        temp = "freeform"
                    # for the second layer of the minor token or
                    # when the value is a list of multiple dictionary values
                    self.helper(prop_value, psubject, temp)

    # parse graph to rdf/xml bytes data

    def graph_to_rdfxml(self):

        # Serialize the graph to RDF/XML format
        rdf_xml_data = self.G.serialize(format="xml")

        # Parse the RDF/XML data
        root = ET.fromstring(rdf_xml_data)

        # Register desired namespaces and prefixes
        ET.register_namespace("mf", MF)
        ET.register_namespace("mfterms", MFTERMS)
        ET.register_namespace("bibo", BIBO)
        ET.register_namespace("dcterms", DCTERMS)
        ET.register_namespace("ims", IMS)
        ET.register_namespace("vcard", VCARD)

        # Add the xmlns:dc attribute to the root element
        root.set("xmlns:dc", DC)

        # Find the dcterms:source element using the full namespace URI
        source_elem = root.find(".//{%s}source" % DCTERMS)

        if source_elem is not None:
            # Change the tag of the dcterms:source element
            source_elem.tag = "{%s}source" % DCTERMS

        # change the major token namespace
        for elem in root.iter():

            if elem.tag.endswith("Description"):
                # Get the 'about' attribute value of the element
                about_value = elem.attrib.get(
                    "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about"
                )

                # Get namespace
                elem_namespace = about_value.rsplit("/", 1)[0]
                term = elem_namespace.rsplit("/", 1)[1]

                if term in ["contributor", "date"]:
                    term = elem_namespace.rsplit("/", 1)[1]
                    elem.tag = "dc:" + term
                elif term == "keyword":
                    term = elem_namespace.rsplit("/", 1)[1]
                    elem.tag = "dc:" + "subject"
                # by default the elem.tag is rdf:Description

                # Remove the 'about' attribute from the element
                elem.attrib.pop(
                    "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about", None
                )

        # Convert the modified XML tree back to as bytes
        rdf_xml_data_bytes = ET.tostring(root)

        return rdf_xml_data_bytes
