"""Matplotlib visualizations saved as PNGs under outputs/."""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from . import analytics as A

OUT = Path(__file__).resolve().parent.parent / "outputs"
C_GDP, C_CPI = "#1f77b4", "#d95f02"
KINDS = ["comparison", "gdp_level", "cpi_inflation", "scatter"]


def _style(ax, title, ylabel):
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.grid(alpha=.25)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def make_chart(kind: str = "comparison", years: float = 20) -> str:
    OUT.mkdir(exist_ok=True)
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    fig, ax = plt.subplots(figsize=(10, 5), dpi=130)
    src = "Source: FRED (GDP, CPILFESL)"
    if kind == "comparison":
        df = A.combined(years)
        ax.plot(df.index, df.gdp_yoy, color=C_GDP, lw=2, label="GDP growth (YoY %, nominal)")
        ax.plot(df.index, df.cpi_yoy, color=C_CPI, lw=2, label="Core CPI inflation (YoY %)")
        ax.axhline(0, color="k", lw=.6)
        ax.axhline(2, color=C_CPI, lw=.8, ls=":", alpha=.7)
        ax.text(df.index[0], 2.2, "2% target", color=C_CPI, fontsize=8)
        _style(ax, "GDP growth vs. Core CPI inflation", "% change, year over year")
        ax.legend(frameon=False)
    elif kind == "gdp_level":
        g = A.gdp_growth()
        g = g[g.index >= g.index[-1] - __import__("pandas").DateOffset(years=int(years))]
        ax.plot(g.index, g.level / 1000, color=C_GDP, lw=2)
        _style(ax, "U.S. GDP (nominal, SAAR)", "Trillions of USD")
    elif kind == "cpi_inflation":
        c = A.cpi_inflation().dropna(subset=["yoy"])
        c = c[c.index >= c.index[-1] - __import__("pandas").DateOffset(years=int(years))]
        ax.plot(c.index, c.yoy, color=C_CPI, lw=2, label="YoY %")
        ax.plot(c.index, c.ann3m, color=C_CPI, lw=1, alpha=.45, label="3-month annualized %")
        ax.axhline(2, color="k", lw=.8, ls=":")
        _style(ax, "Core CPI inflation", "%")
        ax.legend(frameon=False)
    else:  # scatter
        df = A.combined(years)
        sc = ax.scatter(df.cpi_yoy, df.gdp_yoy, c=range(len(df)), cmap="viridis", s=28)
        fig.colorbar(sc, ax=ax, label="time →  (older to newer)")
        _style(ax, f"GDP growth vs Core CPI (r = {df.gdp_yoy.corr(df.cpi_yoy):.2f})", "GDP growth YoY %")
        ax.set_xlabel("Core CPI inflation YoY %")
    fig.text(0.01, 0.01, src, fontsize=7, color="gray")
    fig.tight_layout(rect=(0, .03, 1, 1))
    path = OUT / f"{kind}_{int(years)}y.png"
    fig.savefig(path)
    plt.close(fig)
    return str(path)
