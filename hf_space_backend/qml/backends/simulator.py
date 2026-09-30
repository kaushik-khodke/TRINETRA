"""
SatQuery AI / TRINETRA — Quantum Backend Abstraction
Decouples high-level QML models and agent services from specific simulator
devices (PennyLane default.qubit, lightning.qubit) and future physical QPUs.
"""

import time
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple

from ..config import qml_config

try:
    import pennylane as qml
    HAS_PENNYLANE = True
except ImportError:
    HAS_PENNYLANE = False
    qml = None

class QuantumBackend(ABC):
    """Abstract interface for all quantum execution targets (simulators or real hardware)."""

    def __init__(self, num_qubits: int = 4, shots: Optional[int] = None):
        self.num_qubits = num_qubits
        self.shots = shots
        self.backend_type = "unknown"

    @abstractmethod
    def get_device(self):
        """Returns the underlying PennyLane device or execution handle."""
        pass

    @abstractmethod
    def run(self, qnode, *args, **kwargs) -> Any:
        """Executes a quantum circuit and returns measurement expectation values."""
        pass

    @abstractmethod
    def get_telemetry(self) -> Dict[str, Any]:
        """Returns runtime hardware telemetry (qubits, shots, backend name)."""
        pass


class SimulatorBackend(QuantumBackend):
    """
    Local Quantum Simulator Backend.
    Uses PennyLane default.qubit or lightning.qubit for exact statevector simulation.
    """

    def __init__(self, num_qubits: int = 4, device_name: str = "default.qubit", shots: Optional[int] = None):
        super().__init__(num_qubits=num_qubits, shots=shots)
        self.device_name = device_name
        self.backend_type = "local_simulator"
        self._device = None
        self._init_device()

    def _init_device(self):
        if not HAS_PENNYLANE:
            return

        # Attempt high-performance lightning.qubit first if requested
        if "lightning" in self.device_name:
            try:
                self._device = qml.device("lightning.qubit", wires=self.num_qubits, shots=self.shots)
                self.device_name = "lightning.qubit"
                return
            except Exception:
                pass  # Fall back to default.qubit

        # Standard pure-Python/NumPy statevector device
        try:
            self._device = qml.device("default.qubit", wires=self.num_qubits, shots=self.shots)
            self.device_name = "default.qubit"
        except Exception as e:
            self._device = None

    def get_device(self):
        return self._device

    def is_available(self) -> bool:
        return HAS_PENNYLANE and (self._device is not None)

    def run(self, qnode, *args, **kwargs) -> Any:
        t0 = time.perf_counter()
        res = qnode(*args, **kwargs)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return res, latency_ms

    def get_telemetry(self) -> Dict[str, Any]:
        return {
            "backend_type": self.backend_type,
            "device": self.device_name,
            "num_qubits": self.num_qubits,
            "shots": self.shots or "Analytic (Exact Statevector)",
            "pennylane_installed": HAS_PENNYLANE,
            "pennylane_version": getattr(qml, "__version__", "not_installed") if HAS_PENNYLANE else None
        }


class FutureHardwareBackend(QuantumBackend):
    """
    Physical Quantum Processing Unit (QPU) Abstraction.
    Reserved for future execution on physical hardware (ISRO / IBM / Rigetti / AWS Braket).
    """

    def __init__(self, qpu_name: str = "ibm_brisbane", num_qubits: int = 8, shots: int = 2048):
        super().__init__(num_qubits=num_qubits, shots=shots)
        self.qpu_name = qpu_name
        self.backend_type = "physical_qpu_target"

    def get_device(self):
        raise NotImplementedError(
            f"Physical QPU execution on '{self.qpu_name}' requires active QPU credentials and calibration data."
        )

    def run(self, qnode, *args, **kwargs) -> Any:
        raise NotImplementedError("Physical QPU execution not connected in offline hackathon mode.")

    def get_telemetry(self) -> Dict[str, Any]:
        return {
            "backend_type": self.backend_type,
            "qpu_name": self.qpu_name,
            "num_qubits": self.num_qubits,
            "shots": self.shots,
            "status": "Hardware-Ready (Awaiting QPU dispatch queue)"
        }


def get_quantum_backend(num_qubits: Optional[int] = None) -> QuantumBackend:
    qubits = num_qubits or qml_config.num_qubits
    return SimulatorBackend(
        num_qubits=qubits,
        device_name=qml_config.device_name,
        shots=qml_config.shots
    )
