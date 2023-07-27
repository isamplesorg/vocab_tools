"""
Generate markdown representation of a vocabulary.
"""
import datetime
import typing

import rich.tree

import vocab_tools


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
        f"| The concept `{concept.get_label()}` \n| with URI `{concept.uri}` \n| is defined in vocabulary `{concept.vocabulary}`",
        "",
    ]
    if is_top_concept:
        res.append(f"This is the top concept of the vocabulary.")
    else:
        res.append(f"| Path from the top concept:")
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
        res.append(f"|   {'` -> `'.join(labels)}")
    res += ("", "")
    if len(concept.narrower) > 0:
        res.append("Immediately narrower concepts:\n")
        narrowers = []
        for c in concept.narrower:
            n = vocab_tools.find_concept_in_concept_list(c, concept_list)
            if n is not None:
                narrowers.append(n)
        res.append(", ".join([n.md_link(fixed_width=True) for n in narrowers]))
    res += (
        "",
        "| Definition:",
        "|  " + concept.definition.replace("\n", "\n|  "),
        "",
    )
    if len(concept.notes) > 1:
        res += (
            "| Notes:",
            "|  " + "\n|  ".join([n.replace("\n", "\n|  ") for n in concept.notes]),
            "",
        )
    if len(concept.label) > 1:
        res += (
            "| Alternate labels:",
            "|  " + ", ".join([f"`{lb}`" for lb in concept.label[1:]]),
            "",
        )
    if len(concept.history) > 0:
        res += (
            "| History:",
            "|  " + "|  ".join(concept.history),
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
    res += (
        "---",
        "comment: | \n  WARNING: This file is generated. Any edits will be lost!",
        f'title: "{title.strip()}"',
        f'date: "{datetime.datetime.now().replace(tzinfo=datetime.timezone.utc).isoformat()}"',
        "subtitle: |",
        f"  {V.description}",
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
        "History:",
        "",
        "|  " + "\n|  ".join(V.history),
        "",
    )
    for history in store._get_objects(vocab_uri, vocab_tools.skosT("historyNote")):
        res.append(f"* {history}")
    res += (
        "",
        "Concept Hierarchy:",
        "",
    )
    depth = 1
    base_vocabulary = store.base_vocabulary()
    concept_uris = store.concepts()
    all_concepts = [store.concept(uri) for uri in concept_uris]
    top_concept = store.top_concept()
    for concept, level in concept_tree(top_concept.uri, all_concepts, level=depth):
        label = f"{'  '*level}- [{concept.get_label()}](#{concept.md_link_label()})"
        res.append(label)
    res += ("", "")
    res += describe_concept(store, top_concept, level=2, is_top_concept=True, concept_list=all_concepts)
    #res += top_concept.markdown(level=2, concept_list=all_concepts)
    res.append("")
    for uri, level in store.walk_narrower(top_concept.uri, level=3):
        concept = vocab_tools.find_concept_in_concept_list(uri, all_concepts)
        #res += concept.markdown(level=level, concept_list=all_concepts)
        res += describe_concept(store, concept, level=2, concept_list=all_concepts)
        res.append("")
    return res
