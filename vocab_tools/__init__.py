"""
Provides a convenience wrapper for vocabularies expressed in SKOS rdf.

Part of the iSamples project.
"""
import dataclasses
import logging
import typing
import rdflib
import rdflib.namespace
import rdflib.plugins.sparql

#TODO: this is too specific:
STORE_IDENTIFIER = "https://w3id.org/isample/vocabulary"

#TODO: should use namespaces from rdflib
NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "obo": "http://purl.obolibrary.org/obo/",
    "dcterm": "http://purl.org/dc/terms/",
    "schema": "https://schema.org/",
    "geosciml": "http://resource.geosciml.org/classifier/cgi/lithology",
}


L = logging.getLogger("navocab")


def skosT(term):
    return rdflib.URIRef(f"{NS['skos']}{term}")


def rdfT(term):
    return rdflib.URIRef(f"{NS['rdf']}{term}")


def rdfsT(term):
    return rdflib.URIRef(f"{NS['rdfs']}{term}")

def dctermT(term):
    return rdflib.URIRef(f"{NS['rdfs']}{term}")


def find_concept_in_concept_list(
    uri: str, concept_list: typing.List["VocabularyConcept"]
) -> typing.Optional["VocabularyConcept"]:
    for c in concept_list:
        if str(c.uri) == str(uri):
            return c
    return None


@dataclasses.dataclass
class VocabularyConcept:
    uri: str
    name: str  # Last part of the URI, foo#name or foo/name
    label: typing.List[str]
    definition: str
    broader: typing.List[str]
    narrower: typing.List[str]
    vocabulary: str
    history: typing.List[str] = dataclasses.field(default_factory=list)
    sources: typing.List[str] = dataclasses.field(default_factory=list)
    notes: typing.List[str] = dataclasses.field(default_factory=list)
    #scopenote: typing.List[str] = dataclasses.field(default_factory=list)
    related: typing.List[str] = dataclasses.field(default_factory=list)
    example: typing.List[str] = dataclasses.field(default_factory=list)
    #changenote: typing.List[str] = dataclasses.field(default_factory=list)

    def get_label(self):
        tag = self.name
        if len(self.label) > 0:
            tag = self.label[0]
        return tag

    def md_link_label(self):
        tag = self.get_label()
        tag = tag.strip()
        tag = tag.split("/")[-1]
        tag = tag.lower().strip()
        tag = tag.replace(",", "")
        tag = tag.replace(" ", "-")
        tag = tag.replace("'", "")
        return tag

    def md_link(self, fixed_width=False):
        if fixed_width:
            return f"[`{self.get_label()}`](#{self.md_link_label()})"
        return f"[{self.get_label()}](#{self.md_link_label()})"

    def markdown(
        self, level=1, concept_list: typing.List["VocabularyConcept"] = None
    ) -> typing.List[str]:
        """Return lines of markdown describing self.

        Level is the heading level for the block.

        concept_list is an optional list of loaded VocabularyConcept instances.
        """
        if concept_list is None:
            concept_list = []
        res = [
            f"{'#' * level} {self.get_label()}",
            "[]{#" + self.md_link_label() + "}",
            "",
            f"`{self.uri}` in vocabulary `{self.vocabulary}`",
            "",
            f"Concept: {self.md_link()}",
            "",
        ]
        if len(self.broader) > 0:
            res.append("Broader Concepts:")
            res.append("")
            for broader in self.broader:
                if len(concept_list) > 0:
                    bc = find_concept_in_concept_list(broader, concept_list)
                    res.append(f"- {bc.md_link()}")
                else:
                    res.append(f"- {broader}")
            res.append("")
        if len(self.narrower) > 0:
            res.append("Narrower Concepts:")
            res.append("")
            for narrower in self.narrower:
                if len(concept_list) > 0:
                    nc = find_concept_in_concept_list(narrower, concept_list)
                    res.append(f"- {nc.md_link()}")
                else:
                    res.append(f"- {narrower}")
            res.append("")
        for line in self.definition.split("\n"):
            res.append(line)
        res.append("")
        return res


@dataclasses.dataclass
class Vocabulary:
    uri: str
    label: str
    description: str
    extends: typing.Optional[str] = None
    history: typing.List[str] = dataclasses.field(default_factory=list)
    sourceRepository: typing.Optional[str] = None


