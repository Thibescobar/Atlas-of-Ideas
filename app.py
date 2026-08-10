import hashlib
from pathlib import Path

import networkx as nx
import streamlit as st
import streamlit.components.v1 as components

from atlas_of_ideas.candidates import generate_candidate_relations
from atlas_of_ideas.extraction import extract_concepts
from atlas_of_ideas.graph import build_concepts_sources_graph, build_graph
from atlas_of_ideas.ingest import chunk_document
from atlas_of_ideas.models import CandidateRelation, Relation, SourceDocument, Workspace
from atlas_of_ideas.parsers import parse_upload
from atlas_of_ideas.paths import find_best_paths
from atlas_of_ideas.storage import WorkspaceStore
from atlas_of_ideas.visualization import graph_to_html
from atlas_of_ideas.workspaces import workspace_selectbox_index

st.set_page_config(page_title="Atlas of Ideas", page_icon="🕸️", layout="wide")
STORE = WorkspaceStore()
RELATION_KINDS = [
    "semantic_similarity",
    "co_occurrence",
    "analogy",
    "contradiction",
    "historical_influence",
    "human_interpretation",
]
EPISTEMIC_WARNING = (
    "Un chemin Atlas représente une chaîne de relations documentées ou sémantiques. "
    "Il ne constitue pas en lui-même une preuve de causalité, d’influence historique "
    "ou d’équivalence."
)


def stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def relation_from_candidate(candidate: CandidateRelation, workspace_id: str, kind: str) -> Relation:
    return Relation(
        id=stable_id("rel", candidate.id),
        workspace_id=workspace_id,
        source_concept_id=candidate.source_concept_id,
        target_concept_id=candidate.target_concept_id,
        kind=kind,
        score=candidate.bridge_score or candidate.semantic_score,
        semantic_score=candidate.semantic_score,
        bridge_score=candidate.bridge_score,
        source_count=candidate.source_count,
        domain_count=candidate.domain_count,
        cross_source=candidate.cross_source,
        document_ids=candidate.document_ids,
        domains=candidate.domains,
        rationale=candidate.rationale,
        evidence=candidate.evidence,
        proposed_by="local_candidate_generator",
        validated_by_user=True,
    )


def review_buttons(candidate, reviewed_kind, workspace_id, candidates, relations, key_prefix):
    accept_col, reject_col = st.columns(2)
    if accept_col.button("✓ Accepter", key=f"accept-{key_prefix}", use_container_width=True):
        candidate.status = "accepted"
        candidate.reviewed_kind = reviewed_kind
        relation = relation_from_candidate(candidate, workspace_id, reviewed_kind)
        relations[:] = [item for item in relations if item.id != relation.id] + [relation]
        STORE.save_candidates(workspace_id, candidates)
        STORE.save_relations(workspace_id, relations)
        st.rerun()
    if reject_col.button("✗ Rejeter", key=f"reject-{key_prefix}", use_container_width=True):
        candidate.status = "rejected"
        candidate.reviewed_kind = reviewed_kind
        relation_id = stable_id("rel", candidate.id)
        relations[:] = [item for item in relations if item.id != relation_id]
        STORE.save_candidates(workspace_id, candidates)
        STORE.save_relations(workspace_id, relations)
        st.rerun()


st.title("Atlas of Ideas · v0.3")
st.caption(
    "Découvre des ponts entre tes sources, puis décide humainement lesquels méritent le graphe."
)

with st.sidebar:
    st.header("Workspace")
    workspaces = STORE.list_workspaces()
    workspace_by_id = {workspace.id: workspace for workspace in workspaces}
    workspace_ids = list(workspace_by_id)
    requested_id = st.session_state.get("workspace_selector")
    selected_id = st.selectbox(
        "Ouvrir",
        [None, *workspace_ids],
        index=workspace_selectbox_index(workspace_ids, requested_id),
        format_func=lambda item: (
            "— créer un workspace —"
            if item is None
            else f"{workspace_by_id[item].name} · {item[:8]}"
        ),
        key="workspace_selector",
    )

    if selected_id is None:
        new_name = st.text_input("Nom", value="My ideas")
        new_description = st.text_area(
            "Description", placeholder="Ex. conscience, temps et liberté"
        )
        if st.button("Créer", type="primary", use_container_width=True):
            workspace_id = stable_id("ws", f"{new_name}:{new_description}:{len(workspaces)}")
            STORE.create_workspace(
                Workspace(
                    id=workspace_id,
                    name=new_name.strip() or "Untitled",
                    description=new_description.strip() or None,
                )
            )
            st.session_state["workspace_selector"] = workspace_id
            st.rerun()
        st.stop()

    workspace = workspace_by_id[selected_id]
    st.caption(workspace.description or "Aucune description")

