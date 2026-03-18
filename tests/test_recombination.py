"""Tests for recombination physics."""

import jax.numpy as jnp
import pytest

from archeon.physics.recombination import (
    case_B_recombination_rate,
    saha_ionization_fraction,
    solve_peebles,
)
from archeon.config import get_constants


class TestSahaEquation:
    def test_fully_ionized_at_high_T(self):
        """At T >> 10^4 K, everything should be ionized (x_e ~ 1)."""
        const = get_constants()
        T = jnp.array(50000.0)
        n_b = jnp.array(1e6)
        x_e = saha_ionization_fraction(
            T, n_b,
            const["k_B"], const["m_e"], const["hbar"],
            const["E_ion_H"], const["k_B_eV"]
        )
        assert float(x_e) > 0.99

    def test_neutral_at_low_T(self):
        """At T << 3000 K, hydrogen should be mostly neutral (x_e ~ 0)."""
        const = get_constants()
        T = jnp.array(1000.0)
        n_b = jnp.array(1e6)
        x_e = saha_ionization_fraction(
            T, n_b,
            const["k_B"], const["m_e"], const["hbar"],
            const["E_ion_H"], const["k_B_eV"]
        )
        assert float(x_e) < 0.01


class TestRecombinationRate:
    def test_alpha_positive(self):
        """Recombination rate should be positive."""
        T = jnp.array(3000.0)
        alpha = case_B_recombination_rate(T)
        assert float(alpha) > 0

    def test_alpha_decreases_with_T(self):
        """Higher temperature -> lower recombination rate."""
        T_low = jnp.array(2000.0)
        T_high = jnp.array(10000.0)
        assert float(case_B_recombination_rate(T_low)) > float(case_B_recombination_rate(T_high))


class TestPeeblesIntegration:
    def test_xe_starts_ionized(self):
        """x_e should start near 1 at high z."""
        z_arr, xe_arr = solve_peebles(z_start=1800.0, z_end=200.0, n_steps=2000)
        assert float(xe_arr[0]) > 0.95

    def test_xe_drops_during_recombination(self):
        """x_e should drop significantly by z ~ 800."""
        z_arr, xe_arr = solve_peebles(z_start=1800.0, z_end=200.0, n_steps=2000)
        # Find x_e at z ~ 800
        idx_800 = jnp.argmin(jnp.abs(z_arr - 800.0))
        assert float(xe_arr[idx_800]) < 0.1, f"x_e(z=800) = {float(xe_arr[idx_800])}"

    def test_freeze_out(self):
        """x_e should freeze out at a residual value > 0 (not reach zero)."""
        z_arr, xe_arr = solve_peebles(z_start=1800.0, z_end=200.0, n_steps=2000)
        assert float(xe_arr[-1]) > 1e-5, "Residual ionization expected"
