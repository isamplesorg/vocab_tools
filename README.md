# vocab_tools

Python tools for validating and rendering iSamples vocabularies.

## Validate a vocabulary

Valid vocabulary:
```
$ vocab validate example/data/example.ttl
Loaded vocabulary https://example.net/my/minimal/vocab
SHACL conformance: True
```

Vocabulary with no top concept:
```
$ vocab validate example/data/example_notop.ttl
SHACL conformance: False
Validation Report
Conforms: False
Results (2):
20 of 21 applied.
Constraint Violation in OrConstraintComponent (http://www.w3.org/ns/shacl#OrConstraintComponent):
	Severity: sh:Violation
	Source Shape: skos:VocabularyShape
	Focus Node: eg:vocab
	Value Node: eg:vocab
	Message: Node eg:vocab does not conform to one or more shapes in skos:ExtensionVocabularyShape , skos:BaseVocabularyShape
Constraint Violation in OrConstraintComponent (http://www.w3.org/ns/shacl#OrConstraintComponent):
	Severity: sh:Violation
	Source Shape: skos:VocabularyConceptShape
	Focus Node: eg:thing
	Value Node: eg:thing
	Message: Node eg:thing does not conform to one or more shapes in skos:NarrowerConceptShape , skos:TopConceptShape

Vocabulary not in conformance. Skipping further tests.
```

## Generate Markdown

```
$ vocab validate example/data/example.ttl > example/example.md 
```

## Installation

Use poetry for development work.

For other use, create a python virtual environment and 

```
pip install git+https://github.com/isamplesorg/vocab_tools.git@main
```

To enable the SPARQL service endpoint, also install `uvicorn` and `rdflib-endpoint`:
```
pip install uvicorn git+https://github.com/vemonet/rdflib-endpoint.git@main
```