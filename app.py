import hashlib
from pathlib import Path

import networkx as nx
import streamlit as st

from atlas_of_ideas.candidates import generate_candidate_relations
from atlas_of_ideas.extraction import extract_concepts, slugify
from atlas_of_ideas.graph import build_graph
from atlas_of_ideas.ingest import chunk_document
from atlas_of_ideas.models import Relation, SourceDocument, Workspace
from atlas_of_ideas.parsers import parse_upload
from atlas_of_ideas.storage import WorkspaceStore

st.set_page_config(page_title="Atlas of Ideas", page_icon="🕸️", layout="wide")
STORE = WorkspaceStore()


def stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def dot_escape(value: str) -> str:
    return value.replace('\\', '\\\\').replace('"', '\\"')


def graph_to_dot(graph) -> str:
    lines = ["graph Atlas {", 'graph [overlap=false, splines=true];', 'node [shape=ellipse];']
    for node_id, attrs in graph.nodes(data=True):
        label = dot_escape(attrs.get("label", node_id))
        lines.append(f'"{dot_escape(node_id)}" [label="{label}"];')
    for source, target, attrs in graph.edges(data=True):
        label = dot_escape(f"{attrs.get('kind', '')} {attrs.get('score', 0):.2f}")
        lines.append(f'"{dot_escape(source)}" -- "{dot_escape(target)}" [label="{label}"];')
    lines.append("}")
    return "\n".join(lines)


st.title("Atlas of Ideas")
st.caption("Transforme tes propres sources en graphe d'idées inspectable et validé par toi.")

with st.sidebar:
    st.header("Workspace")
    workspaces = STORE.list_workspaces()
    workspace_by_label = {f"{w.name} · {w.id[:8]}": w for w in workspaces}

    selected_label = st.selectbox(
        "Ouvrir",
        ["— créer un workspace —", *workspace_by_label.keys()],
    )

    if selected_label == "— créer un workspace —":
        new_name = st.text_input("Nom", value="My ideas")
        new_description = st.text_area("Description", placeholder="Ex. conscience, temps et liberté")
        if st.button("Créer", type="primary", use_container_width=True):
            workspace_id = stable_id("ws", f"{new_name}:{new_description}:{len(workspaces)}")
            STORE.create_workspace(
                Workspace(id=workspace_id, name=new_name.strip() or "Untitled", description=new_description.strip() or None)
            )
            st.success("Workspace créé. Sélectionne-le dans la liste.")
            st.rerun()
        st.stop()

    workspace = workspace_by_label[selected_label]
    st.caption(workspace.description or "Aucune description")

workspace_id = workspace.id
documents = STORE.load_documents(workspace_id)
passages = STORE.load_passages(workspace_id)
concepts = STORE.load_concepts(workspace_id)
candidates = STORE.load_candidates(workspace_id)
relations = STORE.load_relations(workspace_id)

source_tab, review_tab, graph_tab, inspect_tab = st.tabs(
    ["1 · Sources", "2 · Relations candidates", "3 · Graphe", "4 · Inspecter"]
)

with source_tab:
    st.subheader("Ajoute tes sources")
    st.write("Formats pris en charge : PDF texte, TXT et Markdown. Les fichiers restent dans ce workspace local.")

    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_files = st.file_uploader(
            "Sources",
            type=["pdf", "txt", "md", "markdown"],
            accept_multiple_files=True,
        )
    with col2:
        domain = st.selectbox(
            "Domaine par défaut",
            ["other", "science", "philosophy", "history", "politics", "spirituality", "psychology", "literature"],
        )
        max_concepts = st.slider("Concepts maximum", 10, 100, 40, 5)

    if st.button("Importer et reconstruire les suggestions", type="primary", disabled=not uploaded_files):
        existing_filenames = {doc.filename for doc in documents if doc.filename}
        new_documents = list(documents)
        imported = 0
        errors = []

        for uploaded in uploaded_files:
            if uploaded.name in existing_filenames:
                continue
            try:
                data = uploaded.getvalue()
                text = parse_upload(uploaded.name, data)
                if not text.strip():
                    errors.append(f"{uploaded.name}: aucun texte extractible")
                    continue
                doc_id = stable_id("doc", f"{workspace_id}:{uploaded.name}:{hashlib.sha1(data).hexdigest()}")
                new_documents.append(
                    SourceDocument(
                        id=doc_id,
                        workspace_id=workspace_id,
                        title=Path(uploaded.name).stem,
                        filename=uploaded.name,
                        domain=domain,
                        text=text,
                    )
                )
                imported += 1
            except Exception as exc:
                errors.append(f"{uploaded.name}: {exc}")

        new_passages = [p for doc in new_documents for p in chunk_document(doc)]
        new_concepts = extract_concepts(new_passages, workspace_id=workspace_id, max_concepts=max_concepts)
        new_candidates = generate_candidate_relations(
            new_concepts,
            new_passages,
            new_documents,
            threshold=0.18,
            limit=80,
        )

        STORE.save_documents(workspace_id, new_documents)
        STORE.save_passages(workspace_id, new_passages)
        STORE.save_concepts(workspace_id, new_concepts)
        STORE.save_candidates(workspace_id, new_candidates)
        # Validated relations survive only if their concepts still exist.
        concept_ids = {concept.id for concept in new_concepts}
        kept_relations = [
            r for r in relations
            if r.source_concept_id in concept_ids and r.target_concept_id in concept_ids
        ]
        STORE.save_relations(workspace_id, kept_relations)

        if imported:
            st.success(f"{imported} nouvelle(s) source(s) importée(s).")
        if errors:
            for error in errors:
                st.warning(error)
        st.rerun()

    st.divider()
    if documents:
        st.metric("Sources", len(documents))
        for doc in documents:
            with st.expander(f"{doc.title} · {doc.domain}"):
                st.caption(doc.filename or doc.id)
                st.write(doc.text[:1800] + ("…" if len(doc.text) > 1800 else ""))
    else:
        st.info("Ajoute au moins une source pour commencer.")

