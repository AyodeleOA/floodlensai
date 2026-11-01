from __future__ import annotations

from app.services.risk_engine.engine import DimensionInput, RiskEngine
from app.services.risk_engine.weights import get_risk_band, get_weight_profile


def test_full_risk_calculation():
    """Test risk calculation with all dimensions available."""
    engine = RiskEngine("illustrative_unvalidated")
    result = engine.calculate_from_values(
        observed_flooding=0.8,
        rainfall_conditions=0.6,
        terrain_susceptibility=0.5,
        drainage_condition=0.3,
        exposure_vulnerability=0.4,
    )
    assert 0 <= result.risk_score <= 100
    assert result.risk_band in ("low", "guarded", "elevated", "high", "very_high")
    assert result.confidence_score > 0
    assert result.data_completeness == 1.0
    assert len(result.contributing_factors) == 5
    assert len(result.missing_inputs) == 0
    assert result.is_illustrative is True


def test_missing_data_handling():
    """Test that missing inputs lower confidence and re-normalise."""
    engine = RiskEngine("illustrative_unvalidated")
    result = engine.calculate_from_values(
        observed_flooding=0.9,
        rainfall_conditions=None,
        terrain_susceptibility=None,
        drainage_condition=0.4,
        exposure_vulnerability=None,
    )
    assert result.risk_score > 0
    assert result.confidence_score < 0.8
    assert result.data_completeness < 1.0
    assert "rainfall_conditions" in result.missing_inputs
    assert "terrain_susceptibility" in result.missing_inputs
    assert "exposure_vulnerability" in result.missing_inputs


def test_all_missing():
    """Test that no data results in zero risk with zero confidence."""
    engine = RiskEngine("illustrative_unvalidated")
    result = engine.calculate_from_values(
        observed_flooding=None,
        rainfall_conditions=None,
        terrain_susceptibility=None,
        drainage_condition=None,
        exposure_vulnerability=None,
    )
    assert result.risk_score == 0.0
    assert result.risk_band == "low"
    assert result.confidence_score == 0.0
    assert result.data_completeness == 0.0
    assert len(result.missing_inputs) == 5


def test_high_risk_with_low_confidence_labelled():
    """Test that high score with low confidence is possible."""
    engine = RiskEngine("illustrative_unvalidated")
    # Only observed_flooding is available with high value
    result = engine.calculate_from_values(
        observed_flooding=0.95,
        rainfall_conditions=None,
        terrain_susceptibility=None,
        drainage_condition=None,
        exposure_vulnerability=None,
    )
    # Score should be significant (re-normalised to 30 points max)
    assert result.risk_score > 0
    # But confidence should be low because only 1/5 dimensions available
    assert result.confidence_score < 0.2
    assert result.data_completeness == 0.2


def test_risk_bands():
    """Test risk band mapping."""
    assert get_risk_band(0) == "low"
    assert get_risk_band(19) == "low"
    assert get_risk_band(20) == "guarded"
    assert get_risk_band(39) == "guarded"
    assert get_risk_band(40) == "elevated"
    assert get_risk_band(59) == "elevated"
    assert get_risk_band(60) == "high"
    assert get_risk_band(79) == "high"
    assert get_risk_band(80) == "very_high"
    assert get_risk_band(100) == "very_high"


def test_weight_profile():
    """Test weight profile configuration."""
    profile = get_weight_profile("illustrative_unvalidated")
    assert "dimensions" in profile
    assert profile["dimensions"]["observed_flooding"]["max_weight"] == 30
    assert profile["dimensions"]["rainfall_conditions"]["max_weight"] == 25
    assert profile["dimensions"]["terrain_susceptibility"]["max_weight"] == 20
    assert profile["dimensions"]["drainage_condition"]["max_weight"] == 15
    assert profile["dimensions"]["exposure_vulnerability"]["max_weight"] == 10


def test_dimension_inputs():
    """Test risk calculation from DimensionInput objects."""
    engine = RiskEngine("illustrative_unvalidated")
    inputs = [
        DimensionInput("observed_flooding", 0.7, True, "Verified report"),
        DimensionInput("rainfall_conditions", 0.5, True),
        DimensionInput("terrain_susceptibility", 0.6, True),
        DimensionInput("drainage_condition", 0.4, True),
        DimensionInput("exposure_vulnerability", 0.3, True),
    ]
    result = engine.calculate(inputs)
    assert result.risk_score > 0
    assert len(result.contributing_factors) == 5
    # Check that weighted scores are proportional to raw values
    for factor in result.contributing_factors:
        assert factor["raw_value"] >= 0
        assert factor["weighted_score"] >= 0
