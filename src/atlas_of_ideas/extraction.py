import re
import unicodedata
from collections import defaultdict

from sklearn.feature_extraction.text import TfidfVectorizer

from .models import Concept, Passage


BILINGUAL_STOPWORDS = {
    "the", "and", "for", "that", "with", "from", "this", "into", "are", "was", "were",
    "have", "has", "had", "not", "but", "you", "your", "their", "they", "its", "can",
    "les", "des", "une", "dans", "pour", "que", "qui", "avec", "sur", "pas", "par", "plus",
    "est", "sont", "être", "comme", "aux", "ces", "cette", "son", "ses", "leur", "leurs",
    "nous", "vous", "ils", "elles", "mais", "donc", "ainsi", "tout", "tous", "toute", "toutes",
    "du", "de", "la", "le", "un", "et", "en", "au", "à", "a", "d", "l", "se", "ce",
}


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    return normalized or "concept"


def extract_concepts(
    passages: list[Passage],
    workspace_id: str,
    max_concepts: int = 40,
    per_passage: int = 8,
) -> list[Concept]:
    if not passages:
        return []

    texts = [passage.text for passage in passages]
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.95 if len(texts) > 2 else 1.0,
        token_pattern=r"(?u)\b[^\W\d_][^\W_]{2,}\b",
        stop_words=sorted(BILINGUAL_STOPWORDS),
        max_features=max(200, max_concepts * 8),
    )
    matrix = vectorizer.fit_transform(texts)
    terms = vectorizer.get_feature_names_out()

    concept_passages: dict[str, set[str]] = defaultdict(set)
    concept_scores: dict[str, float] = defaultdict(float)

    for row_idx, passage in enumerate(passages):
        row = matrix.getrow(row_idx)
        order = row.data.argsort()[::-1][:per_passage]
        for pos in order:
            col_idx = row.indices[pos]
            term = terms[col_idx].strip()
            if len(term) < 3:
                continue
            score = float(row.data[pos])
            concept_passages[term].add(passage.id)
            concept_scores[term] += score

    ranked = sorted(
        concept_scores,
        key=lambda term: (len(concept_passages[term]), concept_scores[term]),
        reverse=True,
    )[:max_concepts]

    return [
        Concept(
            id=f"{workspace_id}:concept:{slugify(term)}",
            workspace_id=workspace_id,
            label=term,
            source_passage_ids=sorted(concept_passages[term]),
            extraction_method="local_tfidf",
        )
        for term in ranked
    ]
