from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.services.risk_engine.weights import get_risk_band, get_weight_profile


@dataclass
class DimensionInput:
    """Input for a single risk dimension."""

    dimension: str
    raw_score: float  # 0.0 to 1.0 (normalised)
    available: bool = True
    description: str | None = None


@dataclass
class RiskResult:
    """Result of a risk calculation."""

    risk_score: float
    risk_band: str
    confidence_score: float
    data_completeness: float
    contributing_factors: list[dict[str, Any]] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)
    calculation_version: str = "0.1.0"
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: datetime | None = None
    is_illustrative: bool = True


class RiskEngine:
    """Configurable Flood Risk Index (FRI) calculator.

    A transparent, configurable decision-support indicator.
    Not a hydrological forecast or official warning.
    """

    def __init__(self, profile_name: str = "illustrative_unvalidated") -> None:
        self.profile = get_weight_profile(profile_name)
        self.profile_name = profile_name
        self.dimensions = self.profile["dimensions"]

    def calculate(self, inputs: list[DimensionInput]) -> RiskResult:
        """Calculate the Flood Risk Index from dimension inputs.

        Missing inputs are NOT treated as zero risk.
        Re-normalise only across available dimensions and lower confidence.
        """
        available_dims = [inp for inp in inputs if inp.available and inp.dimension in self.dimensions]
        available_names = {inp.dimension for inp in available_dims}
        all_missing = [
            dim_name for dim_name in self.dimensions
            if dim_name not in available_names
        ]

        if not available_dims:
            # No data at all — return zero with very low confidence
            return RiskResult(
                risk_score=0.0,
                risk_band="low",
                confidence_score=0.0,
                data_completeness=0.0,
                missing_inputs=all_missing,
                is_illustrative=True,
            )

        # Re-normalise weights across available dimensions only
        total_max_weight = sum(self.dimensions[d.dimension]["max_weight"] for d in available_dims)
        total_max_possible = sum(d["max_weight"] for d in self.dimensions.values())

        weighted_sum = 0.0
        contributing_factors: list[dict[str, Any]] = []

        for inp in available_dims:
            dim_config = self.dimensions[inp.dimension]
            max_weight = dim_config["max_weight"]
            # Scale weight proportionally to available dimensions
            scaled_max = (max_weight / total_max_weight) * total_max_possible if total_max_weight > 0 else 0
            weighted = inp.raw_score * scaled_max
            weighted_sum += weighted
            contributing_factors.append({
                "dimension": inp.dimension,
                "label": dim_config["label"],
                "raw_value": round(inp.raw_score, 4),
                "weighted_score": round(weighted, 2),
                "max_weight": round(scaled_max, 2),
                "description": inp.description or dim_config["description"],
            })

        # Clamp to 0-100
        risk_score = min(max(weighted_sum, 0.0), 100.0)
        risk_band = get_risk_band(risk_score, self.profile_name)

        # Confidence: proportion of dimensions available, adjusted by data quality
        num_available = len(available_dims)
        num_total = len(self.dimensions)
        data_completeness = num_available / num_total if num_total > 0 else 0.0

        # Confidence is lower when fewer dimensions are available
        confidence_score = data_completeness * 0.8  # Max 0.8 for illustrative profile
        if data_completeness < 1.0:
            confidence_score *= 0.7  # Further reduce confidence for incomplete data

        return RiskResult(
            risk_score=round(risk_score, 1),
            risk_band=risk_band,
            confidence_score=round(confidence_score, 2),
            data_completeness=round(data_completeness, 2),
            contributing_factors=contributing_factors,
            missing_inputs=all_missing,
            source_ids=[],
            calculation_version="0.1.0",
            is_illustrative=True,
        )

    def calculate_from_values(
        self,
        observed_flooding: float | None = None,
        rainfall_conditions: float | None = None,
        terrain_susceptibility: float | None = None,
        drainage_condition: float | None = None,
        exposure_vulnerability: float | None = None,
    ) -> RiskResult:
        """Convenience method to calculate risk from raw dimension values (0.0–1.0).

        Pass None for any dimension that has no data.
        """
        inputs = [
            DimensionInput("observed_flooding", observed_flooding, observed_flooding is not None),
            DimensionInput("rainfall_conditions", rainfall_conditions, rainfall_conditions is not None),
            DimensionInput("terrain_susceptibility", terrain_susceptibility, terrain_susceptibility is not None),
            DimensionInput("drainage_condition", drainage_condition, drainage_condition is not None),
            DimensionInput("exposure_vulnerability", exposure_vulnerability, exposure_vulnerability is not None),
        ]
        return self.calculate(inputs)
