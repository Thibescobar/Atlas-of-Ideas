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
    exploratory = calculate_bridge_score(0.6, 0, 0, 0)
    mono = calculate_bridge_score(0.6, 1, 1, 1)
    cross_source = calculate_bridge_score(0.6, 2, 1, 2)
    cross_domain = calculate_bridge_score(0.6, 2, 2, 2)
    assert exploratory < mono < cross_source < cross_domain


def test_generated_relation_exposes_cross_source_provenance():
    documents, passages, concepts = synthetic_corpus()
    candidates = generate_candidate_relations(concepts, passages, documents, threshold=0)
    candidate = next(
        item
        for item in candidates
        if {item.source_concept_id, item.target_concept_id} == {"truth", "knowledge"}
    )
    assert candidate.concept_source_count == 3
    assert candidate.relation_support_source_count == 1
    assert candidate.relation_support_domain_count == 1
    assert candidate.support_level == "single_source"
    assert candidate.cross_source is False
    assert candidate.support_document_ids == ["philosophy"]
    assert set(candidate.context_document_ids) == {"science", "philosophy", "spirituality"}


def test_cross_source_bridge_outranks_trivial_local_co_occurrence():
    cross = calculate_bridge_score(0.45, 2, 2, 2)
    local = calculate_bridge_score(0.70, 1, 1, 1)
    assert cross > local


def test_disjoint_concept_sources_do_not_become_relation_support():
    """Two sources for A plus two for B must not become four supporting sources."""
    documents = [
        SourceDocument(
            id=f"d{index}",
            workspace_id="w",
            title=f"Document {index}",
            domain="science" if index < 3 else "philosophy",
            text=text,
        )
        for index, text in enumerate(
            [
                "Alpha describes objective structure.",
                "Alpha concerns stable mathematical form.",
                "Beta describes knowledge and structure.",
                "Beta concerns philosophical form.",
            ],
            start=1,
        )
    ]
    passages = [
        Passage(
            id=f"{document.id}:p0",
            workspace_id="w",
            document_id=document.id,
            text=document.text,
            start_char=0,
            end_char=len(document.text),
        )
        for document in documents
    ]
    concepts = [
        Concept(id="a", label="alpha", source_passage_ids=["d1:p0", "d2:p0"]),
        Concept(id="b", label="beta", source_passage_ids=["d3:p0", "d4:p0"]),
    ]

    candidate = generate_candidate_relations(concepts, passages, documents, threshold=0)[0]

    assert candidate.concept_source_count == 4
    assert candidate.relation_support_source_count == 0
    assert candidate.relation_support_domain_count == 0
    assert candidate.support_document_ids == []
    assert candidate.evidence == []
    assert len(candidate.context) == 4
    assert candidate.support_level == "exploratory"
    assert candidate.cross_source is False
    assert candidate.bridge_score == calculate_bridge_score(candidate.semantic_score, 0, 0, 0)


def test_two_independent_shared_passages_create_multi_source_support():
    documents = [
        SourceDocument(id="d1", title="One", domain="science", text="Alpha relates to beta."),
        SourceDocument(
            id="d2", title="Two", domain="philosophy", text="Alpha and beta form an analogy."
        ),
    ]
    passages = [
        Passage(
            id=f"{document.id}:p0",
            document_id=document.id,
            text=document.text,
            start_char=0,
            end_char=len(document.text),
        )
        for document in documents
    ]
    shared_ids = [passage.id for passage in passages]
    concepts = [
        Concept(id="a", label="alpha", source_passage_ids=shared_ids),
        Concept(id="b", label="beta", source_passage_ids=shared_ids),
    ]

    candidate = generate_candidate_relations(concepts, passages, documents, threshold=0)[0]

    assert candidate.concept_source_count == 2
    assert candidate.relation_support_source_count == 2
    assert candidate.relation_support_domain_count == 2
    assert candidate.support_level == "multi_source"
    assert candidate.cross_source is True
    assert len(candidate.evidence) == 2
    assert candidate.context == []
