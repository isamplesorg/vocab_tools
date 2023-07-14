# vocab_tools

Python tools for validating and rendering iSamples vocabularies.

## Validate a vocabulary

```
$ vocab validate tests/data/example.ttl
[06:47:07] INFO     Loaded vocabulary https://example.net/my/minimal/vocab
           INFO     SHACL conformance: True
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