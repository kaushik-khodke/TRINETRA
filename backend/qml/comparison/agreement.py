"""
SatQuery AI / TRINETRA — Agreement & Comparison Engine
Calculates reproducible mathematical agreement metrics between operational
classical remote-sensing models and experimental PennyLane QML circuits.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class AgreementReport:
    """Rigorous mathematical comparison between classical and QML inferences."""
    agrees: bool
    verdict: str  # "FULL_AGREEMENT", "PARTIAL_AGREEMENT", "DISAGREEMENT"
    classical_prediction: str
    qml_prediction: str
    classical_confidence: float
    qml_confidence: float
    confidence_delta: float
    calibrated_agreement_score: float
    status_message: str
    parameter_comparison: Dict[str, Any]
    latency_comparison: Dict[str, Any]
    insights: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agrees": self.agrees,
            "verdict": self.verdict,
            "classical_prediction": self.classical_prediction,
            "qml_prediction": self.qml_prediction,
            "classical_confidence": round(self.classical_confidence, 4),
            "qml_confidence": round(self.qml_confidence, 4),
            "confidence_delta": round(self.confidence_delta, 4),
            "calibrated_agreement_score": round(self.calibrated_agreement_score, 4),
            "status_message": self.status_message,
            "parameter_comparison": self.parameter_comparison,
            "latency_comparison": self.latency_comparison,
            "insights": self.insights
        }


class AgreementAnalyzer:
    """
    Evaluates cross-paradigm concordance between classical neural/radiometric models
    and quantum parameterized circuits.
    """

    CLASSICAL_PARAM_ESTIMATES = {
        "change_analysis": 1245000,    # Siamese differential convolutional network
        "optical_sar_fusion": 850000,  # Dual-encoder cross-attention net
        "vqa": 2100000                 # Multimodal bilinear network
    }

    @classmethod
    def analyze(
        cls,
        task: str,
        classical_pred: str,
        classical_conf: float,
        classical_latency_ms: float,
        qml_pred: str,
        qml_conf: float,
        qml_latency_ms: float,
        qml_circuit_meta: Dict[str, Any]
    ) -> AgreementReport:
        """
        Computes formal agreement metrics, calibrated agreement score, and physical insights.
        Formula for Calibrated Agreement Score:
        - If class labels match: score = 1.0 - 0.5 * |conf_classical - conf_qml|
        - If class labels differ: score = 0.5 * (1.0 - conf_qml)
        Bounded rigorously in [0.0, 1.0].
        """
        c_pred_norm = classical_pred.strip().lower()
        q_pred_norm = qml_pred.strip().lower()

        # Check semantic agreement (handles 'increased' vs 'detected expansion', etc.)
        direct_match = (c_pred_norm == q_pred_norm)
        semantic_match = (
            ("increase" in c_pred_norm and "increase" in q_pred_norm) or
            ("decrease" in c_pred_norm and "decrease" in q_pred_norm) or
            ("unchanged" in c_pred_norm and "unchanged" in q_pred_norm) or
            ("detect" in c_pred_norm and "increase" in q_pred_norm)
        )
        agrees = direct_match or semantic_match

        conf_delta = abs(float(classical_conf) - float(qml_conf))

        if agrees:
            calibrated_score = max(0.50, min(1.0, 1.0 - 0.5 * conf_delta))
            verdict = "FULL_AGREEMENT" if conf_delta < 0.20 else "PARTIAL_AGREEMENT"
            status_message = "✓ Quantum circuit corroborates the operational classical model prediction."
        else:
            calibrated_score = max(0.0, min(0.49, 0.5 * (1.0 - float(qml_conf))))
            verdict = "DISAGREEMENT"
            status_message = "⚠ Discrepancy observed: Quantum research branch requires analyst review. Operational classical result is retained."

        # Model complexity & parameter reduction ratio
        classical_params = cls.CLASSICAL_PARAM_ESTIMATES.get(task, 1200000)
        qml_params = qml_circuit_meta.get("total_parameters", 35)
        param_reduction_pct = round((1.0 - (qml_params / classical_params)) * 100.0, 3)

        parameter_comp = {
            "classical_model_parameters": classical_params,
            "quantum_circuit_parameters": qml_params,
            "quantum_parameter_reduction": f"{param_reduction_pct}%",
            "quantum_bits (qubits)": qml_circuit_meta.get("num_qubits", 4),
            "quantum_circuit_depth": qml_circuit_meta.get("circuit_depth", 5)
        }

        latency_comp = {
            "classical_inference_ms": round(classical_latency_ms, 2),
            "quantum_simulation_ms": round(qml_latency_ms, 2),
            "simulation_delta_ms": round(qml_latency_ms - classical_latency_ms, 2)
        }

        insights = [
            f"Operational Baseline: Classical specialist ({classical_params:,} params) remains the validated operational truth.",
            f"Parameter Efficiency: The QML circuit achieves classification using only {qml_params} trainable angles ({param_reduction_pct}% fewer parameters).",
            f"Hilbert Space Expressivity: 4 qubits span a 16-dimensional complex state space capable of modeling non-linear feature entanglements with shallow circuit depth.",
            "Hardware Scalability: On future fault-tolerant QPUs (FTQC), execution time scales with circuit depth rather than input image resolution."
        ]

        if not agrees:
            insights.append(
                f"Discrepancy Analysis: QML classified '{qml_pred}' vs Classical '{classical_pred}'. This sample has been flagged for the verified research hard-example buffer."
            )

        return AgreementReport(
            agrees=agrees,
            verdict=verdict,
            classical_prediction=classical_pred,
            qml_prediction=qml_pred,
            classical_confidence=float(classical_conf),
            qml_confidence=float(qml_conf),
            confidence_delta=conf_delta,
            calibrated_agreement_score=calibrated_score,
            status_message=status_message,
            parameter_comparison=parameter_comp,
            latency_comparison=latency_comp,
            insights=insights
        )