class VocabularyStore:
    _PFX = f"""
PREFIX skos: <{NS['skos']}>
PREFIX owl: <{NS['owl']}>
PREFIX rdf: <{NS['rdf']}>
PREFIX rdfs: <{NS['rdfs']}>
"""
    DEFAULT_FORMAT = "text/turtle"
    DEFAULT_STORE = "default"

    def __init__(
        self,
        storage_uri=DEFAULT_STORE,
        store_identifier=STORE_IDENTIFIER,
        purge_existing=False,
    ):
        self.origin = None
        self.storage_uri = storage_uri
        self.store_identifier = store_identifier
        self._g = None
        self._terms = {}
        self._literals = ""
        self._initialize_store(purge=purge_existing)

    def __len__(self):
        return len(self._g)

    def _initialize_store(self, purge=False, store="default"):
        graph = rdflib.ConjunctiveGraph(store=store, identifier=self.store_identifier)
        if purge:
            graph.destroy(self.storage_uri)
        graph.open(self.storage_uri, create=True)
        self._g = graph

    @property
    def graph(self):
        return self._g

    def load(
        self,
        source: str,
        format: str = DEFAULT_FORMAT,
        bindings: typing.Optional[dict] = None,
    ):
        """
        Loads a vocabulary into the store.

        """
        g_loaded = self._g.parse(source, format=format)
        if bindings is not None:
            for k, v in bindings.items():
                self._g.bind(k, v)
        # Figure the broader concept vocabularies.
        # First check for extension_vocab rdfs:subPropertyOf extended_vocab
        # if not present, then compute and add it for later use.
        # What vocabulary did we just load?
        q = (
            VocabularyStore._PFX
            + """SELECT ?s
        WHERE {
            ?s rdf:type skos:ConceptScheme .
        }"""
        )
        qres = g_loaded.query(q)
        loaded_vocabulary = self._result_single_value(qres, abbreviate=False)
        if loaded_vocabulary is not None:
            L.info("Loaded vocabulary %s", loaded_vocabulary)
            q = (
                VocabularyStore._PFX
                + """SELECT ?extended
            WHERE {
                ?vocabulary rdfs:subPropertyOf ?extended .
            }"""
            )
            qres = self._g.query(q, initBindings={"vocabulary": loaded_vocabulary})
            _extended_vocab = self._result_single_value(qres, abbreviate=False)
            if _extended_vocab is not None:
                L.info("Extends: %s", _extended_vocab)
                return
            # The extended vocabulary is not specified
            # Figure it by examining the broader concepts for each
            # concept in the loaded vocabulary
            q = (
                VocabularyStore._PFX
                + """SELECT ?s
            WHERE {
                ?child rdf:type skos:Concept .
                ?child skos:broader ?s .
            }"""
            )
            qres = g_loaded.query(q)
            broader_concepts = self._one_res(qres)
            vocabs = set()
            for c in broader_concepts:
                concept = self.concept(str(c))
                if concept.vocabulary is not None:
                    vocabs.add(concept.vocabulary)
            for vocab in vocabs:
                if str(vocab) != str(loaded_vocabulary):
                    L.info("Extends: %s", vocab)
                    self._g.add(
                        (
                            rdflib.URIRef(loaded_vocabulary),
                            rdfsT("subPropertyOf"),
                            rdflib.URIRef(vocab),
                        )
                    )
                    self._g.commit()
            return
        L.warning("Loaded vocabulary does not specify skos:ConceptScheme")

    def expand_name(self, n: typing.Optional[str]) -> typing.Optional[str]:
        if n is None:
            return n
        try:
            return self._g.namespace_manager.expand_curie(n)
        except (ValueError, TypeError):
            pass
        return n

    def compact_name(self, n: typing.Optional[str]) -> typing.Optional[str]:
        if n is None:
            return n
        try:
            return rdflib.URIRef(n).n3(self._g.namespace_manager)
        except (ValueError, TypeError):
            pass
        return n

    def _one_res(self, rows, abbreviate=False) -> list[str]:
        res = []
        for r in rows:
            if abbreviate:
                res.append(self.compact_name(r[0]))
            else:
                res.append(r[0])
        return res

    def _result_single_value(self, rows, abbreviate=False) -> typing.Any:
        for r in rows:
            if abbreviate:
                return self.compact_name(r[0])
            return r[0]
        return None

    def _get_objects(self, subject: str, predicate: str) -> list[str]:
        q = """SELECT ?o
        WHERE {
            ?subject ?predicate ?o .
        }"""
        qres = self.query(q, subject=subject, predicate=predicate)
        res = []
        for row in qres:
            res.append(row[0])
        return res

    def objects(self, subject: str, predicate: str) -> list[str]:
        res = []
        qres = self._get_objects(subject, predicate)
        for row in qres:
            v = row
            v = str(v).strip()
            if len(v) > 0:
                res.append(v)
        return res

    def namespaces(self) -> list[str, rdflib.URIRef]:
        return [n for n in self._g.namespace_manager.namespaces()]

    def bind(self, prefix: str, uri: str, override: bool = True):
        self._g.namespace_manager.bind(prefix, uri, override=override)

    def query(self, q, **bindings):
        # L.debug(f"query: {q}")
        sparql = rdflib.plugins.sparql.prepareQuery(VocabularyStore._PFX + q)
        return self._g.query(sparql, initBindings=bindings)

    def vocabulary(self, uri: str) -> Vocabulary:
        """Return a Vocabulary given its URI.

        Raises KeyError if the vocabulary is not in the graph.
        """
        q = """SELECT ?vocabulary ?label ?definition ?extends ?repository
               WHERE {
            ?vocabulary rdf:type skos:ConceptScheme .
            ?vocabulary skos:prefLabel ?label .
            OPTIONAL {?vocabulary skos:definition ?definition .} .
            OPTIONAL {?vocabulary skos:inScheme ?extends .} .
            OPTIONAL {?vocabulary schema:codeRepository ?repository .} .
        }"""
        qh = """SELECT ?history
        WHERE {
            ?vocabulary skos:historyNote ?history .
        }"""
        qres = self.query(q, vocabulary=rdflib.URIRef(uri))
        for res in qres:
            _ext = res[3]
            _repo = res[4]
            L.debug(f"sourceRepository: {_repo}")
            qhres = self.query(qh, vocabulary=res[0])
            _hist = [h[0] for h in qhres]
            return Vocabulary(
                uri=str(res[0]),
                label=str(res[1]),
                description=str(res[2]),
                extends=str(_ext) if _ext is not None else None,
                sourceRepository=str(_repo) if _repo is not None else None,
                history=_hist,
            )
        raise KeyError(f"Vocabulary '{uri}' not found.")

    def base_vocabulary(self) -> Vocabulary:
        """Return the base vocabulary.

        This is the skos:ConceptScheme instance that has no skos:inScheme
        """
        q = """SELECT DISTINCT ?vocabulary
        WHERE {
            ?vocabulary rdf:type skos:ConceptScheme .
            ?subject ?predicate ?foo .
            FILTER (?predicate != skos:inScheme) .
        }"""
        qres = self.query(q)
        for res in qres:
            return self.vocabulary(res[0])
        raise ValueError("No base vocabulary found.")

    def vocabularies(self, abbreviate: bool = True) -> list[str]:
        """Return the base and all extension vocabulary URIs in the graph.

        Anything that is of type skos:ConceptScheme.
        """
        q = """SELECT ?vocabulary
        WHERE {
            ?vocabulary rdf:type skos:ConceptScheme .
        }"""
        qres = self.query(q)
        return [row[0] for row in qres]

    def concept(self, term: str):
        """Given a URI, return the matching VocabularyConcept

        Raises KeyError if not found.
        """
        term = self.expand_name(term)
        if "#" in term:
            ab = term.split("#")
        else:
            ab = term.split("/")
        name = ab[-1]
        labels = self.objects(term, skosT("prefLabel"))
        labels += self.objects(term, skosT("altLabel"))
        #labels += self.objects(term, rdfsT("label"))  # these are by convention the same as skos:prefLabel
        tmp = self.objects(term, skosT("definition"))
        definition = "\n".join(tmp)
        broader = self.objects(term, skosT("broader"))
        narrower = self.narrower(term)
        notes = self.objects(term, skosT("note"))
        notes += self.objects(term, skosT("editorialNote"))
        notes += self.objects(term, skosT("scopeNote"))
        notes += self.objects(term, skosT("changeNote"))
        notes += self.objects(term, rdfsT("comment"))
        vocabulary = self.objects(term, skosT("inScheme"))
        if len(vocabulary) > 0:
            vocabulary = vocabulary[0]
        else:
            # May be set with topConceptOf
            vocabulary = self.objects(term, skosT("topConceptOf"))
            if len(vocabulary) > 0:
                vocabulary = vocabulary[0]
            else:
                vocabulary = None
        history = self.objects(term, skosT("historyNote"))
        sources = self.objects(term, dctermT("source"))
        return VocabularyConcept(
            uri=str(term),
            name=name,
            label=labels,
            definition=definition.strip(),
            broader=broader,
            narrower=narrower,
            vocabulary=vocabulary,
            history=history,
            notes=notes,
            sources=sources,
            #scopenote=self.objects(term, skosT("scopeNote")),
            related=self.objects(term, skosT("related")),
            example=self.objects(term, skosT("example")),
            #changenote=self.objects(term, skosT("changeNote")),
        )


    def top_concept(self):
        """Get the root concept(s) in the specified vocabulary.
        -> typing.List["VocabularyConcept"]
        This is the concept that is skos:topConceptOf the vocabulary.
         The top concept in an extension vocabulary is a concept from the parent
         vocabulary, and likely has skos:broader concepts in that parent vocabulary
        """
        q = """SELECT DISTINCT ?subject
        WHERE {
            ?subject rdf:type skos:Concept .
            ?subject skos:topConceptOf ?vocabulary .
            ?subject ?predicate ?foo .
        }"""
        # remove  FILTER(?predicate != skos:broader) .

        qres = self.query(q)
        uri = self._one_res(qres)
        #L.debug(f"top concept uri: {uri}")
        L.debug(f"number of top concepts: {len(uri)}")
        if len(uri) < 1:
            raise ValueError("No topConcept found")

        conceptList = []
        for acon in uri:
            L.debug(f"self.concept(acon) uri: {self.concept(acon).uri}")
            conceptList.append(self.concept(acon))

        L.debug(f"len(conceptList): {len(conceptList)}")
        # return self.concept(uri[0])
        # modify to account for vocabs with >1 top concept.
        #return [self.concept(arow) for arow in uri]
        return conceptList

    def concepts(
        self, v: typing.Optional[str] = None, abbreviate: bool = False
    ) -> list[str]:
        """List the concept URIs in the specific vocabulary.

        Returns a list of the skos:Concept instances in the specified vocabulary
        as it exists in the current graph store.
        """
        try:
            v = self._g.namespace_manager.expand_curie(v)
        except (ValueError, TypeError):
            pass
        if v is None:
            q = """SELECT ?s
            WHERE {
                ?s rdf:type skos:Concept .
            }"""
            qres = self.query(q)
        else:
            q = """SELECT ?s
                WHERE {
                    ?s skos:inScheme | skos:topConceptOf ?vocabulary .
                    ?s rdf:type skos:Concept .
                }"""
            qres = self.query(q, vocabulary=v)
        return self._one_res(qres, abbreviate=abbreviate)


    def broader(
        self, concept: str, v: typing.Optional[str] = None, abbreviate: bool = False
    ) -> list[str]:
        concept = rdflib.URIRef(self.expand_name(concept))
        if v is None:
            q = """SELECT ?s
            WHERE {
                ?child skos:broader ?s .
            }"""
            qres = self.query(q, child=concept)
        else:
            v = self.expand_name(v)
            q = """SELECT ?s
            WHERE {
                ?s skos:inScheme ?vocabulary .
                ?child skos:broader ?s .
            }"""
            qres = self.query(q, vocabulary=v, child=concept)
        res = []
        # Should only ever be a single broader term in a well constructed taxonomy,
        # but who knows how well these things are constructed?
        return self._one_res(qres, abbreviate=abbreviate)

    def narrower(
        self, concept: str, v: typing.Optional[str] = None, abbreviate: bool = False
    ) -> list[str]:
        concept = rdflib.URIRef(self.expand_name(concept))
        if v is None:
            q = """SELECT ?s
            WHERE {
                ?s skos:broader ?parent .
            }"""
            qres = self.query(q, parent=concept)
        else:
            v = self.expand_name(v)
            q = """SELECT ?s
            WHERE {
                ?s skos:inScheme ?vocabulary .
                ?s skos:broader ?parent .
            }"""
            qres = self.query(q, vocabulary=v, parent=concept)
        return self._one_res(qres, abbreviate=abbreviate)

    def walk_narrower(self, concept_uri: str, level: int = 0):
        """
        Yields narrower concepts by performing depth first traversal.

        Yielded content is URI, depth
        where depth is the path length from the starting URI.
        """
        for uri in self.narrower(concept_uri):
            yield uri, level
            yield from self.walk_narrower(uri, level=level + 1)

    def walk_broader(self, concept_uri: str, level: int = 0):
        yield concept_uri, level
        for uri in self.broader(concept_uri):
            yield from self.walk_broader(uri, level=level + 1)

    def vocab_path(self, v: str) -> typing.List[str]:
        """Get the list of vocabularies progressively broader than vocabulary v.

        Result is a list of extension URIs
        """
        q = """SELECT ?vocab
        WHERE  {
            ?src skos:inScheme+ ?vocab .
        } 
        """
        qres = self.query(q, src=rdflib.URIRef(self.expand_name(v)))
        return [v[0] for v in qres]

    def walk_vocab_tree(self, v: str, level: int = 0):
        q = """SELECT ?vocab
        WHERE {
            ?src ^skos:inScheme ?vocab .
            ?vocab rdf:type skos:ConceptScheme .
        }
        """
        yield v, level
        qres = self.query(q, src=rdflib.URIRef(self.expand_name(v)))
        for res in qres:
            uri = res[0]
            yield from self.walk_vocab_tree(uri, level=level + 1)

    def vocab_tree(self, v:str) -> typing.List[str]:
        q = """SELECT ?vocab
        WHERE {
            ?src ^skos:inScheme+ ?vocab .
            ?vocab rdf:type skos:ConceptScheme .
        }
        """
        qres = self.query(q, src=rdflib.URIRef(self.expand_name(v)))
        return [v[0] for v in qres]
