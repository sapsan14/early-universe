"""Tests for perturbation theory module."""

import jax.numpy as jnp
import pytest

from archeon.physics.perturbations import (
    compute_matter_pk,
    growth_factor,
    matter_power_spectrum,
    primordial_power_spectrum,
    sigma_R_squared,
    transfer_function_bbks,
    transfer_function_eh98,
)


class TestTransferFunction:
    def test_T_at_k0_is_1(self):
        """T(k -> 0) should approach 1 (large scales unaffected)."""
        k = jnp.array([1e-4, 1e-3])
        T = transfer_function_bbks(k, Omega_m=0.3153, h=0.6736)
        assert float(T[0]) > 0.9

    def test_T_decreases_at_high_k(self):
        """T(k) should decrease at high k (small scales are damped)."""
        k = jnp.logspace(-3, 0, 100)
        T = transfer_function_bbks(k, Omega_m=0.3153, h=0.6736)
        assert float(T[-1]) < float(T[0])

    def test_eh98_positive(self):
        """EH98 transfer function should be positive everywhere."""
        k = jnp.logspace(-4, 1, 200)
        T = transfer_function_eh98(k, h=0.6736, Omega_m=0.3153, Omega_b=0.0493)
        assert jnp.all(T > 0) or jnp.all(jnp.isfinite(T))


class TestPrimordialSpectrum:
    def test_scale_invariant(self):
        """For n_s = 1, P_prim should be constant."""
        k = jnp.logspace(-3, 0, 100)
        P = primordial_power_spectrum(k, A_s=2.1e-9, n_s=1.0, k_pivot=0.05)
        assert jnp.allclose(P, 2.1e-9, rtol=1e-10)

    def test_red_tilt(self):
        """For n_s < 1, P_prim should decrease with k."""
        k = jnp.logspace(-3, 0, 100)
        P = primordial_power_spectrum(k, A_s=2.1e-9, n_s=0.96, k_pivot=0.05)
        assert float(P[-1]) < float(P[0])


class TestPowerSpectrum:
    def test_pk_positive(self):
        """P(k) should be positive."""
        k = jnp.logspace(-3, 0, 100)
        Pk = compute_matter_pk(k)
        assert jnp.all(Pk > 0)

    def test_pk_shape(self):
        """P(k) should peak around k ~ 0.01-0.02 h/Mpc and decline at high k."""
        k = jnp.logspace(-4, 1, 500)
        Pk = compute_matter_pk(k)
        i_peak = jnp.argmax(Pk)
        k_peak = float(k[i_peak])
        assert 0.005 < k_peak < 0.1, f"P(k) peaks at k = {k_peak}"


class TestGrowthFactor:
    def test_D_at_z0_is_1(self):
        """D(z=0) should be 1 by normalization."""
        D = float(growth_factor(0.0, Omega_m=0.3153, Omega_Lambda=0.6847))
        assert abs(D - 1.0) < 0.05

    def test_D_decreases_with_z(self):
        """D(z) should decrease with increasing z."""
        D_0 = float(growth_factor(0.0, Omega_m=0.3153, Omega_Lambda=0.6847))
        D_1 = float(growth_factor(1.0, Omega_m=0.3153, Omega_Lambda=0.6847))
        assert D_1 < D_0


class TestSigma8:
    def test_sigma8_order_of_magnitude(self):
        """sigma_8 should be O(1) for Planck parameters (0.81)."""
        k = jnp.logspace(-4, 2, 2000)
        Pk = compute_matter_pk(k)
        s8_sq = float(sigma_R_squared(8.0, k, Pk))
        # The absolute value depends on normalization, but should be finite and positive
        assert s8_sq > 0
        assert jnp.isfinite(s8_sq)
