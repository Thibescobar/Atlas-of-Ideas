import networkx as nx

from .models import Concept, Relation


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
            rationale=relation.rationale,
            evidence=[item.model_dump() for item in relation.evidence],
        )

    return graph
