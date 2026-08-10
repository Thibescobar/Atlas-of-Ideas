# Atlas of Ideas — v0.3

> Build a map of what you read, what you think, and how independent sources connect.

Atlas of Ideas is a local Streamlit application that turns a user's PDF, TXT and Markdown sources into an inspectable knowledge graph. It extracts concepts, proposes bridges, preserves their exact evidence, and keeps every strong relationship pending until a person accepts or rejects it.

## Cross-source first

Atlas v0.3 treats provenance as a fundamental graph dimension. A **bridge** is a candidate connection between two concepts, especially one supported by more than one document or domain. Cross-source candidates are ranked ahead of trivial local co-occurrences when their textual evidence is credible.

Every candidate exposes:

- its semantic similarity;
- its `bridge_score`;
- the number of contextual sources versus relation-supporting sources and domains;
- whether it is cross-source;
- the documents, domains, and evidence passages involved.

The local, deterministic score is normalized from 0 to 1:

```text
bridge_score =
    54% semantic similarity
    + relation-support source diversity bonus (up to 30%)
    + domain diversity bonus (up to 14%)
    + evidence quality bonus (up to 10%)
    - exploratory penalty when no explicit relational evidence exists (8%)
```

`concept_source_count` counts documents containing either concept. It never creates a support
bonus by itself. `relation_support_source_count` counts only documents containing a passage
associated with both concepts. Separate passages describing A and B are context, not evidence.
Candidates based only on semantic similarity remain visible as `exploratory`. The diversity
bonuses are capped. A high score means “worth inspecting across this corpus,” not “true.”

## Workflow

```text
your sources → passages → local TF-IDF concepts → candidate bridges
                                                       │
                                                   USER REVIEW
                                                       │
                                             validated graph + paths
```

The five application tabs are:

- **Sources** — import `.pdf`, `.txt`, `.md`, or `.markdown` files and assign a domain;
- **Bridges** — filter by cross/mono-source and minimum sources, sort, inspect, re-type, accept, or reject;
- **Graph** — explore an interactive, zoomable and draggable graph in Concepts or Concepts + Sources mode;
- **Paths** — find up to five bounded simple paths between validated concepts;
- **Inspect** — review complete provenance and the current human decision for a candidate.

## Run locally

Python 3.11 or newer is required.

```bash
git clone https://github.com/Thibescobar/Atlas-of-Ideas.git
cd Atlas-of-Ideas
git switch v0.3-cross-source
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
streamlit run app.py
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

No API key, paid API, cloud database, or hosted service is required. Documents and graph data are stored as JSON under `data/workspaces/<workspace-id>/`.

## Exploring the graph

Only accepted relations become concept-to-concept graph edges. In **Concepts + Sources** view, rectangular document nodes connect to round concept nodes, making provenance visible. Filters control cross-source versus mono-source edges, minimum bridge score, and minimum source count. Hover for details; drag nodes, zoom, or use the navigation controls.

The Paths tab uses NetworkX over validated relations. It ranks simple paths of at most six relations and displays each edge type, score, and supporting source.

## Data compatibility

The v0.3 Pydantic models add provenance and scoring fields with defaults. Existing v0.2 workspace JSON remains loadable; legacy relations use their old score as both semantic and bridge score until suggestions are rebuilt. Rebuilding candidates enriches them with document and domain metadata.

## Atlas discovers connections, not truths.

A semantic similarity or graph path is not, by itself:

- causality;
- historical influence;
- philosophical equivalence;
- moral equivalence.

Atlas may reveal that unrelated texts share concepts such as truth, community, authority, or belief. It must not silently convert that proximity into a historical or causal claim. Sensitive types such as `historical_influence`, `contradiction`, and `analogy` remain visible, editable proposals governed by the `pending`, `accepted`, and `rejected` human-review states.

## Architecture

```text
app.py                         Streamlit UI and human review flow
src/atlas_of_ideas/
├── candidates.py             deterministic bridge discovery and scoring
├── extraction.py             local TF-IDF concept extraction
├── graph.py                  concept and concept+source NetworkX graphs
├── paths.py                  bounded, ranked simple-path search
├── visualization.py          interactive PyVis rendering
├── models.py                 Pydantic data model and compatibility defaults
├── ingest.py                 passage chunking
├── storage.py                local JSON persistence
└── parsers/                  PDF/TXT/Markdown parsing
tests/                        synthetic corpus and regression tests
```

## Development

```bash
pytest
ruff check .
```

The extraction and scoring baseline is deliberately transparent and inexpensive. TF-IDF recognizes textual overlap, not deep multilingual meaning, irony, historical context, or the truth of a claim. Text-only PDFs are supported; scanned PDFs require OCR before import.

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
