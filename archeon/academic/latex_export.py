"""LaTeX export: publication-quality figures and tables.

Generates matplotlib figures styled for ApJ/MNRAS/A&A journals
and LaTeX tables with cosmological parameter estimates.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


# ---------------------------------------------------------------------------
# Journal styles
# ---------------------------------------------------------------------------

JOURNAL_STYLES = {
    "apj": {
        "figwidth": 3.5,       # single column (inches)
        "figwidth_double": 7.1,
        "fontsize": 10,
        "font_family": "serif",
        "usetex": False,
    },
    "mnras": {
        "figwidth": 3.32,
        "figwidth_double": 6.97,
        "fontsize": 9,
        "font_family": "serif",
        "usetex": False,
    },
    "aa": {
        "figwidth": 3.54,
        "figwidth_double": 7.09,
        "fontsize": 9,
        "font_family": "serif",
        "usetex": False,
    },
}


def apply_journal_style(journal: str = "apj") -> dict:
    """Apply journal-specific matplotlib rcParams."""
    import matplotlib as mpl

    style = JOURNAL_STYLES.get(journal, JOURNAL_STYLES["apj"])
    params = {
        "figure.figsize": (style["figwidth"], style["figwidth"] * 0.75),
        "font.size": style["fontsize"],
        "font.family": style["font_family"],
        "axes.linewidth": 0.8,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "legend.fontsize": style["fontsize"] - 1,
        "legend.frameon": False,
    }
    mpl.rcParams.update(params)
    return style


# ---------------------------------------------------------------------------
# Figure generators
# ---------------------------------------------------------------------------

def plot_power_spectrum(
    ell: np.ndarray,
    cl: np.ndarray,
    label: str = "ARCHEON",
    journal: str = "apj",
    save_path: str | None = None,
    **kwargs: Any,
) -> Any:
    """Plot D_l = l(l+1)C_l / 2π — standard CMB power spectrum figure."""
    import matplotlib.pyplot as plt

    style = apply_journal_style(journal)
    fig, ax = plt.subplots(figsize=(style["figwidth_double"], style["figwidth_double"] * 0.5))

    dl = ell * (ell + 1) * cl / (2 * np.pi)
    ax.plot(ell, dl, label=label, linewidth=1.2, **kwargs)
    ax.set_xlabel(r"Multipole $\ell$")
    ax.set_ylabel(r"$\ell(\ell+1)C_\ell / 2\pi$ [$\mu$K$^2$]")
    ax.set_xscale("log")
    ax.legend()
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig


def plot_parameter_comparison(
    param_names: list[str],
    values: dict[str, np.ndarray],
    uncertainties: dict[str, np.ndarray],
    reference: dict[str, float] | None = None,
    journal: str = "apj",
    save_path: str | None = None,
) -> Any:
    """Whisker plot comparing parameter estimates across methods."""
    import matplotlib.pyplot as plt

    style = apply_journal_style(journal)
    n_params = len(param_names)
    n_methods = len(values)

    fig, ax = plt.subplots(
        figsize=(style["figwidth_double"], max(n_params * 0.5, 3)))

    methods = list(values.keys())
    y_positions = np.arange(n_params)

    for j, method in enumerate(methods):
        offset = (j - n_methods / 2 + 0.5) * 0.15
        ax.errorbar(
            values[method], y_positions + offset,
            xerr=uncertainties[method],
            fmt="o", markersize=4, capsize=3,
            label=method, linewidth=1.0)

    if reference:
        for i, name in enumerate(param_names):
            if name in reference:
                ax.axvline(reference[name], color="gray",
                           linestyle="--", linewidth=0.5, alpha=0.5)

    ax.set_yticks(y_positions)
    ax.set_yticklabels(param_names)
    ax.legend(loc="lower right")
    ax.set_xlabel("Parameter value")
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig


# ---------------------------------------------------------------------------
# LaTeX table generators
# ---------------------------------------------------------------------------

def parameters_to_latex(
    param_names: list[str],
    values: np.ndarray,
    uncertainties: np.ndarray,
    method: str = "CNN",
    caption: str = "Cosmological parameter estimates",
    label: str = "tab:params",
    reference: dict[str, float] | None = None,
) -> str:
    """Generate LaTeX table of parameter estimates.

    Returns a complete \\begin{table}...\\end{table} string.
    """
    lines = [
        r"\begin{table}",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
    ]

    if reference:
        lines.append(r"\begin{tabular}{lccc}")
        lines.append(r"\hline\hline")
        lines.append(r"Parameter & " + method + r" & Planck 2018 & Tension ($\sigma$) \\")
    else:
        lines.append(r"\begin{tabular}{lcc}")
        lines.append(r"\hline\hline")
        lines.append(r"Parameter & Value & Uncertainty \\")

    lines.append(r"\hline")

    for i, name in enumerate(param_names):
        val = values[i]
        unc = uncertainties[i]
        val_str = f"${val:.4f} \\pm {unc:.4f}$"

        if reference and name in reference:
            ref_val = reference[name]
            tension = abs(val - ref_val) / (unc + 1e-10)
            lines.append(
                f"{name} & {val_str} & ${ref_val:.4f}$ & ${tension:.1f}\\sigma$ \\\\")
        else:
            lines.append(f"{name} & ${val:.4f}$ & ${unc:.4f}$ \\\\")

    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    return "\n".join(lines)


def comparison_to_latex(
    methods: dict[str, tuple[np.ndarray, np.ndarray]],
    param_names: list[str],
    caption: str = "Method comparison",
    label: str = "tab:comparison",
) -> str:
    """Generate multi-method comparison LaTeX table."""
    method_names = list(methods.keys())
    n_methods = len(method_names)

    header_cols = " & ".join([f"\\textbf{{{m}}}" for m in method_names])
    lines = [
        r"\begin{table*}",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        r"\begin{tabular}{l" + "c" * n_methods + "}",
        r"\hline\hline",
        f"Parameter & {header_cols} \\\\",
        r"\hline",
    ]

    for i, name in enumerate(param_names):
        cells = []
        for m in method_names:
            val, unc = methods[m]
            cells.append(f"${val[i]:.4f} \\pm {unc[i]:.4f}$")
        lines.append(f"{name} & {' & '.join(cells)} \\\\")

    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table*}")

    return "\n".join(lines)
