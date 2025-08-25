import pytest
import sys
import os

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from render.render import RenderHelper


class TestMoonPhase:
    """Test suite for moon phase calculations."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            (0.0, "wi-moon-new"),
            (0.25, "wi-moon-first-quarter"),
            (0.5, "wi-moon-full"),
            (0.75, "wi-moon-third-quarter"),
            (1.0, "wi-moon-new"),
        ],
    )
    def test_wi_moon_phase_boundary_values(self, value, expected):
        """Test moon phase with exact boundary values between phases."""
        result = RenderHelper.wi_moon_phase(value)
        assert result == expected

    @pytest.mark.parametrize(
        "value,expected",
        [
            # Test values very close to 0
            (0.001, "wi-moon-waxing-crescent-0"),
            (0.01, "wi-moon-waxing-crescent-0"),
            # Test values very close to 0.25
            (0.249, "wi-moon-waxing-crescent-5"),
            (0.251, "wi-moon-waxing-gibbous-1"),
            # Test values very close to 0.5
            (0.499, "wi-moon-waxing-gibbous-6"),
            (0.501, "wi-moon-waning-gibbous-1"),
            # Test values very close to 0.75
            (0.749, "wi-moon-waning-gibbous-6"),
            (0.751, "wi-moon-waning-crescent-1"),
            # Test values very close to 1.0
            (0.999, "wi-moon-waning-crescent-6"),
        ],
    )
    def test_wi_moon_phase_very_small_increments(self, value, expected):
        """Test moon phase with very small increments to verify calculation precision."""
        result = RenderHelper.wi_moon_phase(value)
        assert result == expected

    @pytest.mark.parametrize("i", range(6))
    def test_wi_moon_phase_all_crescent_numbers(self, i):
        """Test that all waxing crescent phases produce valid numbers 0-5."""
        # Calculate a value that should produce index i
        value = (i + 0.5) * 0.25 / 6  # Add 0.5 to target middle of range
        result = RenderHelper.wi_moon_phase(value)
        expected_suffix = str(i)
        assert result == f"wi-moon-waxing-crescent-{expected_suffix}"

    @pytest.mark.parametrize(
        "value,expected_num",
        [
            # Test waxing gibbous (0.25 < value < 0.5)
            (0.26, 1),  # Just after 0.25
            (0.30, 2),  # Early waxing gibbous
            (0.35, 3),  # Mid waxing gibbous
            (0.40, 4),  # Late waxing gibbous
            (0.45, 5),  # Very late waxing gibbous
            (0.49, 6),  # Just before full
            # Test waning gibbous (0.5 < value < 0.75)
            (0.51, 1),  # Just after full
            (0.55, 2),  # Early waning gibbous
            (0.60, 3),  # Mid waning gibbous
            (0.65, 4),  # Late waning gibbous
            (0.70, 5),  # Very late waning gibbous
            (0.74, 6),  # Just before third quarter
        ],
    )
    def test_wi_moon_phase_all_gibbous_numbers(self, value, expected_num):
        """Test that all gibbous phases produce valid numbers 1-6."""
        result = RenderHelper.wi_moon_phase(value)
        if value < 0.5:
            assert result == f"wi-moon-waxing-gibbous-{expected_num}"
        else:
            assert result == f"wi-moon-waning-gibbous-{expected_num}"

    @pytest.mark.parametrize(
        "value,expected",
        [
            (0.125, "wi-moon-waxing-crescent-3"),  # 1/8
            (0.375, "wi-moon-waxing-gibbous-4"),  # 3/8
            (0.625, "wi-moon-waning-gibbous-4"),  # 5/8
            (0.875, "wi-moon-waning-crescent-4"),  # 7/8
        ],
    )
    def test_wi_moon_phase_mathematical_precision(self, value, expected):
        """Test moon phase calculation with mathematically precise values."""
        result = RenderHelper.wi_moon_phase(value)
        assert result == expected
