"""
Generate markdown representation of a vocabulary.
"""
import datetime
import logging
import typing

import rich.tree

import vocab_tools

L = logging.getLogger("tomarkdown")

def concept_tree(
    top_concept_uri: str,
    concepts: typing.List[vocab_tools.VocabularyConcept],
    level: int = 0,
):
    def _narrower(concept: vocab_tools.VocabularyConcept, llevel=0):
        for narrower_uri in concept.narrower:
            c = vocab_tools.find_concept_in_concept_list(narrower_uri, concepts)
            if c is not None:
                yield c, llevel + 1
            yield from _narrower(c, llevel=llevel + 1)

    top_concept = vocab_tools.find_concept_in_concept_list(top_concept_uri, concepts)
    yield top_concept, level
    yield from _narrower(top_concept, llevel=level)


def describe_concept(
    store: vocab_tools.VocabularyStore,
    concept: vocab_tools.VocabularyConcept,
    level: int = 0,
    is_top_concept: bool = False,
    concept_list: typing.Optional[typing.List[vocab_tools.VocabularyConcept]] = None,
) -> typing.List[str]:
    if concept_list is None:
        concept_list = []
    res = [
        f"{'#' * level} {concept.get_label()}",
        "[]{#" + concept.md_link_label() + "}",
        "",
        #f"The concept `{concept.get_label()}` <br/> ",
        f"URI `{concept.uri}` <br/> ",
        f"defined in vocabulary `{concept.vocabulary}`",
        "",
    ]
    if is_top_concept:
        res.append(f"This is a top concept of the vocabulary.")
    else:
        res.append(f"Path from the top concept: ")
        path = []
        for uri, _ in store.walk_broader(concept.uri):
            path.append(uri)
        path.reverse()
        labels = []
        for uri in path:
            #c = store.concept(uri)
            c = vocab_tools.find_concept_in_concept_list(uri, concept_list)
            if not c is None:
                labels.append(c.md_link(fixed_width=True))
        res.append(f"{'` -> `'.join(labels)}")
    res += ("", "")
    if len(concept.narrower) > 0:
        res.append("Immediately narrower concepts: ")
        narrowers = []
        for c in concept.narrower:
            n = vocab_tools.find_concept_in_concept_list(c, concept_list)
            if n is not None:
                narrowers.append(n)
        res.append(", ".join([n.md_link(fixed_width=True) for n in narrowers]))
    res += (
        "",
        "**Definition: **",
        concept.definition.replace("\n", " <br/> "),
        "",
    )
    if len(concept.notes) > 1:
        res += (
            "**Notes: **",
            "\n\n".join([n.replace("\n", " <br/> ") for n in concept.notes]),
            "",
        )
    if len(concept.label) > 1:
        res += (
            "**Alternate labels: **",
            ", ".join([f"`{lb}`" for lb in concept.label[1:]]),
            "",
        )
    if len(concept.history) > 0:
        res += (
            "**History: **",
            f" <br/> ".join(concept.history),
            "",
        )
    if len(concept.sources) > 0:
        res += (
            "**Sources: **",
            f" <br/> ".join(concept.sources),
            "",
        )
    if len(concept.example) > 0:
        res += (
            "**Example: **",
            f" <br/> ".join(concept.example),
            "",
        )
    return res


def describe_vocabulary(
    store: vocab_tools.VocabularyStore, vocab_uri: str
) -> list[str]:
    V: vocab_tools.Vocabulary = store.vocabulary(vocab_uri)
    res = []
    title = V.label
    # Markdown frontmatter
    description = V.description.split("\n")
    res += (
        "---",
        "comment: | \n  WARNING: This file is generated. Any edits will be lost!",
        f'title: "{title.strip()}"',
        f'date: "{datetime.datetime.now().replace(tzinfo=datetime.timezone.utc).isoformat()}"',
        "subtitle: |",
    )
    for row in description:
        res.append(f"  {row}")
    res += (
        "execute:",
        "  echo: false",
        "---",
        "",
    )
    # Document content
    res += ("Vocabularies and extensions: ", "")
    for uri, depth in store.walk_vocab_tree(vocab_uri):
        voc = store.vocabulary(uri)
        res.append(f"{'  '*depth}- `{voc.label}` [`{voc.uri}`]({voc.uri})")
    res += (
        "",
        "**History:**",
        "",
        " <br /> ".join(V.history),
        "",
    )
    for history in store._get_objects(vocab_uri, vocab_tools.skosT("historyNote")):
        res.append(f"* {history}")
    res += (
        "",
        "**Concept Hierarchy:**",
        "",
    )
    depth = 1
    base_vocabulary = store.base_vocabulary()
    concept_uris = store.concepts()
    all_concepts = [store.concept(uri) for uri in concept_uris]
    top_concepts = []
    try:
        #top_concepts = [store.top_concept(), ]
        top_concepts = store.top_concept()

        L.debug(f"count Top concepts: {len(top_concepts)}")
    except ValueError as e:
        L.warning("No top level concept found.")
        # Since there's no top concept available, find the concepts
        # where the parent lineage is shortest and use those as starting
        # points to traverse the vocabulary
        res += (
            "> **Note**",
            "> No top level concept is available in the loaded vocabularies. ",
            "> Hierarchy is generated from the broadest concepts available.",
            "",
        )
        for concept in all_concepts:
            broaders = [c for c in store.walk_broader(concept.uri)]
            if len(broaders) < 3:
                top_concepts.append(concept)
    for top_concept in top_concepts:

        L.debug(f"Top concept.uri: {top_concept.uri}")
        for concept, level in concept_tree(top_concept.uri, all_concepts, level=depth):
            label = f"{'  '*level}- [{concept.get_label()}](#{concept.md_link_label()})"
            res.append(label)
        res += ("", "")
    for top_concept in top_concepts:
        res += describe_concept(store, top_concept, level=2, is_top_concept=True, concept_list=all_concepts)
    #res += top_concept.markdown(level=2, concept_list=all_concepts)
        res.append("")
    #for top_concept in top_concepts:
        for uri, level in store.walk_narrower(top_concept.uri, level=3):
            L.debug(f"walk narrower, uri: {uri}, level: {level}")
            concept = vocab_tools.find_concept_in_concept_list(uri, all_concepts)
            #res += concept.markdown(level=level, concept_list=all_concepts)
            res += describe_concept(store, concept, level=level, concept_list=all_concepts)
            res.append("")
    return res
