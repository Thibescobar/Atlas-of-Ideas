# Roadmap

## Phase 0 — Philosophy of the project

Before scaling data, define an epistemic contract:

- What is a "connection"?
- What counts as evidence?
- Which relations are descriptive vs interpretative?
- How do we represent uncertainty?
- How do we display disagreement?
- How do we avoid turning semantic similarity into pseudo-causality?

## Phase 1 — Tiny corpus, fully inspectable

Use 20–50 documents across 4–6 domains.

Suggested starting axes:

- time
- consciousness
- causality
- order / disorder
- freedom
- progress
- cooperation
- death
- identity

Prefer public-domain or openly licensed sources.

Deliverables:

- ingestion pipeline;
- source metadata;
- passage chunking;
- searchable corpus;
- TF-IDF baseline;
- simple cross-domain similarity graph.

## Phase 2 — Better semantic representation

Add sentence-transformers or another embedding backend.

Compare:

- lexical similarity;
- embedding similarity;
- concept co-occurrence;
- human judgment.

Create a small manually labeled evaluation set.

## Phase 3 — Concept extraction

Extract:

- named entities;
- recurring abstract concepts;
- claims;
- quotations;
- dates;
- persons;
- schools of thought.

Do not let an LLM silently become the database.
Store the extracted claim plus the source passage and extraction method.

## Phase 4 — Typed relationships

Replace generic "related to" edges with explicit classes:

- semantic similarity;
- historical influence;
- citation;
- analogy;
- opposition;
- shared metaphor;
- co-occurrence;
- temporal succession;
- human interpretation.

## Phase 5 — Provenance and disagreement

Every graph edge gets:

- source passages;
- source IDs;
- extraction method;
- model/version;
- confidence;
- counter-evidence;
- human validation status.

## Phase 6 — Human layer

Allow contributors to submit a reflection such as:

> Learning evolutionary theory changed how I think about freedom.

Store this separately from documentary claims.

Possible fields:

- author pseudonym;
- context/profession (optional);
- concepts mentioned;
- proposed relationship;
- confidence;
- consent/license.

Then compare the "documented knowledge graph" to the
"human interpretation graph".

## Phase 7 — Temporal graph

Attach time intervals to ideas and relationships.

Questions become possible:

- When did two vocabularies begin to converge?
- Does a metaphor move from theology to philosophy to science?
- Which concepts appear in several disciplines at the same historical moment?

## Phase 8 — Network science

Explore:

- centrality;
- community detection;
- bridge concepts;
- shortest semantic paths;
- domain mixing;
- concept drift;
- temporal communities.

The interesting metric is not simply "most central concept".
Look for concepts that connect otherwise separated communities.

## Phase 9 — Research-grade evaluation

Build benchmarks for:

- relation correctness;
- provenance correctness;
- domain diversity;
- novelty;
- hallucination rate;
- causal overclaiming.

Run blinded human evaluation on proposed cross-domain links.

## Phase 10 — Generative exploration

Only after provenance works well:

> Give me three surprising but defensible paths from entropy to mortality.

The LLM becomes a guide over the graph, not the source of truth.
