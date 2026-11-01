from __future__ import annotations

from typing import Any

# Risk dimension weight profiles
# All profiles are labelled until calibrated with local flood records
WEIGHT_PROFILES: dict[str, dict[str, Any]] = {
    "illustrative_unvalidated": {
        "label": "Illustrative (Unvalidated)",
        "description": "Initial demo weights. Not calibrated. Do not use for operational decisions.",
        "dimensions": {
            "observed_flooding": {
                "max_weight": 30,
                "label": "Observed Flooding",
                "description": "Verified recent reports, observed extent, recurrence, evidence quality",
            },
            "rainfall_conditions": {
                "max_weight": 25,
                "label": "Rainfall Conditions",
                "description": "Recent rainfall accumulation, forecast if configured",
            },
            "terrain_susceptibility": {
                "max_weight": 20,
                "label": "Terrain Susceptibility",
                "description": "Elevation, slope, depressions, flow accumulation",
            },
            "drainage_condition": {
                "max_weight": 15,
                "label": "Drainage Condition",
                "description": "Proximity to drainage, blockage reports, density/gaps",
            },
            "exposure_vulnerability": {
                "max_weight": 10,
                "label": "Exposure / Vulnerability",
                "description": "Proximity to roads, markets, schools, health facilities, settlements",
            },
        },
        "risk_bands": {
            "low": (0, 19),
            "guarded": (20, 39),
            "elevated": (40, 59),
            "high": (60, 79),
            "very_high": (80, 100),
        },
    },
}


def get_weight_profile(name: str) -> dict[str, Any]:
    """Get a risk weight profile by name."""
    if name not in WEIGHT_PROFILES:
        raise ValueError(f"Unknown weight profile: {name}")
    return WEIGHT_PROFILES[name]


def get_risk_band(score: float, profile_name: str = "illustrative_unvalidated") -> str:
    """Map a risk score to its band label."""
    profile = get_weight_profile(profile_name)
    for band, (low, high) in profile["risk_bands"].items():
        if low <= score <= high:
            return band
    return "low"
