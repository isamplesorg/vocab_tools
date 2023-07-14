"""
Generate markdown representation of a vocabulary.
"""
import datetime
import typing

import vocab_tools


def concept_tree(top_concept_uri: str, concepts:typing.List[vocab_tools.VocabularyConcept], level:int=0):

    def _narrower(concept: vocab_tools.VocabularyConcept, llevel=0):
        for narrower_uri in concept.narrower:
            c = vocab_tools.find_concept_in_concept_list(narrower_uri, concepts)
            if c is not None:
                yield c, llevel+1
            yield from _narrower(c, llevel=llevel+1)

    top_concept = vocab_tools.find_concept_in_concept_list(top_concept_uri, concepts)
    yield top_concept, level
    yield from _narrower(top_concept, llevel=level)


def describe_vocabulary(store:vocab_tools.VocabularyStore, vocab_uri:str)-> list[str]:
    V: vocab_tools.Vocabulary = store.vocabulary(vocab_uri)
    res = []
    title = V.label
    # Markdown frontmatter
    res += (
        "---",
        "comment: | \n  WARNING: This file is generated. Any edits will be lost!",
        f"title: \"{title.strip()}\"",
        f"date: \"{datetime.datetime.now().replace(tzinfo=datetime.timezone.utc).isoformat()}\"",
        "subtitle: |",
        f"  {V.description}",
        "execute:",
        "  echo: false",
        "---",
        "",
    )
    # Document content
    res += (
        "Namespace: ",
        f"[`{V.uri}`]({V.uri})",
        "",
        "**History**",
        "",
    )
    for history in store._get_objects(vocab_uri, vocab_tools.skosT("historyNote")):
        res.append(f"* {history}")
    res += (
        "",
        "**Concepts**",
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
    res += top_concept.markdown(level=2)
    res.append("")
    for uri, level in store.walk_narrower(top_concept.uri, level=3):
        concept = vocab_tools.find_concept_in_concept_list(uri, all_concepts)
        res += concept.markdown(level=level, concept_list=all_concepts)
        res.append("")
    return res
