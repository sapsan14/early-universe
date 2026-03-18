"""Tests for inflation models."""

import pytest

from archeon.physics.inflation import (
    compare_models,
    quadratic_slow_roll,
    starobinsky_slow_roll,
    power_law_slow_roll,
)


class TestStarobinsky:
    def test_ns_planck_compatible(self):
        """n_s for Starobinsky should match Planck 2018: 0.9649 ± 0.0042."""
        sr = starobinsky_slow_roll(N=55.0)
        assert 0.955 < sr.n_s < 0.975, f"n_s = {sr.n_s}"

    def test_r_small(self):
        """r for Starobinsky should be very small (< 0.01)."""
        sr = starobinsky_slow_roll(N=55.0)
        assert sr.r < 0.01, f"r = {sr.r}"

    def test_epsilon_small(self):
        """Slow-roll requires epsilon << 1."""
        sr = starobinsky_slow_roll(N=55.0)
        assert sr.epsilon < 0.01


class TestQuadratic:
    def test_ns_reasonable(self):
        """n_s for quadratic should be in plausible range."""
        sr = quadratic_slow_roll(N=55.0)
        assert 0.95 < sr.n_s < 0.98

    def test_r_larger_than_starobinsky(self):
        """Quadratic model predicts larger r than Starobinsky."""
        sr_q = quadratic_slow_roll(N=55.0)
        sr_s = starobinsky_slow_roll(N=55.0)
        assert sr_q.r > sr_s.r


class TestPowerLaw:
    def test_linear_potential(self):
        """p=1 (linear) should give well-defined slow-roll params."""
        sr = power_law_slow_roll(N=55.0, p=1.0)
        assert 0.95 < sr.n_s < 0.98
        assert sr.r > 0

    def test_higher_p_higher_r(self):
        """Higher p should give larger r."""
        sr1 = power_law_slow_roll(N=55.0, p=1.0)
        sr2 = power_law_slow_roll(N=55.0, p=2.0)
        assert sr2.r > sr1.r


class TestCompareModels:
    def test_all_models_return(self):
        """compare_models should return all implemented models."""
        models = compare_models(N=55.0)
        assert "quadratic" in models
        assert "starobinsky" in models
        assert "natural_f5" in models
        assert "linear_p1" in models

    def test_all_ns_reasonable(self):
        """All models should give n_s in a reasonable range."""
        models = compare_models(N=55.0)
        for name, sr in models.items():
            assert 0.9 < sr.n_s < 1.05, f"{name}: n_s = {sr.n_s}"
