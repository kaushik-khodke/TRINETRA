"""
SatQuery AI / TRINETRA — QML Configuration
Environment settings, hardware device flags, and execution timeouts
for the PennyLane quantum research branch.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class QMLConfig:
    enabled: bool = field(default_factory=lambda: os.getenv("QML_ENABLED", "true").lower() in ("true", "1", "yes"))
    mode: str = field(default_factory=lambda: os.getenv("QML_MODE", "research"))
    device_name: str = field(default_factory=lambda: os.getenv("QML_DEVICE", "default.qubit"))
    num_qubits: int = field(default_factory=lambda: int(os.getenv("QML_QUBITS", "6")))
    num_layers: int = field(default_factory=lambda: int(os.getenv("QML_LAYERS", "3")))
    shots: Optional[int] = field(default_factory=lambda: (
        int(os.getenv("QML_SHOTS")) if os.getenv("QML_SHOTS") and os.getenv("QML_SHOTS") != "0" else None
    ))
    timeout_seconds: float = field(default_factory=lambda: float(os.getenv("QML_TIMEOUT_SECONDS", "3.0")))
    supported_tasks: List[str] = field(default_factory=lambda: [
        t.strip() for t in os.getenv("QML_TASKS", "change_analysis,optical_sar_fusion,vqa").split(",")
    ])
    results_dir: str = field(default_factory=lambda: os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "results"
    ))

    def is_task_supported(self, task: str) -> bool:
        if not self.enabled:
            return False
        return task in self.supported_tasks

# Singleton instance
qml_config = QMLConfig()
