from atlas_of_ideas.models import CandidateRelation, Relation


def test_v02_candidate_model_remains_compatible():
    candidate = CandidateRelation.model_validate(
        {
            "id": "old",
            "source_concept_id": "a",
            "target_concept_id": "b",
            "semantic_score": 0.42,
            "rationale": "legacy",
        }
    )
    assert candidate.bridge_score == 0.42
    assert candidate.concept_source_count == 1
    assert candidate.relation_support_source_count == 0
    assert candidate.support_level == "exploratory"
    assert candidate.cross_source is False


def test_v02_relation_model_remains_compatible():
    relation = Relation.model_validate(
        {
            "source_concept_id": "a",
            "target_concept_id": "b",
            "kind": "semantic_similarity",
            "score": 0.51,
            "rationale": "legacy",
        }
    )
    assert relation.semantic_score == 0.51
    assert relation.bridge_score == 0.51
    assert relation.concept_source_count == 1
    assert relation.relation_support_source_count == 0
    assert relation.support_level == "exploratory"
