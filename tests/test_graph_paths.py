from atlas_of_ideas.graph import build_concepts_sources_graph, build_graph
from atlas_of_ideas.models import Concept, Evidence, Passage, Relation, SourceDocument
from atlas_of_ideas.paths import find_best_paths


def graph_fixture():
    concepts = [
        Concept(id=name, workspace_id="w", label=name) for name in ["truth", "knowledge", "belief"]
    ]
    evidence = [
        Evidence(
            passage_id="d1:p0",
            document_id="d1",
            source_title="Document 1",
            domain="science",
            quote="Truth and knowledge.",
        )
    ]
    relations = [
        Relation(
            source_concept_id="truth",
            target_concept_id="knowledge",
            kind="semantic_similarity",
            score=0.8,
            bridge_score=0.8,
            concept_source_count=1,
            relation_support_source_count=1,
            relation_support_domain_count=1,
            support_level="single_source",
            support_document_ids=["d1"],
            rationale="r",
            evidence=evidence,
            validated_by_user=True,
        ),
        Relation(
            source_concept_id="knowledge",
            target_concept_id="belief",
            kind="analogy",
            score=0.7,
            bridge_score=0.7,
            concept_source_count=1,
            relation_support_source_count=1,
            relation_support_domain_count=1,
            support_level="single_source",
            support_document_ids=["d1"],
            rationale="r",
            evidence=evidence,
            validated_by_user=True,
        ),
    ]
    document = SourceDocument(
        id="d1", workspace_id="w", title="Document 1", domain="science", text="Truth and knowledge."
    )
    passage = Passage(
        id="d1:p0",
        workspace_id="w",
        document_id="d1",
        text=document.text,
        start_char=0,
        end_char=len(document.text),
    )
    concepts[0].source_passage_ids = [passage.id]
    return concepts, relations, [passage], [document]


def test_build_graph_preserves_bridge_metadata():
    concepts, relations, _, _ = graph_fixture()
    graph = build_graph(concepts, relations)
    assert graph.number_of_edges() == 2
    assert graph.edges["truth", "knowledge"]["bridge_score"] == 0.8


def test_concepts_sources_graph_adds_shaped_provenance_nodes():
    concepts, relations, passages, documents = graph_fixture()
    graph = build_concepts_sources_graph(concepts, relations, passages, documents)
    assert graph.nodes["d1"]["node_type"] == "document"
    assert graph.nodes["truth"]["node_type"] == "concept"
    assert graph.edges["d1", "truth"]["kind"] == "supports_concept"


def test_find_best_paths_returns_steps_and_sources():
    concepts, relations, _, _ = graph_fixture()
    paths = find_best_paths(build_graph(concepts, relations), "truth", "belief")
    assert len(paths) == 1
    assert paths[0].node_ids == ("truth", "knowledge", "belief")
    assert paths[0].steps[0].source_titles == ("Document 1",)
