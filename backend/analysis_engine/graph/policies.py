"""
TRINETRA Analysis Engine — Graph Policies
Defines execution policies, error recovery, and timeout thresholds for LangGraph nodes.
"""

from typing import Dict, Any


class GraphExecutionPolicy:
    MAX_NODE_RETRIES: int = 1
    TIMEOUT_SECONDS: float = 120.0
    FALLBACK_TO_DETERMINISTIC_REASONING: bool = True

    @staticmethod
    def handle_node_error(node_name: str, error: Exception) -> Dict[str, Any]:
        """Maps an unhandled node exception to a structured state error dict."""
        return {
            "failed_node": node_name,
            "error_type": type(error).__name__,
            "message": str(error),
            "recoverable": False,
        }
