from dataclasses import dataclass

import numpy as np


@dataclass
class CandidateLink:
    left: int
    right: int
    score: float


def discover_cross_domain_links(
    similarities: np.ndarray,
    domains: list[str],
    threshold: float = 0.15,
) -> list[CandidateLink]:
    candidates: list[CandidateLink] = []

    for i in range(len(domains)):
        for j in range(i + 1, len(domains)):
            if domains[i] == domains[j]:
                continue

            score = float(similarities[i, j])
            if score >= threshold:
                candidates.append(CandidateLink(i, j, score))

    return sorted(candidates, key=lambda item: item.score, reverse=True)