with review_tab:
    st.subheader("Valide ou rejette les connexions proposées")
    st.caption("Une suggestion n'entre dans le knowledge graph qu'après validation explicite.")

    pending = [candidate for candidate in candidates if candidate.status == "pending"]
    accepted_count = sum(candidate.status == "accepted" for candidate in candidates)
    rejected_count = sum(candidate.status == "rejected" for candidate in candidates)
    m1, m2, m3 = st.columns(3)
    m1.metric("À revoir", len(pending))
    m2.metric("Acceptées", accepted_count)
    m3.metric("Rejetées", rejected_count)

    concept_by_id = {concept.id: concept for concept in concepts}
    relation_kinds = [
        "semantic_similarity",
        "co_occurrence",
        "analogy",
        "contradiction",
        "historical_influence",
        "human_interpretation",
    ]

    for candidate in pending[:25]:
        left = concept_by_id.get(candidate.source_concept_id)
        right = concept_by_id.get(candidate.target_concept_id)
        if not left or not right:
            continue

        with st.container(border=True):
            st.markdown(f"### {left.label} ↔ {right.label}")
            st.write(candidate.rationale)
            st.progress(candidate.semantic_score, text=f"score proposé : {candidate.semantic_score:.2f}")
            reviewed_kind = st.selectbox(
                "Type de relation",
                relation_kinds,
                index=relation_kinds.index(candidate.suggested_kind),
                key=f"kind-{candidate.id}",
            )
            for evidence in candidate.evidence:
                with st.expander(f"Source · {evidence.source_title}"):
                    st.write(evidence.quote)

            accept_col, reject_col = st.columns(2)
            if accept_col.button("✓ Accepter", key=f"accept-{candidate.id}", use_container_width=True):
                candidate.status = "accepted"
                candidate.reviewed_kind = reviewed_kind
                relation = Relation(
                    id=stable_id("rel", candidate.id),
                    workspace_id=workspace_id,
                    source_concept_id=candidate.source_concept_id,
                    target_concept_id=candidate.target_concept_id,
                    kind=reviewed_kind,
                    score=candidate.semantic_score,
                    rationale=candidate.rationale,
                    evidence=candidate.evidence,
                    proposed_by="local_candidate_generator",
                    validated_by_user=True,
                )
                relations = [r for r in relations if r.id != relation.id] + [relation]
                STORE.save_candidates(workspace_id, candidates)
                STORE.save_relations(workspace_id, relations)
                st.rerun()

            if reject_col.button("✗ Rejeter", key=f"reject-{candidate.id}", use_container_width=True):
                candidate.status = "rejected"
                STORE.save_candidates(workspace_id, candidates)
                st.rerun()

    if not pending:
        st.info("Aucune relation candidate à revoir. Ajoute des sources ou reconstruis les suggestions.")

with graph_tab:
    st.subheader("Knowledge graph validé")
    graph = build_graph(concepts, relations)
    c1, c2, c3 = st.columns(3)
    c1.metric("Concepts extraits", len(concepts))
    c2.metric("Relations validées", len(relations))
    c3.metric("Composantes", len(list(nx.connected_components(graph))) if graph.number_of_nodes() else 0)

    if graph.number_of_edges():
        st.graphviz_chart(graph_to_dot(graph), use_container_width=True)
    else:
        st.info("Valide quelques relations pour faire apparaître ton graphe.")

with inspect_tab:
    st.subheader("Inspecter un concept")
    graph = build_graph(concepts, relations)
    if not concepts:
        st.info("Aucun concept extrait pour le moment.")
    else:
        concept_options = {concept.label: concept for concept in sorted(concepts, key=lambda item: item.label)}
        selected = st.selectbox("Concept", concept_options.keys())
        concept = concept_options[selected]
        st.code(concept.id)
        st.caption(f"Méthode d'extraction : {concept.extraction_method}")

        source_passages = [p for p in passages if p.id in concept.source_passage_ids]
        st.markdown("#### Passages sources")
        for passage in source_passages[:10]:
            doc = next((d for d in documents if d.id == passage.document_id), None)
            with st.expander(doc.title if doc else passage.document_id):
                st.write(passage.text)

        st.markdown("#### Relations validées")
        if concept.id in graph:
            neighbors = list(graph.neighbors(concept.id))
            if not neighbors:
                st.caption("Aucune relation validée.")
            for neighbor_id in neighbors:
                edge = graph.edges[concept.id, neighbor_id]
                neighbor = next((c for c in concepts if c.id == neighbor_id), None)
                st.markdown(
                    f"**{neighbor.label if neighbor else neighbor_id}** · `{edge['kind']}` · {edge['score']:.2f}"
                )
                st.caption(edge["rationale"])