workspace_id = workspace.id
documents = STORE.load_documents(workspace_id)
passages = STORE.load_passages(workspace_id)
concepts = STORE.load_concepts(workspace_id)
candidates = STORE.load_candidates(workspace_id)
relations = STORE.load_relations(workspace_id)
concept_by_id = {concept.id: concept for concept in concepts}
document_by_id = {document.id: document for document in documents}

source_tab, bridges_tab, graph_tab, paths_tab, inspect_tab = st.tabs(
    ["Sources", "Bridges", "Graph", "Paths", "Inspect"]
)

with source_tab:
    st.subheader("Ajoute tes sources")
    st.write("PDF texte, TXT et Markdown. Tout reste dans ce workspace local.")
    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_files = st.file_uploader(
            "Sources", type=["pdf", "txt", "md", "markdown"], accept_multiple_files=True
        )
    with col2:
        domain = st.selectbox(
            "Domaine par défaut",
            [
                "other",
                "science",
                "philosophy",
                "history",
                "politics",
                "spirituality",
                "psychology",
                "literature",
            ],
        )
        max_concepts = st.slider("Concepts maximum", 10, 100, 40, 5)

    if st.button(
        "Importer et reconstruire les bridges", type="primary", disabled=not uploaded_files
    ):
        existing_filenames = {document.filename for document in documents if document.filename}
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
                doc_id = stable_id(
                    "doc", f"{workspace_id}:{uploaded.name}:{hashlib.sha1(data).hexdigest()}"
                )
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
            except (OSError, RuntimeError, ValueError) as exc:
                errors.append(f"{uploaded.name}: {exc}")

        new_passages = [
            passage for document in new_documents for passage in chunk_document(document)
        ]
        new_concepts = extract_concepts(
            new_passages, workspace_id=workspace_id, max_concepts=max_concepts
        )
        passage_by_id = {passage.id: passage for passage in new_passages}
        new_document_by_id = {document.id: document for document in new_documents}
        for concept in new_concepts:
            concept_domains = {
                new_document_by_id[passage_by_id[pid].document_id].domain
                for pid in concept.source_passage_ids
                if pid in passage_by_id and passage_by_id[pid].document_id in new_document_by_id
            }
            concept.domain = next(iter(concept_domains)) if len(concept_domains) == 1 else "other"
        new_candidates = generate_candidate_relations(
            new_concepts, new_passages, new_documents, threshold=0.18, limit=100
        )
        STORE.save_documents(workspace_id, new_documents)
        STORE.save_passages(workspace_id, new_passages)
        STORE.save_concepts(workspace_id, new_concepts)
        STORE.save_candidates(workspace_id, new_candidates)
        concept_ids = {concept.id for concept in new_concepts}
        STORE.save_relations(
            workspace_id,
            [
                relation
                for relation in relations
                if relation.source_concept_id in concept_ids
                and relation.target_concept_id in concept_ids
            ],
        )
        if imported:
            st.success(f"{imported} nouvelle(s) source(s) importée(s).")
        for error in errors:
            st.warning(error)
        st.rerun()

    st.divider()
    st.metric("Sources", len(documents))
    for document in documents:
        with st.expander(f"{document.title} · {document.domain}"):
            st.caption(document.filename or document.id)
            st.write(document.text[:1800] + ("…" if len(document.text) > 1800 else ""))
    if not documents:
        st.info("Ajoute au moins une source pour commencer.")

