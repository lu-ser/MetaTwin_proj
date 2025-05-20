from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, OWL
import json
# Crea un grafico e carica l'ontologia
g = Graph()
g.parse("onto.owl")

# Namespace per l'ontologia specifica, se necessario
ONTO = Namespace("http://www.semanticweb.org/jbagwell/ontologies/2017/9/untitled-ontology-6#")

# Query SPARQL per ottenere classi, commenti e gerarchie
query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX onto: <http://www.semanticweb.org/jbagwell/ontologies/2017/9/untitled-ontology-6#>

SELECT ?class ?superclass WHERE {
    ?class rdf:type owl:Class .
    OPTIONAL {?class rdfs:subClassOf ?superclass}
    FILTER (STRSTARTS(STR(?class), STR(onto:)))
}
"""

# Esegui la query
results = g.query(query)

# Creazione della mappa per la gerarchia
class_hierarchy = {}

for row in results:
    class_name = row[0].split('#')[-1] if '#' in str(row[0]) else str(row[0])
    superclass_name = row[1].split('#')[-1] if '#' in str(row[1]) and row[1] else "No superclass"

    if class_name in class_hierarchy:
        # Aggiungi il commento se non già presente
        class_hierarchy[class_name].setdefault('superclass', []).append(superclass_name)
    else:
        class_hierarchy[class_name] = {
            'superclass': [superclass_name] if superclass_name != "No superclass" else []
        }

# Serializza in JSON
json_hierarchy = json.dumps(class_hierarchy, indent=4)
print(json_hierarchy)

# Salvare in un file
with open("class_hierarchy.json", "w") as outfile:
    outfile.write(json_hierarchy)
