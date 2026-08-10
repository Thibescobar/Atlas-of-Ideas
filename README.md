# Atlas of Ideas — v0.2

> Build a map of what you read, what you think, and how the two connect.

Atlas of Ideas turns a user's own sources into an inspectable personal knowledge graph. The application deliberately separates **machine suggestions** from **user-validated relations**.

## What v0.2 can do

- create multiple local workspaces;
- upload `.pdf`, `.txt`, `.md` and `.markdown` sources;
- extract text from text-based PDFs;
- split documents into passages;
- extract candidate concepts locally with TF-IDF;
- generate candidate relations from co-occurrence and contextual similarity;
- show evidence passages for every candidate relation;
- let the user accept, reject, or re-type a relation;
- persist documents, passages, concepts, candidates and validated relations as JSON;
- visualize only the validated graph;
- inspect where every concept and relation came from.

## Epistemic rule

A model-generated connection is **not a fact**.

The pipeline is:

```text
user sources
    │
    ▼
text extraction
    │
    ▼
passages
    │
    ▼
concept extraction
    │
    ▼
candidate relations
    │
    ▼
USER REVIEW
    │
    ▼
validated knowledge graph
```

Candidate relations live in `candidates.json`. Only accepted relations are copied into `relations.json` and shown as edges in the validated graph.

## Run locally

Python 3.11+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
streamlit run app.py
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
streamlit run app.py
```

## Repository structure

```text
atlas-of-ideas/
├── app.py
├── pyproject.toml
├── src/atlas_of_ideas/
│   ├── models.py          # workspaces, documents, concepts, candidate + validated relations
│   ├── ingest.py          # document chunking
│   ├── extraction.py      # local TF-IDF concept extraction
│   ├── candidates.py      # candidate relation discovery
│   ├── graph.py           # NetworkX graph construction
│   ├── storage.py         # local JSON persistence
│   └── parsers/
│       └── base.py        # PDF/TXT/Markdown parsing
├── data/workspaces/       # created at runtime; one folder per workspace
├── tests/
└── docs/
```

A workspace is stored roughly as:

```text
data/workspaces/ws-.../
├── workspace.json
├── documents.json
├── passages.json
├── concepts.json
├── candidates.json
└── relations.json
```

## Current extraction strategy

The default system intentionally has no API dependency. Concept extraction and relation discovery use transparent local TF-IDF baselines. This makes the first version cheap, inspectable and easy to debug.

It is **not** meant to be the final semantic engine.

## Best next upgrades

### 1. Sentence embeddings

Add a pluggable `SentenceTransformerEmbedder`, preferably multilingual. Keep TF-IDF as a baseline for evaluation.

### 2. LLM extraction, but structured

Use an LLM to propose `Concept`, `Claim`, `Person`, `Work` and typed relationships. Store the exact source passages and model/method for every proposal. Never silently promote an LLM output into a validated relation.

### 3. Claims as first-class nodes

Instead of directly connecting broad concepts, represent claims:

```text
[Passage] --SUPPORTS--> [Claim] --ABOUT--> [Concept]
                         │
                         └--CONTRADICTS--> [Claim]
```

This will make disagreement and evidence much more rigorous.

### 4. Better PDF ingestion

Current PDF parsing handles PDFs with embedded text. Add OCR only as an optional path for scans and preserve page numbers in `Passage` provenance.

### 5. Rich graph UI

Replace the basic Graphviz view with Cytoscape.js or Sigma.js for filtering, zooming, dynamic neighborhoods, evidence panels and temporal exploration.

### 6. Graph analytics

Add bridge-concept discovery, betweenness centrality, communities, domain mixing, temporal concept drift and a configurable `surprise_score`.

### 7. Personal hypotheses

Let users manually create an intuition such as:

> entropy seems analogous to impermanence

Then ask the system to search their corpus for supporting and contradicting evidence before they validate the edge.

## Tests

```bash
pytest
```

The core pipeline tests do not require Streamlit.

## License

Atlas of Ideas is licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE).
It permits noncommercial use, modification, and redistribution, including noncommercial
research and teaching. It also permits use by the organizations listed in the license,
including educational institutions and public research organizations, regardless of
their funding source or obligations resulting from that funding.

Commercial uses outside these permissions require a separate paid commercial license.
Contact [Thibault Escobar](https://github.com/Thibescobar) for commercial licensing terms.

The full license text governs these permissions. Dependencies remain subject to their
respective licenses.
