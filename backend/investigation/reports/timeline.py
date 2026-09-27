"""
TRINETRA Phase 6 — Investigation Timeline Formatter
Constructs chronological milestone sequences mapping Earth-Observation observations
to detected surface transitions.
"""

from typing import Dict, Any, List, Optional


class TimelineFormatter:
    """
    Renders chronological milestones for multi-temporal investigations.
    """

    @classmethod
    def format_timeline(
        cls,
        observations: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
        evidence_items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        milestones = []
        sorted_obs = sorted(observations, key=lambda o: o.get("datetime", "") or "")

        for idx, obs in enumerate(sorted_obs):
            obs_id = obs.get("id", f"obs_{idx+1}")
            obs_date = (obs.get("datetime") or "2026-01-01T00:00:00Z")[:10]
            platform = obs.get("properties", {}).get("platform", "Satellite Sensor")

            is_first = (idx == 0)
            is_last = (idx == len(sorted_obs) - 1)

            if is_first:
                event_type = "BASELINE"
                title = f"Baseline Observation — {platform}"
                desc = "Initial reference state; vegetated/open surface with baseline spectral response."
            elif is_last:
                event_type = "TERMINAL_STATE"
                title = f"Target Evaluation — {platform}"
                desc = "Subsequent acquisition verifying physical surface transformation and newly emerged structures."
            else:
                event_type = "INTERMEDIATE"
                title = f"Transitional Epoch — {platform}"
                desc = "Interim acquisition capturing ongoing earthworks and clearance activities."

            # Find matching evidence for this date or observation
            matching_ev = [
                e.get("id") for e in evidence_items
                if obs_id in e.get("observation_ids", [])
            ]

            milestones.append({
                "index": idx,
                "date": obs_date,
                "observation_id": obs_id,
                "platform": platform,
                "event_type": event_type,
                "title": title,
                "description": desc,
                "associated_evidence_ids": matching_ev,
            })

        return milestones
