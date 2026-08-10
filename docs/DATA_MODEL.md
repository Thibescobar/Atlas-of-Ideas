# Data model

The graph intentionally distinguishes objects and assertions.

## Nodes

- Document
- Passage
- Concept
- Person
- Event
- Claim
- HumanReflection

## Edges

- MENTIONS
- SUPPORTS
- CONTRADICTS
- SEMANTICALLY_SIMILAR
- INFLUENCED_BY
- ANALOGOUS_TO
- OCCURRED_BEFORE
- INTERPRETED_AS

## Important distinction

A model-generated link is a **candidate assertion**, not a fact.

Each assertion should eventually contain:

```json
{
  "relation": "ANALOGOUS_TO",
  "source": "entropy",
  "target": "impermanence",
  "confidence": 0.63,
  "method": "embedding_similarity",
  "model": "baseline-v1",
  "evidence_passages": ["p12", "p83"],
  "validated_by_human": false
}
```
