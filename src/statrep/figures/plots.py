"""Figure functions for the four M1 analysis blocks (descriptives,
comparisons, correlation, regression). Migrated and cleaned up from
`statistical-analysis/SKILL.md`'s inline plot functions (`plot_distribution`
was referenced there but never defined — added here to fill that gap).

Every function saves a 300dpi PNG to ``save_path`` and returns the path.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import seaborn as sns

from .style import PALETTE, init_figure, significance_star


def _finish(fig, save_path: str | Path) -> Path:
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    sns.despine(fig=fig)
    fig.tight_layout()
    fig.savefig(save_path)
    import matplotlib.pyplot as plt

    plt.close(fig)
    return save_path


def plot_distribution(
    values: pd.Series,
    title: str,
    save_path: str | Path,
    figsize: tuple[float, float] = (8, 5),
) -> Path:
    """Histogram + KDE for a single continuous variable, used in the
    descriptives block."""
    fig, ax = init_figure(figsize)
    sns.histplot(values.dropna(), kde=True, color=PALETTE["primary"], ax=ax)
    ax.axvline(values.mean(), color=PALETTE["positive"], linestyle="--", linewidth=1.2, label="M")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel(values.name or "")
    ax.legend(frameon=False)
    return _finish(fig, save_path)


def plot_group_comparison(
    means: list[list[float]],
    sds: list[list[float]],
    group_labels: list[str],
    dv_labels: list[str],
    title: str,
    save_path: str | Path,
    p_values: list[float] | None = None,
    figsize: tuple[float, float] = (10, 6),
) -> Path:
    """Grouped bar chart with error bars and significance stars, used for
    two-group comparisons (t-test / Mann-Whitney)."""
    fig, ax = init_figure(figsize)
    x = np.arange(len(dv_labels))
    width = 0.35
    ax.bar(x - width / 2, means[0], width, yerr=sds[0], capsize=4,
           color=PALETTE["primary"], alpha=0.85, label=group_labels[0])
    ax.bar(x + width / 2, means[1], width, yerr=sds[1], capsize=4,
           color=PALETTE["secondary"], alpha=0.85, label=group_labels[1])
    if p_values is not None:
        for i, p in enumerate(p_values):
            star = significance_star(p) or "ns"
            max_y = max(means[0][i] + sds[0][i], means[1][i] + sds[1][i])
            ax.text(x[i], max_y * 1.05, star, ha="center", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(dv_labels, rotation=15, ha="right")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.legend(frameon=False)
    return _finish(fig, save_path)


def plot_anova_boxplot(
    df: pd.DataFrame,
    group_var: str,
    dv_vars: list[str],
    title: str,
    save_path: str | Path,
    figsize: tuple[float, float] = (14, 8),
) -> Path:
    """Grid of grouped box plots, one per dependent variable — used for
    one-way ANOVA / Kruskal-Wallis comparisons across 3+ groups."""
    import matplotlib.pyplot as plt

    n_vars = len(dv_vars)
    cols = min(3, n_vars)
    rows = (n_vars + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=figsize, squeeze=False)
    axes = axes.flatten()
    palette = sns.color_palette("Set2", df[group_var].nunique())
    i = 0
    for i, dv in enumerate(dv_vars):
        sns.boxplot(data=df, x=group_var, y=dv, hue=group_var, palette=palette,
                    legend=False, ax=axes[i])
        axes[i].set_title(dv, fontweight="bold")
    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)
    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.02)
    return _finish(fig, save_path)


def plot_correlation_heatmap(
    corr_matrix: pd.DataFrame,
    p_matrix: pd.DataFrame,
    title: str,
    save_path: str | Path,
    figsize: tuple[float, float] = (12, 10),
) -> Path:
    """Lower-triangle correlation heatmap with significance stars."""
    fig, ax = init_figure(figsize)
    annot = corr_matrix.round(2).astype(str)
    for i in range(len(corr_matrix)):
        for j in range(len(corr_matrix.columns)):
            p = p_matrix.iloc[i, j]
            r = corr_matrix.iloc[i, j]
            star = significance_star(p) if pd.notna(p) else ""
            annot.iloc[i, j] = f"{r:.2f}{star}"
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    sns.heatmap(corr_matrix, mask=mask, annot=annot, fmt="", cmap="RdBu_r",
                center=0, vmin=-1, vmax=1, square=True, linewidths=0.5, ax=ax)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    fig.tight_layout()
    fig.savefig(save_path, dpi=300, bbox_inches="tight")
    import matplotlib.pyplot as plt

    plt.close(fig)
    return Path(save_path)


def plot_regression_coefficients(
    names: list[str],
    betas: list[float],
    ci_lower: list[float],
    ci_upper: list[float],
    title: str,
    save_path: str | Path,
    figsize: tuple[float, float] = (8, 6),
) -> Path:
    """Standardized regression coefficient forest plot with 95% CI."""
    fig, ax = init_figure(figsize)
    y_pos = np.arange(len(names))
    colors = [PALETTE["positive"] if b > 0 else PALETTE["negative"] for b in betas]
    ax.barh(y_pos, betas, color=colors, alpha=0.7, height=0.6)
    ax.errorbar(
        betas, y_pos,
        xerr=[np.array(betas) - np.array(ci_lower), np.array(ci_upper) - np.array(betas)],
        fmt="none", color="black", capsize=3, linewidth=1.2,
    )
    ax.axvline(x=0, color="gray", linestyle="--", linewidth=0.8)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.set_xlabel("Standardized Regression Coefficient (β)")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    return _finish(fig, save_path)


__all__ = [
    "plot_distribution",
    "plot_group_comparison",
    "plot_anova_boxplot",
    "plot_correlation_heatmap",
    "plot_regression_coefficients",
]
