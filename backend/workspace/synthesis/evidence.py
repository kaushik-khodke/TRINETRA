"""
TRINETRA Phase 8 — Evidence Graph Builder
Assembles referenced intelligence items into a navigable directed evidence graph.
"""

from typing import Dict, Any, List, Set
from collections import defaultdict


class EvidenceGraphBuilder:
    """
    Constructs an evidence network model from board items and relational links.
    """

    @classmethod
    def build_graph(
        cls,
        items: List[Dict[str, Any]],
        relations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        node_map: Dict[str, Dict[str, Any]] = {}
        degrees: Dict[str, int] = defaultdict(int)

        for item in items:
            item_id = item.get("item_id", "")
            node_map[item_id] = {
                "item_id": item_id,
                "type": item.get("type", "UNKNOWN"),
                "source_id": item.get("source_id", ""),
                "title": item.get("title", ""),
                "annotation": item.get("annotation", ""),
                "degree": 0,
            }

        edges = []
        for rel in relations:
            src = rel.get("source_item_id")
            tgt = rel.get("target_item_id")
            if src in node_map and tgt in node_map:
                edges.append({
                    "relation_id": rel.get("relation_id"),
                    "source": src,
                    "target": tgt,
                    "type": rel.get("relation_type", "supports"),
                })
                degrees[src] += 1
                degrees[tgt] += 1

        for item_id, deg in degrees.items():
            if item_id in node_map:
                node_map[item_id]["degree"] = deg

        isolated_nodes = [node["item_id"] for node in node_map.values() if node["degree"] == 0]
        sorted_nodes = sorted(node_map.values(), key=lambda n: n["degree"], reverse=True)

        return {
            "node_count": len(node_map),
            "edge_count": len(edges),
            "nodes": list(node_map.values()),
            "edges": edges,
            "isolated_nodes": isolated_nodes,
            "top_connected_nodes": sorted_nodes[:5],
        }
