from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import CandidateRelation, Concept, Evidence, Passage, SourceDocument


def calculate_bridge_score(
    semantic_score: float,
    relation_support_source_count: int,
    relation_support_domain_count: int,
    evidence_count: int,
) -> float:
    """Return a transparent, normalized cross-source-first score.

    Semantic proximity remains the largest component, while independent source
    and domain support can lift a moderate cross-source link above a local
    co-occurrence. Counts are capped so large corpora cannot dominate the score.
    """
    semantic = max(0.0, min(1.0, semantic_score))
    source_bonus = min(max(relation_support_source_count - 1, 0), 3) / 3 * 0.30
    domain_bonus = min(max(relation_support_domain_count - 1, 0), 2) / 2 * 0.14
    evidence_bonus = min(max(evidence_count, 0), 4) / 4 * 0.10
    exploratory_penalty = 0.08 if relation_support_source_count == 0 else 0.0
    score = 0.54 * semantic + source_bonus + domain_bonus + evidence_bonus
    return round(max(0.0, min(1.0, score - exploratory_penalty)), 6)


def _evidence_from_passages(
    passage_ids: list[str],
    passage_by_id: dict[str, Passage],
    document_by_id: dict[str, SourceDocument],
) -> list[Evidence]:
    result = []
    for passage_id in passage_ids:
        passage = passage_by_id.get(passage_id)
        if not passage:
            continue
        document = document_by_id.get(passage.document_id)
        result.append(
            Evidence(
                passage_id=passage_id,
                quote=passage.text[:500],
                source_title=document.title if document else passage.document_id,
                document_id=passage.document_id,
                domain=document.domain if document else "other",
            )
        )
    return result


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
            context_document_ids = sorted(
                {passage_by_id[pid].document_id for pid in all_passage_ids if pid in passage_by_id}
            )
            context_domains = sorted(
                {
                    document_by_id[doc_id].domain
                    for doc_id in context_document_ids
                    if doc_id in document_by_id
                }
            )
            support_document_ids = sorted(
                {passage_by_id[pid].document_id for pid in shared if pid in passage_by_id}
            )
            support_domains = sorted(
                {
                    document_by_id[doc_id].domain
                    for doc_id in support_document_ids
                    if doc_id in document_by_id
                }
            )
            relation_support_source_count = len(support_document_ids)
            relation_support_domain_count = len(support_domains)
            support_level = (
                "multi_source"
                if relation_support_source_count > 1
                else "single_source"
                if relation_support_source_count == 1
                else "exploratory"
            )
            cross_source = support_level == "multi_source"

            evidence_ids = []
            seen_evidence_documents: set[str] = set()
            for pid in shared:
                passage = passage_by_id.get(pid)
                if passage and passage.document_id not in seen_evidence_documents:
                    evidence_ids.append(pid)
                    seen_evidence_documents.add(passage.document_id)
                if len(evidence_ids) == 4:
                    break
            evidence = _evidence_from_passages(evidence_ids, passage_by_id, document_by_id)
            context_ids = []
            seen_context_documents: set[str] = set()
            for pid in all_passage_ids:
                passage = passage_by_id.get(pid)
                if (
                    passage
                    and pid not in shared
                    and passage.document_id not in seen_context_documents
                ):
                    context_ids.append(pid)
                    seen_context_documents.add(passage.document_id)
                if len(context_ids) == 4:
                    break
            context = _evidence_from_passages(context_ids, passage_by_id, document_by_id)

            bridge_score = calculate_bridge_score(
                semantic_score,
                relation_support_source_count,
                relation_support_domain_count,
                len(evidence),
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
                f" Contexte conceptuel : {len(context_document_ids)} source(s). "
                f"Support relationnel : {relation_support_source_count} source(s), "
                f"{relation_support_domain_count} domaine(s). "
                "Cette proximité ne démontre ni causalité ni influence historique."
            )
            if support_level == "exploratory":
                rationale += " Candidate exploratoire : aucun passage ne soutient explicitement la relation."

            candidates.append(
                CandidateRelation(
                    id=f"{left.id}|{right.id}",
                    workspace_id=left.workspace_id,
                    source_concept_id=left.id,
                    target_concept_id=right.id,
                    suggested_kind=kind,
                    semantic_score=round(semantic_score, 6),
                    bridge_score=bridge_score,
                    source_count=relation_support_source_count,
                    domain_count=relation_support_domain_count,
                    concept_source_count=len(context_document_ids),
                    concept_domain_count=len(context_domains),
                    relation_support_source_count=relation_support_source_count,
                    relation_support_domain_count=relation_support_domain_count,
                    support_level=support_level,
                    cross_source=cross_source,
                    document_ids=support_document_ids,
                    domains=support_domains,
                    context_document_ids=context_document_ids,
                    support_document_ids=support_document_ids,
                    rationale=rationale,
                    context=context,
                    evidence=evidence,
                )
            )

    return sorted(
        candidates,
        key=lambda item: (
            item.bridge_score or 0,
            item.relation_support_source_count or 0,
            item.relation_support_domain_count or 0,
            item.semantic_score,
            item.id,
        ),
        reverse=True,
    )[:limit]
