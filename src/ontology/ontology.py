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
    body = "\n"

    with open(DATA_PATH / "klink2" / f"{named_list}_triples.csv", "r") as f:
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

    with open(DATA_PATH / "ontology" / f"{named_list}.ttl", "w") as f:
        f.write(ontology_str)

    print(f"File exported to {DATA_PATH / 'ontology' / named_list}.ttl")
