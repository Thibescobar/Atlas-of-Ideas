from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import CandidateRelation, Concept, Evidence, Passage, SourceDocument


def calculate_bridge_score(
    semantic_score: float,
    source_count: int,
    domain_count: int,
    evidence_count: int,
    same_source_co_occurrence: bool = False,
) -> float:
    """Return a transparent, normalized cross-source-first score.

    Semantic proximity remains the largest component, while independent source
    and domain support can lift a moderate cross-source link above a local
    co-occurrence. Counts are capped so large corpora cannot dominate the score.
    """
    semantic = max(0.0, min(1.0, semantic_score))
    source_bonus = min(max(source_count - 1, 0), 3) / 3 * 0.24
    domain_bonus = min(max(domain_count - 1, 0), 2) / 2 * 0.14
    evidence_bonus = min(max(evidence_count, 0), 4) / 4 * 0.08
    triviality_penalty = 0.12 if same_source_co_occurrence else 0.0
    score = 0.54 * semantic + source_bonus + domain_bonus + evidence_bonus
    return round(max(0.0, min(1.0, score - triviality_penalty)), 6)


def _concept_context(concept: Concept, passage_by_id: dict[str, Passage]) -> str:
    return "\n".join(
        passage_by_id[pid].text for pid in concept.source_passage_ids if pid in passage_by_id
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
            semantic_score = float(sims[i, j])
            shared = sorted(set(left.source_passage_ids) & set(right.source_passage_ids))

            all_passage_ids = sorted(set(left.source_passage_ids + right.source_passage_ids))
            document_ids = sorted(
                {passage_by_id[pid].document_id for pid in all_passage_ids if pid in passage_by_id}
            )
            domains = sorted(
                {
                    document_by_id[doc_id].domain
                    for doc_id in document_ids
                    if doc_id in document_by_id
                }
            )
            source_count = max(1, len(document_ids))
            domain_count = max(1, len(domains))
            cross_source = source_count > 1

            evidence_ids = shared[:4]
            if not evidence_ids:
                # Round-robin by document gives independent sources priority.
                seen_documents: set[str] = set()
                evidence_ids = []
                for pid in all_passage_ids:
                    passage = passage_by_id.get(pid)
                    if passage and passage.document_id not in seen_documents:
                        evidence_ids.append(pid)
                        seen_documents.add(passage.document_id)
                    if len(evidence_ids) == 4:
                        break

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
                        document_id=passage.document_id,
                        domain=document.domain if document else "other",
                    )
                )

            same_source_co_occurrence = bool(shared) and source_count == 1
            bridge_score = calculate_bridge_score(
                semantic_score,
                source_count,
                domain_count,
                len(evidence),
                same_source_co_occurrence,
            )
            if max(semantic_score, bridge_score) < threshold:
                continue

            kind = "co_occurrence" if shared else "semantic_similarity"
            rationale = (
                f"Les concepts apparaissent ensemble dans {len(shared)} passage(s) et ont une proximité "
                f"textuelle de {semantic_score:.2f}."
                if shared
                else f"Les contextes textuels associés aux deux concepts ont une proximité de {semantic_score:.2f}."
            )
            rationale += (
                f" Support : {source_count} source(s), {domain_count} domaine(s). "
                "Cette proximité ne démontre ni causalité ni influence historique."
            )

            candidates.append(
                CandidateRelation(
                    id=f"{left.id}|{right.id}",
                    workspace_id=left.workspace_id,
                    source_concept_id=left.id,
                    target_concept_id=right.id,
                    suggested_kind=kind,
                    semantic_score=round(semantic_score, 6),
                    bridge_score=bridge_score,
                    source_count=source_count,
                    domain_count=domain_count,
                    cross_source=cross_source,
                    document_ids=document_ids,
                    domains=domains or ["other"],
                    rationale=rationale,
                    evidence=evidence,
                )
            )

    return sorted(
        candidates,
        key=lambda item: (
            item.bridge_score or 0,
            item.source_count,
            item.domain_count,
            item.semantic_score,
            item.id,
        ),
        reverse=True,
    )[:limit]
