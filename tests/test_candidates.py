from atlas_of_ideas.candidates import calculate_bridge_score, generate_candidate_relations
from atlas_of_ideas.models import Concept, Passage, SourceDocument


def synthetic_corpus():
    documents = [
        SourceDocument(
            id="science",
            workspace_id="w",
            title="Science",
            domain="science",
            text="Mathematical models seek objective relations and truth.",
        ),
        SourceDocument(
            id="philosophy",
            workspace_id="w",
            title="Philosophy",
            domain="philosophy",
            text="Truth concerns the relation between knowledge and reality.",
        ),
        SourceDocument(
            id="spirituality",
            workspace_id="w",
            title="Spirituality",
            domain="spirituality",
            text="Truth and belief are connected through testimony.",
        ),
    ]
    passages = [
        Passage(
            id=f"{doc.id}:p0",
            workspace_id="w",
            document_id=doc.id,
            text=doc.text,
            start_char=0,
            end_char=len(doc.text),
        )
        for doc in documents
    ]
    concepts = [
        Concept(
            id="truth",
            workspace_id="w",
            label="truth",
            source_passage_ids=[passage.id for passage in passages],
        ),
        Concept(
            id="knowledge",
            workspace_id="w",
            label="knowledge",
            source_passage_ids=["philosophy:p0"],
        ),
        Concept(
            id="belief", workspace_id="w", label="belief", source_passage_ids=["spirituality:p0"]
        ),
    ]
    return documents, passages, concepts


def test_bridge_score_is_normalized_and_deterministic():
    first = calculate_bridge_score(0.62, 3, 2, 3)
    second = calculate_bridge_score(0.62, 3, 2, 3)
    assert first == second
    assert 0 <= first <= 1


def test_source_and_domain_diversity_raise_bridge_score():
    mono = calculate_bridge_score(0.6, 1, 1, 1, same_source_co_occurrence=True)
    cross_source = calculate_bridge_score(0.6, 2, 1, 2)
    cross_domain = calculate_bridge_score(0.6, 2, 2, 2)
    assert mono < cross_source < cross_domain


def test_generated_relation_exposes_cross_source_provenance():
    documents, passages, concepts = synthetic_corpus()
    candidates = generate_candidate_relations(concepts, passages, documents, threshold=0)
    candidate = next(
        item
        for item in candidates
        if {item.source_concept_id, item.target_concept_id} == {"truth", "knowledge"}
    )
    assert candidate.cross_source is True
    assert candidate.source_count == 3
    assert candidate.domain_count == 3
    assert set(candidate.document_ids) == {"science", "philosophy", "spirituality"}


def test_cross_source_bridge_outranks_trivial_local_co_occurrence():
    cross = calculate_bridge_score(0.45, 2, 2, 2)
    local = calculate_bridge_score(0.70, 1, 1, 1, same_source_co_occurrence=True)
    assert cross > local
