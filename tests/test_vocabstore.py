import vocab_tools
import os.path

THIS_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "../example"))


def _get_store_for_all():
    s = vocab_tools.VocabularyStore()
    s.load(os.path.join(THIS_FOLDER, "data/example.ttl"))
    s.load(os.path.join(THIS_FOLDER, "data/extension_example.ttl"))
    s.load(os.path.join(THIS_FOLDER, "data/extension_extension.ttl"))
    return s


def test_top_concept():
    s = vocab_tools.VocabularyStore()
    s.load(os.path.join(THIS_FOLDER, "data/example.ttl"))
    tc = s.top_concept()
    assert tc.uri == "https://example.net/my/minimal/thing"


def test_concepts():
    s = vocab_tools.VocabularyStore()
    s.load(os.path.join(THIS_FOLDER, "data/example.ttl"))
    s.load(os.path.join(THIS_FOLDER, "data/extension_example.ttl"))
    cs = s.concepts()
    assert len(cs) == 4
    # convert URIrefs to strings
    cs = [str(c) for c in cs]
    assert "https://example.net/my/extension/liquid" in cs
    assert "https://example.net/my/minimal/thing" in cs
    assert "https://example.net/my/minimal/solid" in cs


def test_vocabularies():
    s = _get_store_for_all()
    vs = s.vocabularies(abbreviate=False)
    uris = [str(uri) for uri in vs]
    assert len(uris) == 3
    assert "https://example.net/my/minimal/vocab" in uris
    assert "https://example.net/my/extension/vocab" in uris
    assert "https://example.net/my/extension2/vocab" in uris


def test_vocabulary():
    s = _get_store_for_all()
    v = s.vocabulary("https://example.net/my/minimal/vocab")
    assert v.label == "Minimal Example Vocabulary"
    assert v.extends is None
    v = s.vocabulary("https://example.net/my/extension/vocab")
    assert v.label == "Simple Vocabulary Extension"
    assert v.extends == "https://example.net/my/minimal/vocab"


def test_basevocabulary():
    s = _get_store_for_all()
    v = s.base_vocabulary()
    assert v.uri == "https://example.net/my/minimal/vocab"


def test_vocabulary_path():
    s = _get_store_for_all()
    res = s.vocab_path("https://example.net/my/extension2/vocab")
    assert len(res) == 2
    res = [str(v) for v in res]
    assert "https://example.net/my/minimal/vocab" in res
    assert "https://example.net/my/extension/vocab" in res


def test_broader():
    s = _get_store_for_all()
    c = s.concept("ext2:beer")
    res = s.broader(c.uri)
    assert str(res[0]) == "https://example.net/my/extension/liquid"


def test_narrower():
    s = _get_store_for_all()
    c = s.concept("eg:thing")
    res = s.narrower(c.uri)
    assert len(res) == 2
    res = [str(v) for v in res]
    assert "https://example.net/my/minimal/solid" in res
    assert "https://example.net/my/extension/liquid" in res


def test_walk_narrower():
    s = _get_store_for_all()
    c = s.concept("eg:thing")
    counter = 0
    for cn, depth in s.walk_narrower(c.uri, level=1):
        counter += 1
        print(f"{'-'*(depth)} {cn}")
    assert counter == 4
