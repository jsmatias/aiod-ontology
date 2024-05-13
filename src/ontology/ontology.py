from config import DATA_PATH


HEADER = (
    "@prefix : <http://http://aiod.eu/schema/aiod#> .\n"
    "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
    "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n"
    "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
    "@base <http://http://aiod.eu/schema/aiod#> .\n"
    "\n"
    "<http://http://aiod.eu/schema/aiod#> rdf:type owl:Ontology ;\n"
    '                                         dc:title "AIoD Ontology"@en ;\n'
    '                                         dc:description "AI on demand"@en .\n'
)

PREDICATE_DICT = {
    "klink:relatedEquivalent": "Related Equivalent",
    "klink:broaderGeneric": "Broader Generic",
    "klink:contributesTo": "Contributes To",
}


def export_ontology(named_list: str):
    """
    Export ontology from a named list.

    Args:
        named_list (str): Name of the list.

    Raises:
        Exception: If the triples file is not found.

    Prints:
        str: Confirmation message with the exported file path.
    """
    body = "\n"

    triples_path = DATA_PATH / "klink2" / named_list / f"{named_list}_triples.csv"
    if not triples_path.is_file():
        raise Exception(
            f"File {triples_path} not found. Make sure the triples were generated and saved correctly."
        )
    with open(triples_path, "r") as f:
        lines = f.readlines()
    i = 1
    for line in lines[1:]:
        kw1, kw2, predicate = line.split(";")
        label = PREDICATE_DICT[predicate.strip()]
        kw1 = kw1.replace(" ", "_").replace(".", "").replace("(", "_").replace(")", "_")
        kw2 = kw2.replace(" ", "_").replace(".", "").replace("(", "_").replace(")", "_")

        relation = (
            f":RE{i} a owl:ObjectProperty ;\n"
            f"   rdfs:domain :{kw1.strip()} ;\n"
            f"   rdfs:range :{kw2.strip()} ;\n"
            f'   rdfs:label "{label}"@en .\n'
        )
        body += "\n" + relation
        i += 1
    ontology_str = HEADER + body

    ontology_file_path = DATA_PATH / "ontology" / f"{named_list}.ttl"
    with open(ontology_file_path, "w") as f:
        f.write(ontology_str)

    print(f"File exported to {ontology_file_path}")
