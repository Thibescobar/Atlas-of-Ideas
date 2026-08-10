import colorsys
import hashlib

import networkx as nx
from pyvis.network import Network


def domain_color(domain: str) -> str:
    """Generate a stable, restrained color without maintaining a giant palette."""
    digest = int(hashlib.sha1(domain.encode("utf-8")).hexdigest()[:6], 16)
    hue = (digest % 360) / 360
    red, green, blue = colorsys.hls_to_rgb(hue, 0.52, 0.48)
    return f"#{round(red * 255):02x}{round(green * 255):02x}{round(blue * 255):02x}"


def graph_to_html(graph: nx.Graph, height: int = 680) -> str:
    network = Network(height=f"{height}px", width="100%", bgcolor="#0e1117", font_color="#fafafa")
    network.barnes_hut(gravity=-3500, central_gravity=0.2, spring_length=150)

    for node_id, attrs in graph.nodes(data=True):
        node_type = attrs.get("node_type", "concept")
        label = attrs.get("label", node_id)
        domain = attrs.get("domain", "other")
        network.add_node(
            node_id,
            label=label,
            title=f"{label}<br>Domaine : {domain}<br>Type : {node_type}",
            shape="box" if node_type == "document" else "dot",
            color=domain_color(domain),
            size=24 if node_type == "document" else 18,
        )

    edge_colors = {
        "contradiction": "#ef4444",
        "historical_influence": "#f59e0b",
        "analogy": "#8b5cf6",
        "supports_concept": "#64748b",
    }
    for left, right, attrs in graph.edges(data=True):
        kind = attrs.get("kind", "relation")
        score = float(attrs.get("bridge_score") or attrs.get("score") or 0.0)
        network.add_edge(
            left,
            right,
            label=kind,
            title=f"{kind}<br>Score : {score:.2f}<br>{attrs.get('rationale', '')}",
            color=edge_colors.get(kind, "#38bdf8"),
            width=1 + 4 * score,
            dashes=kind == "supports_concept",
        )

    network.set_options(
        '{"interaction":{"hover":true,"navigationButtons":true,"keyboard":true},'
        '"physics":{"stabilization":{"iterations":180}},'
        '"edges":{"smooth":{"type":"dynamic"},"font":{"size":10,"align":"middle"}}}'
    )
    return network.generate_html(notebook=False)