with bridges_tab:
    st.subheader("Bridges à valider")
    st.caption(
        "Cross-source first : un bridge reste une hypothèse jusqu’à ta validation explicite."
    )
    filter_col, source_col, sort_col = st.columns(3)
    relation_filter = filter_col.selectbox(
        "Relations", ["Toutes", "Cross-source uniquement", "Mono-source uniquement"]
    )
    minimum_sources = source_col.selectbox(
        "Minimum sources", [1, 2, 3, 4], format_func=lambda x: "4+" if x == 4 else str(x)
    )
    sort_by = sort_col.selectbox("Trier par", ["bridge_score", "semantic_score", "source_count"])

    visible = [candidate for candidate in candidates if candidate.status == "pending"]
    if relation_filter == "Cross-source uniquement":
        visible = [candidate for candidate in visible if candidate.cross_source]
    elif relation_filter == "Mono-source uniquement":
        visible = [candidate for candidate in visible if not candidate.cross_source]
    visible = [candidate for candidate in visible if candidate.source_count >= minimum_sources]
    visible.sort(
        key=lambda item: (getattr(item, sort_by) or 0, item.bridge_score or 0, item.id),
        reverse=True,
    )

    pending_count = sum(candidate.status == "pending" for candidate in candidates)
    accepted_count = sum(candidate.status == "accepted" for candidate in candidates)
    rejected_count = sum(candidate.status == "rejected" for candidate in candidates)
    m1, m2, m3 = st.columns(3)
    m1.metric("À revoir", pending_count)
    m2.metric("Acceptées", accepted_count)
    m3.metric("Rejetées", rejected_count)

    for candidate in visible[:30]:
        left = concept_by_id.get(candidate.source_concept_id)
        right = concept_by_id.get(candidate.target_concept_id)
        if not left or not right:
            continue
        with st.container(border=True):
            st.markdown(f"### {left.label} ↔ {right.label}")
            badge = "BRIDGE" if candidate.cross_source else "MONO-SOURCE"
            st.markdown(
                f"`{badge}` · **{candidate.source_count} sources** · **{candidate.domain_count} domaines** · "
                f"bridge score **{candidate.bridge_score:.2f}** · semantic score **{candidate.semantic_score:.2f}**"
            )
            st.caption(candidate.rationale)
            reviewed_kind = st.selectbox(
                "Type de relation",
                RELATION_KINDS,
                index=RELATION_KINDS.index(candidate.suggested_kind),
                key=f"kind-bridge-{candidate.id}",
            )
            for evidence in candidate.evidence:
                with st.expander(f"{evidence.source_title} · {evidence.domain}"):
                    st.write(evidence.quote)
            review_buttons(
                candidate,
                reviewed_kind,
                workspace_id,
                candidates,
                relations,
                f"bridge-{candidate.id}",
            )
    if not visible:
        st.info("Aucun bridge ne correspond aux filtres actuels.")

