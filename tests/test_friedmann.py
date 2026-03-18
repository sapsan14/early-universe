"""Tests for the Friedmann equation solver.

Validates against known Planck 2018 values and analytical limits.
"""

import jax.numpy as jnp
import pytest

from archeon.physics.friedmann import (
    E_squared,
    age_of_universe,
    angular_diameter_distance,
    comoving_distance,
    conformal_time,
    cosmic_time,
    deceleration_parameter,
    evolve_scale_factor,
    hubble,
    hubble_from_z,
    luminosity_distance,
    matter_radiation_equality,
    params_from_config,
    redshift_matter_radiation_equality,
    solve_background,
)

# Planck 2018 best-fit
H0 = 67.36
Om = 0.3153
Or = 9.14e-5
OL = 0.6847
Ok = 0.0


class TestHubbleParameter:
    def test_H_at_a1_equals_H0(self):
        """At a=1 (today), H(a) should equal H0."""
        H = hubble(1.0, H0, Om, Or, OL, Ok)
        assert abs(float(H) - H0) / H0 < 1e-4

    def test_E_squared_at_a1(self):
        """E^2(a=1) = Omega_r + Omega_m + Omega_k + Omega_Lambda ~ 1."""
        E2 = E_squared(1.0, Om, Or, OL, Ok)
        assert abs(float(E2) - 1.0) < 1e-3

    def test_radiation_dominated_early(self):
        """At very small a, radiation term dominates: E^2 ~ Omega_r/a^4."""
        a = 1e-6
        E2 = float(E_squared(a, Om, Or, OL, Ok))
        rad_term = Or / a**4
        assert abs(E2 - rad_term) / rad_term < 0.01

    def test_H_increases_with_redshift(self):
        """H(z) should increase monotonically at z > 0."""
        z_vals = jnp.array([0.0, 0.5, 1.0, 2.0, 5.0, 10.0])
        H_vals = hubble_from_z(z_vals, H0, Om, Or, OL, Ok)
        for i in range(len(H_vals) - 1):
            assert H_vals[i] < H_vals[i + 1]


class TestAgeOfUniverse:
    def test_age_planck(self):
        """Age should be ~13.8 Gyr (Planck 2018: 13.797 ± 0.023 Gyr)."""
        age = float(age_of_universe(H0, Om, Or, OL, Ok))
        assert 13.5 < age < 14.1, f"Age = {age} Gyr, expected ~13.8"

    def test_cosmic_time_at_half(self):
        """t(a=0.5) should be less than t(a=1)."""
        t_half = float(cosmic_time(0.5, H0, Om, Or, OL, Ok))
        t_full = float(cosmic_time(1.0, H0, Om, Or, OL, Ok))
        assert 0 < t_half < t_full


class TestDistances:
    def test_comoving_at_z0(self):
        """Comoving distance to z=0 should be 0."""
        chi = float(comoving_distance(0.0, H0, Om, Or, OL, Ok))
        assert abs(chi) < 1.0  # < 1 Mpc due to numerics

    def test_comoving_to_cmb(self):
        """Comoving distance to z=1100 should be ~14 Gpc."""
        chi = float(comoving_distance(1100.0, H0, Om, Or, OL, Ok))
        assert 13000 < chi < 15000, f"chi(z=1100) = {chi} Mpc"

    def test_dL_greater_than_dA(self):
        """d_L > d_A for z > 0 (Etherington reciprocity: d_L = (1+z)^2 * d_A)."""
        z = 1.0
        dL = float(luminosity_distance(z, H0, Om, Or, OL, Ok))
        dA = float(angular_diameter_distance(z, H0, Om, Or, OL, Ok))
        assert dL > dA
        assert abs(dL / dA - (1 + z)**2) < 0.01


class TestMatterRadiationEquality:
    def test_z_eq_planck(self):
        """z_eq should be ~3400 (Planck 2018: 3387)."""
        z_eq = float(redshift_matter_radiation_equality(Om, Or))
        assert 3000 < z_eq < 4000, f"z_eq = {z_eq}"


class TestDeceleration:
    def test_deceleration_today(self):
        """Universe is accelerating today: q(a=1) < 0."""
        q = float(deceleration_parameter(1.0, Om, Or, OL, Ok))
        assert q < 0, f"q(a=1) = {q}, expected < 0 (accelerating)"

    def test_deceleration_early(self):
        """Early universe is decelerating: q(a=0.01) > 0."""
        q = float(deceleration_parameter(0.01, Om, Or, OL, Ok))
        assert q > 0, f"q(a=0.01) = {q}, expected > 0 (decelerating)"


class TestScaleFactorEvolution:
    def test_a_increases(self):
        """Scale factor should increase monotonically."""
        t_arr, a_arr = evolve_scale_factor(H0, Om, Or, OL, Ok)
        da = jnp.diff(a_arr)
        assert jnp.all(da > 0)


class TestSolveBackground:
    def test_full_solution(self):
        """Test the convenience solver."""
        sol = solve_background("planck2018")
        assert 13.5 < sol.age_gyr < 14.1
        assert 3000 < sol.z_eq < 4000
        assert sol.params.H0 == 67.36
