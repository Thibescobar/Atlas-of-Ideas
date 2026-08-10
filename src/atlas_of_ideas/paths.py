from dataclasses import dataclass
from itertools import pairwise
from math import prod

import networkx as nx


@dataclass(frozen=True)
class PathStep:
    source_id: str
    target_id: str
    kind: str
    score: float
    source_titles: tuple[str, ...]


@dataclass(frozen=True)
class AtlasPath:
    node_ids: tuple[str, ...]
    score: float
    steps: tuple[PathStep, ...]


def find_best_paths(
    graph: nx.Graph,
    source_id: str,
    target_id: str,
    max_paths: int = 5,
    cutoff: int = 6,
) -> list[AtlasPath]:
    """Rank bounded simple paths by geometric mean edge score, then brevity."""
    if source_id not in graph or target_id not in graph or source_id == target_id:
        return []

    results: list[AtlasPath] = []
    try:
        paths = nx.all_simple_paths(graph, source_id, target_id, cutoff=cutoff)
        for node_ids in paths:
            steps = []
            edge_scores = []
            for left, right in pairwise(node_ids):
                attrs = graph.edges[left, right]
                score = float(attrs.get("bridge_score") or attrs.get("score") or 0.0)
                edge_scores.append(max(score, 1e-9))
                titles = tuple(
                    sorted(
                        {
                            item.get("source_title", "")
                            for item in attrs.get("evidence", [])
                            if item.get("source_title")
                        }
                    )
                )
                steps.append(
                    PathStep(
                        source_id=left,
                        target_id=right,
                        kind=str(attrs.get("kind", "relation")),
                        score=score,
                        source_titles=titles,
                    )
                )
            path_score = prod(edge_scores) ** (1 / len(edge_scores))
            results.append(AtlasPath(tuple(node_ids), round(path_score, 6), tuple(steps)))
    except nx.NetworkXNoPath:
        return []

    return sorted(results, key=lambda item: (-item.score, len(item.node_ids), item.node_ids))[
        :max_paths
    ]
