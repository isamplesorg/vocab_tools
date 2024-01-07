"""Script for validating and generating vocabulary artifacts.
"""
import importlib.resources
import json
import logging
import os
import sys
import typing

import click
import pyshacl
import rdflib
import rich.logging

import vocab_tools
import vocab_tools.tomarkdown

DEFAULT_SHAPE = "data/vocabulary_shape.ttl"


FORMAT = "%(message)s"
L = logging.getLogger("")


def get_shape(path:typing.Optional[str] = None) -> typing.Optional[rdflib.Graph]:
    """
    Returns the SHACL shape as rdflib graph.
    """
    if path is not None:
        if not os.path.exists(path):
            L.error("No SHACL file at %s", path)
            return None
    else:
        path = str(importlib.resources.files(vocab_tools).joinpath(DEFAULT_SHAPE))
    g = rdflib.ConjunctiveGraph()
    return g.parse(path)


def getDefaultVocabulary(vs:vocab_tools.VocabularyStore, abbreviate:bool=False) -> str:
    vocabs = vs.vocabulary_list(abbreviate=abbreviate)
    vocabulary = vocabs[0]
    if len(vocabs) > 1:
        L.warning("More than one vocabulary in store. Using: %s", vocabulary)
    return vocabulary


@click.group()
def main():
    logging.basicConfig(
        level="INFO", format=FORMAT, datefmt="[%X]"
    )

@main.command()
@click.argument("source", nargs=1)
@click.option("-v", "--vocab", default=None, help="Vocabulary to load", multiple=True)
@click.option("-s", "--shape", default=None, help="SHACL shape file for vocabulary structure validation")
def validate(source: str, vocab:typing.List[str], shape:typing.Optional[str]):
    """Validate vocabulary structure.
    """
    dataset = vocab_tools.VocabularyStore()
    dataset.load(source)
    shape_graph = get_shape(shape)
    conforms, results_graph, results = pyshacl.validate(
        dataset.graph,
        shacl_graph = shape_graph,
        inference='rdfs',
        abort_on_first=False,
        allow_warnings=True,
        meta_shacl=False,
        advanced=True,
        js=False,
        debug=False
    )
    L.info("SHACL conformance: %s", conforms)
    if not conforms:
        # Show problems
        print(results)
        L.error("Vocabulary not in conformance. Skipping further tests.")
        return
    for v in vocab:
        dataset.load(v)
    # TODO: additional tests
    #   - resolvable terms
    #   - all leaves connected to a topConcept


@main.command("uijson")
@click.argument("sources", nargs=-1)
@click.option(
    "-e", "--extensions", is_flag=True, help="Traverse vocabulary extensions"
)
def uijson(sources, extensions):
    """Render VOCABULARY as JSON suitable for inclusion in iSamples WebUI.
    """
    def _narrower(s, v, c, indent=0, level=0, max=100):
        ns = s.narrower(c, v, abbreviate=False)
        for n in ns:
            entry = _json_for_uri_ref(n, s)
            if level < max:
                for nn in _narrower(s, v, n, indent=indent + 2, level=level + 1, max=max):
                    entry["children"].append(nn)
            yield entry

    def _json_for_uri_ref(n: rdflib.URIRef, s: rdflib.store.Store):
        _c = s.concept(n)
        # TODO: use provided lang instead of assuming everything is @en
        entry = {
            "concept": str(n),
            "label": {
                "en": _c.label[0] if len(_c.label) > 0 else str(s.compact_name(n))
            },
            "children": []
        }
        return entry

    def _convert_to_ui_format(entry: dict) -> dict:
        child_dict = {
            "label": entry["label"]
        }
        ui_dict = {
            entry["concept"]: child_dict
        }
        children = []
        for child in entry["children"]:
            children.append(_convert_to_ui_format(child))
        child_dict["children"] = children
        return ui_dict

    raise NotImplementedError("Json generation needs to be updated.")
    dataset = vocab_tools.VocabularyStore()
    for source in sources:
        dataset.load(source)
    vocabularies = dataset.vocabularies()
    base_vocabulary = dataset.base_vocabulary()
    top_concept = dataset.top_concept()  # note this returns a list, or throws error
    concept, vocabulary = dataset.getVocabRoot(None)
    L.info("Using vocabulary %s", base_vocabulary)
    L.debug("Using %s as root concept", top_concept)
    if extensions:
        vocabulary = None
    result = []
    for n in _narrower(dataset, vocabulary, concept):
        result.append(n)
    root_entry = _json_for_uri_ref(rdflib.URIRef(concept), dataset)
    for child in result:
        root_entry["children"].append(child)

    # Note that due to the way the RDF queries are structured, if we construct the dictionaries in the format
    # the UI expects while we are iterating, the RDF query blows up.  So, keep it in one format while iterating and
    # convert when done.
    root_entry = _convert_to_ui_format(root_entry)
    print(json.dumps(root_entry, indent=2))


@main.command()
@click.argument("sources", nargs=-1)
def markdown(sources):
    """Generate markdown representation of the vocabulary.
    """
    store = vocab_tools.VocabularyStore()
    for source in sources:
        store.load(source)
    vocab = store.base_vocabulary()
    # TODO: enable presentation of individual extensions
    #   This will require the renderer to handle multiple top level concepts
    #   with those concepts being the external concepts referenced by the extension.
    vocab_docs = [vocab_tools.tomarkdown.describe_vocabulary(store, vocab.uri), ]
    for document in vocab_docs:
        for line in document:
            print(line)


@main.command("sparqlr")
@click.argument("sources", nargs=-1)
@click.option("--host", default="localhost", help="Hostname for service")
@click.option("-p", "--port", default=9000, help="Port for service listener")
def sparqler(sources, host, port):
    """Run a SPARQL endpoint for querying loaded vocabularies.

    e.g.: vocab sparqlr tests/data/example.ttl tests/data/extension_example.ttl
    """
    try:
        import vocab_tools.sparqlr
    except ImportError:
        L.error("Please pip install rdflib-endpoint and uvicorn to enable the sparqlet service.")
        L.info("pip install uvicorn git+https://github.com/vemonet/rdflib-endpoint.git@main")
        return
    store = vocab_tools.VocabularyStore()
    for source in sources:
        store.load(source)
    vocab_tools.sparqlr.run_service(store.graph, host=host, port=port)


if __name__ == "__main__":
    sys.exit(main())

