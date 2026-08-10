from atlas_of_ideas.epistemics import EdgeAssessment


def test_causal_claim_is_penalized():
    weak = EdgeAssessment(0.9, 0.8, 0.7, causal_claim=True)
    non_causal = EdgeAssessment(0.9, 0.8, 0.7, causal_claim=False)

    assert weak.confidence < non_causal.confidence
