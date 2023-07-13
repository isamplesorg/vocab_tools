"""Script for validating and generating vocabulary artifacts.
"""
import importlib.resources
import logging
import os
import sys
import typing

import click
import pyshacl
import rdflib
import rich.logging

import vocab_tools

DEFAULT_SHAPE = "data/vocabulary_shape.ttl"


FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[rich.logging.RichHandler()]
)
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


@click.group()
def main():
    pass

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
        dataset.g,
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


@main.command()
def markdown():
    """Generate markdown representation of the vocabulary.

    """
    pass


if __name__ == "__main__":
    sys.exit(main())

