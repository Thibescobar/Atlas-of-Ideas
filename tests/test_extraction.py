from atlas_of_ideas.extraction import extract_concepts
from atlas_of_ideas.models import Passage


def test_extract_concepts_returns_source_links():
    passages = [
        Passage(id="p1", workspace_id="w", document_id="d1", text="Freedom and causality shape debates about determinism.", start_char=0, end_char=55),
        Passage(id="p2", workspace_id="w", document_id="d2", text="Causality and freedom are recurring philosophical questions.", start_char=0, end_char=57),
    ]
    concepts = extract_concepts(passages, workspace_id="w", max_concepts=10)
    assert concepts
    assert all(c.workspace_id == "w" for c in concepts)
    assert any(c.source_passage_ids for c in concepts)
