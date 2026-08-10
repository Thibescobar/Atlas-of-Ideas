import networkx as nx

from .models import Concept, Passage, Relation, SourceDocument


def build_graph(concepts: list[Concept], relations: list[Relation]) -> nx.Graph:
    graph = nx.Graph()

    for concept in concepts:
        graph.add_node(
            concept.id,
            label=concept.label,
            domain=concept.domain,
            aliases=concept.aliases,
        )

    for relation in relations:
        if relation.source_concept_id not in graph or relation.target_concept_id not in graph:
            continue
        graph.add_edge(
            relation.source_concept_id,
            relation.target_concept_id,
            kind=relation.kind,
            score=relation.score,
            semantic_score=relation.semantic_score,
            bridge_score=relation.bridge_score,
            source_count=relation.source_count,
            domain_count=relation.domain_count,
            concept_source_count=relation.concept_source_count,
            relation_support_source_count=relation.relation_support_source_count,
            relation_support_domain_count=relation.relation_support_domain_count,
            support_level=relation.support_level,
            cross_source=relation.cross_source,
            document_ids=relation.document_ids,
            domains=relation.domains,
            rationale=relation.rationale,
            context=[item.model_dump() for item in relation.context],
            evidence=[item.model_dump() for item in relation.evidence],
        )

    return graph


def build_concepts_sources_graph(
    concepts: list[Concept],
    relations: list[Relation],
    passages: list[Passage],
    documents: list[SourceDocument],
) -> nx.Graph:
    """Build a graph containing validated concept edges and provenance nodes."""
    graph = build_graph(concepts, relations)
    passage_by_id = {passage.id: passage for passage in passages}
    document_by_id = {document.id: document for document in documents}

    for document in documents:
        graph.add_node(
            document.id,
            label=document.title,
            domain=document.domain,
            node_type="document",
            author=document.author,
        )

    for concept in concepts:
        graph.nodes[concept.id]["node_type"] = "concept"
        supporting_documents = sorted(
            {
                passage_by_id[pid].document_id
                for pid in concept.source_passage_ids
                if pid in passage_by_id and passage_by_id[pid].document_id in document_by_id
            }
        )
        for document_id in supporting_documents:
            graph.add_edge(
                document_id,
                concept.id,
                kind="supports_concept",
                score=1.0,
                bridge_score=1.0,
                semantic_score=1.0,
                source_count=1,
                cross_source=False,
                rationale="Ce concept a été extrait de ce document.",
                evidence=[],
            )
    return graph
