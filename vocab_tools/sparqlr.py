import fastapi
import rdflib_endpoint
import uvicorn

# list named graphs
example_query = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?s ?p ?o
WHERE { ?s ?p ?o . }
"""

example_queries = {
    "graphs": {
        "query": """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT DISTINCT ?g 
WHERE {
  GRAPH ?g { ?s ?p ?o }
}"""},
    "vocabularies": {
        "query": """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?vocab ?broader
WHERE {
  ?vocab rdf:type skos:ConceptScheme .
}
"""},
    "concepts": {
        "query": """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?concept ?broader
WHERE {
  ?concept rdf:type skos:Concept .
  OPTIONAL {
    ?concept skos:broader ?broader .
  } .
}"""
    }
}

def run_service(g, port:int=9000, host:str="localhost") -> None:
    app = rdflib_endpoint.SparqlEndpoint(
        graph=g,
        path="/",
        title="Vocabulary SPARQL",
        cors_enabled=True,
        example_query=example_query,
        example_queries=example_queries
    )
    uvicorn.run(app, host=host, port=port)
