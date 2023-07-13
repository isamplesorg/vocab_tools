"""Script for validating and generating vocabulary artifacts.
"""
import importlib.resources
import logging
import sys
import typing

import click
import rich.logging

import navocab

DEFAULT_SHAPE = "data/vocabulary_shape.ttl"

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[rich.logging.RichHandler()]
)
L = logging.getLogger("")

@click.group()
def main():
    t = importlib.resources(navocab)
    for f in t:
        print(f)
    pass

@main.command()
@click.argument("source", nargs=1)
@click.option("-v", "--vocab", default=None, help="Vocabulary to load", multiple=True)
@click.option("-s", "--shape", default=DEFAULT_SHAPE, help="SHACL shape file for vocabulary structure validation")
def validate(source: str, vocab:typing.List[str]):
    dataset = navocab.VocabularyStore()
    for v in vocab:
        dataset.load(v)
    dataset.load(source)
    for vocab in dataset.vocabularies():
        print(vocab)

if __name__ == "__main__":
    sys.exit(main())

