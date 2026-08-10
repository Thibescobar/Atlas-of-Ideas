from collections import defaultdict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import CandidateRelation, Concept, Evidence, Passage, SourceDocument


def _concept_context(concept: Concept, passage_by_id: dict[str, Passage]) -> str:
    return "\n".join(
        passage_by_id[pid].text
        for pid in concept.source_passage_ids
        if pid in passage_by_id
    )


def generate_candidate_relations(
    concepts: list[Concept],
    passages: list[Passage],
    documents: list[SourceDocument],
    threshold: float = 0.18,
    limit: int = 60,
) -> list[CandidateRelation]:
    if len(concepts) < 2:
        return []

    passage_by_id = {p.id: p for p in passages}
    document_by_id = {d.id: d for d in documents}
    contexts = [_concept_context(c, passage_by_id) or c.label for c in concepts]

    matrix = TfidfVectorizer(ngram_range=(1, 2), lowercase=True).fit_transform(contexts)
    sims = cosine_similarity(matrix)
    candidates: list[CandidateRelation] = []

    for i in range(len(concepts)):
        for j in range(i + 1, len(concepts)):
            left, right = concepts[i], concepts[j]
            score = float(sims[i, j])
            shared = sorted(set(left.source_passage_ids) & set(right.source_passage_ids))
            co_occurrence_boost = min(0.25, 0.06 * len(shared))
            combined = min(1.0, score + co_occurrence_boost)
            if combined < threshold:
                continue

            evidence_ids = shared[:3]
            if not evidence_ids:
                evidence_ids = (left.source_passage_ids[:1] + right.source_passage_ids[:1])[:2]

            evidence = []
            for pid in evidence_ids:
                passage = passage_by_id.get(pid)
                if not passage:
                    continue
                document = document_by_id.get(passage.document_id)
                evidence.append(
                    Evidence(
                        passage_id=pid,
                        quote=passage.text[:500],
                        source_title=document.title if document else passage.document_id,
                    )
                )

            kind = "co_occurrence" if shared else "semantic_similarity"
            rationale = (
                f"Les concepts apparaissent ensemble dans {len(shared)} passage(s) et ont une proximité "
                f"textuelle de {score:.2f}."
                if shared
                else f"Les contextes textuels associés aux deux concepts ont une proximité de {score:.2f}."
            )

            candidates.append(
                CandidateRelation(
                    id=f"{left.id}|{right.id}",
                    workspace_id=left.workspace_id,
                    source_concept_id=left.id,
                    target_concept_id=right.id,
                    suggested_kind=kind,
                    semantic_score=combined,
                    rationale=rationale,
                    evidence=evidence,
                )
            )

    return sorted(candidates, key=lambda item: item.semantic_score, reverse=True)[:limit]
