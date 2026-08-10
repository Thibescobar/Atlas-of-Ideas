from dataclasses import dataclass


@dataclass
class EdgeAssessment:
    semantic_similarity: float
    provenance_quality: float
    cross_source_support: float
    causal_claim: bool = False

    @property
    def confidence(self) -> float:
        '''
        Conservative score: semantic resemblance alone is intentionally insufficient.
        '''
        base = (
            0.45 * self.semantic_similarity
            + 0.35 * self.provenance_quality
            + 0.20 * self.cross_source_support
        )

        if self.causal_claim:
            base *= 0.65

        return max(0.0, min(1.0, base))