with graph_tab:
    st.subheader("Graphe interactif validé")
    view_col, relation_col, score_col, sources_col = st.columns(4)
    view_mode = view_col.radio("View", ["Concepts", "Concepts + Sources"])
    with relation_col:
        st.write("Relations")
        show_cross = st.checkbox("cross-source", value=True)
        show_mono = st.checkbox("mono-source", value=False)
    minimum_bridge = score_col.slider("Minimum bridge score", 0.0, 1.0, 0.0, 0.05)
    graph_min_sources = sources_col.slider("Minimum sources", 1, 4, 1)
    filtered_relations = [
        relation
        for relation in relations
        if (relation.bridge_score or relation.score) >= minimum_bridge
        and relation.source_count >= graph_min_sources
        and ((relation.cross_source and show_cross) or (not relation.cross_source and show_mono))
    ]
    graph = (
        build_graph(concepts, filtered_relations)
        if view_mode == "Concepts"
        else build_concepts_sources_graph(concepts, filtered_relations, passages, documents)
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Concepts", len(concepts))
    c2.metric("Relations affichées", len(filtered_relations))
    c3.metric(
        "Composantes", nx.number_connected_components(graph) if graph.number_of_nodes() else 0
    )
    if graph.number_of_edges():
        components.html(graph_to_html(graph), height=700, scrolling=False)
    else:
        st.info("Valide quelques relations ou élargis les filtres.")

with paths_tab:
    st.subheader("Explorateur de chemins")
    st.warning(EPISTEMIC_WARNING)
    validated_graph = build_graph(concepts, relations)
    connected_concepts = [concept for concept in concepts if validated_graph.degree(concept.id) > 0]
    if len(connected_concepts) < 2:
        st.info("Il faut au moins deux concepts reliés par des relations validées.")
    else:
        options = {
            f"{concept.label} · {concept.id[-8:]}": concept.id
            for concept in sorted(connected_concepts, key=lambda x: x.label)
        }
        start_col, end_col = st.columns(2)
        start_label = start_col.selectbox("Concept de départ", options, index=0)
        end_label = end_col.selectbox("Concept d’arrivée", options, index=min(1, len(options) - 1))
        if st.button("Chercher les meilleurs chemins", type="primary"):
            results = find_best_paths(
                validated_graph, options[start_label], options[end_label], max_paths=5, cutoff=6
            )
            if not results:
                st.info("Aucun chemin simple trouvé avec une profondeur maximale de 6 relations.")
            for index, result in enumerate(results, 1):
                labels = [
                    validated_graph.nodes[node_id].get("label", node_id)
                    for node_id in result.node_ids
                ]
                with st.expander(
                    f"Chemin {index} · score {result.score:.2f} · {' → '.join(labels)}",
                    expanded=index == 1,
                ):
                    for step in result.steps:
                        left = validated_graph.nodes[step.source_id].get("label", step.source_id)
                        right = validated_graph.nodes[step.target_id].get("label", step.target_id)
                        sources = (
                            ", ".join(step.source_titles)
                            or "source non renseignée (workspace v0.2)"
                        )
                        st.markdown(f"**{left} → {right}** · `{step.kind}` · {step.score:.2f}")
                        st.caption(f"Sources : {sources}")

with inspect_tab:
    st.subheader("Inspecter une relation")
    if not candidates:
        st.info("Aucune relation candidate.")
    else:
        candidate_options = {}
        for candidate in candidates:
            left = concept_by_id.get(candidate.source_concept_id)
            right = concept_by_id.get(candidate.target_concept_id)
            if left and right:
                candidate_options[f"{left.label} ↔ {right.label} · {candidate.status}"] = candidate
        selected_label = st.selectbox("Relation", candidate_options)
        candidate = candidate_options[selected_label]
        left = concept_by_id[candidate.source_concept_id]
        right = concept_by_id[candidate.target_concept_id]
        st.markdown(f"## {left.label} ↔ {right.label}")
        st.markdown(
            f"Type proposé : `{candidate.suggested_kind}`  \n"
            f"Bridge score : **{candidate.bridge_score:.2f}**  \n"
            f"Semantic score : **{candidate.semantic_score:.2f}**  \n"
            f"Statut : `{candidate.status}`"
        )
        st.markdown("#### Sources impliquées")
        for document_id in candidate.document_ids:
            document = document_by_id.get(document_id)
            st.write(f"- {document.title if document else document_id}")
        st.markdown("#### Domaines")
        st.write(", ".join(candidate.domains) or "Non renseignés (workspace v0.2)")
        st.markdown("#### Passages / evidence")
        for evidence in candidate.evidence:
            with st.expander(f"{evidence.source_title} · {evidence.domain}"):
                st.write(evidence.quote)
        reviewed_kind = st.selectbox(
            "Type de relation",
            RELATION_KINDS,
            index=RELATION_KINDS.index(candidate.reviewed_kind or candidate.suggested_kind),
            key=f"kind-inspect-{candidate.id}",
        )
        if candidate.status == "pending":
            review_buttons(
                candidate,
                reviewed_kind,
                workspace_id,
                candidates,
                relations,
                f"inspect-{candidate.id}",
            )
        else:
            st.caption(
                "La décision est persistée. Reconstruis les suggestions pour réinitialiser les candidates."
            )

st.divider()
st.caption(
    "Atlas discovers connections, not truths. Toute relation forte reste soumise à validation humaine."
)
