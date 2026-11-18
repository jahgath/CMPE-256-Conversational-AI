"""Economic indicator calculations. All functions are pure and return plain dicts
so they can be used both by the LLM tool layer and by tests."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .fred import load, SERIES


def _window(s: pd.Series, years: float | None) -> pd.Series:
    if not years:
        return s
    return s[s.index >= s.index[-1] - pd.DateOffset(months=int(round(years * 12)))]


def _d(ts) -> str:
    return pd.Timestamp(ts).strftime("%Y-%m-%d")


def quarter_label(ts) -> str:
    t = pd.Timestamp(ts)
    return f"{t.year} Q{(t.month - 1) // 3 + 1}"


def gdp_growth() -> pd.DataFrame:
    """Quarterly GDP: QoQ annualized %, YoY %."""
    g = load("GDP")
    return pd.DataFrame({
        "level": g,
        "qoq_annualized": ((g / g.shift(1)) ** 4 - 1) * 100,
        "yoy": g.pct_change(4) * 100,
    })


def cpi_inflation() -> pd.DataFrame:
    """Monthly Core CPI: MoM %, YoY %, 3-month annualized %."""
    c = load("CPILFESL")
    return pd.DataFrame({
        "level": c,
        "mom": c.pct_change() * 100,
        "yoy": c.pct_change(12) * 100,
        "ann3m": ((c / c.shift(3)) ** 4 - 1) * 100,
    })


def latest(series_id: str) -> dict:
    sid = series_id.upper()
    if sid == "GDP":
        df = gdp_growth().dropna(subset=["yoy"])
        r = df.iloc[-1]
        return {"series": "GDP", "period": quarter_label(df.index[-1]), "date": _d(df.index[-1]),
                "value_billions_usd": round(r.level, 1), "units": SERIES["GDP"]["units"],
                "qoq_annualized_pct": round(r.qoq_annualized, 2), "yoy_pct": round(r.yoy, 2)}
    df = cpi_inflation().dropna(subset=["yoy"])
    r = df.iloc[-1]
    return {"series": "CPILFESL", "period": pd.Timestamp(df.index[-1]).strftime("%B %Y"), "date": _d(df.index[-1]),
            "index_value": round(r.level, 3), "units": SERIES["CPILFESL"]["units"],
            "yoy_inflation_pct": round(r.yoy, 2), "mom_pct": round(r.mom, 2),
            "annualized_3m_pct": round(r.ann3m, 2)}


def history(series_id: str, years: float = 10) -> dict:
    sid = series_id.upper()
    if sid == "GDP":
        df = _window(gdp_growth()["level"], years).to_frame()
        df["yoy"] = gdp_growth()["yoy"].reindex(df.index)
        first, last = df.iloc[0], df.iloc[-1]
        n = (df.index[-1] - df.index[0]).days / 365.25
        out = {"series": "GDP", "start": quarter_label(df.index[0]), "end": quarter_label(df.index[-1]),
               "start_value": round(first.level, 1), "end_value": round(last.level, 1),
               "total_change_pct": round((last.level / first.level - 1) * 100, 1),
               "cagr_pct": round(((last.level / first.level) ** (1 / n) - 1) * 100, 2),
               "avg_yoy_growth_pct": round(df.yoy.mean(), 2),
               "peak_yoy": {"period": quarter_label(df.yoy.idxmax()), "pct": round(df.yoy.max(), 2)},
               "trough_yoy": {"period": quarter_label(df.yoy.idxmin()), "pct": round(df.yoy.min(), 2)}}
        out["yearly_samples"] = {quarter_label(i): round(v, 1) for i, v in df.level.iloc[::4].items()}
        return out
    cdf = cpi_inflation()
    df = _window(cdf["yoy"].dropna(), years).to_frame("yoy")
    lv = _window(cdf["level"], years)
    return {"series": "CPILFESL", "start": lv.index[0].strftime("%b %Y"), "end": lv.index[-1].strftime("%b %Y"),
            "index_start": round(lv.iloc[0], 2), "index_end": round(lv.iloc[-1], 2),
            "total_price_change_pct": round((lv.iloc[-1] / lv.iloc[0] - 1) * 100, 1),
            "avg_yoy_inflation_pct": round(df.yoy.mean(), 2),
            "peak_yoy": {"period": df.yoy.idxmax().strftime("%b %Y"), "pct": round(df.yoy.max(), 2)},
            "trough_yoy": {"period": df.yoy.idxmin().strftime("%b %Y"), "pct": round(df.yoy.min(), 2)},
            "latest_yoy_pct": round(df.yoy.iloc[-1], 2),
            "yoy_by_year_end": {str(i.year): round(v, 2) for i, v in df.yoy.items() if i.month == 12 or i == df.index[-1]}}


def combined(years: float | None = None) -> pd.DataFrame:
    """Quarterly frame aligning GDP YoY growth with Core CPI YoY (quarter-end-month average)."""
    g = gdp_growth()["yoy"]
    c = cpi_inflation()["yoy"].dropna()
    cq = c.resample("QS").mean()          # quarterly mean, labelled at quarter start = FRED GDP dating
    df = pd.concat({"gdp_yoy": g, "cpi_yoy": cq}, axis=1).dropna()
    return _window(df, years) if years else df


def relationship(years: float = 20) -> dict:
    df = combined(years)
    corr0 = df.gdp_yoy.corr(df.cpi_yoy)
    lags = {k: round(df.gdp_yoy.corr(df.cpi_yoy.shift(-k)), 3) for k in (0, 2, 4, 8)}  # GDP leads CPI by k qtrs
    ex = df[(df.index < "2020-01-01") | (df.index > "2021-12-31")]
    return {"window": f"{quarter_label(df.index[0])} to {quarter_label(df.index[-1])}", "n_quarters": len(df),
            "correlation_gdp_vs_cpi_yoy": round(corr0, 3),
            "correlation_excluding_2020_2021": round(ex.gdp_yoy.corr(ex.cpi_yoy), 3),
            "gdp_leads_cpi_correlations_by_quarters": lags,
            "avg_gdp_yoy_pct": round(df.gdp_yoy.mean(), 2), "avg_cpi_yoy_pct": round(df.cpi_yoy.mean(), 2),
            "latest": {"gdp_yoy_pct": round(df.gdp_yoy.iloc[-1], 2), "cpi_yoy_pct": round(df.cpi_yoy.iloc[-1], 2)},
            "note": "Correlation is not causation; 2020-21 pandemic distortions strongly affect the full-window figure."}


def trends() -> dict:
    out = {}
    g = gdp_growth().dropna(subset=["yoy"])
    c = cpi_inflation().dropna(subset=["yoy"])
    out["gdp"] = {"latest": latest("GDP"), "yoy_pct_5y_ago": round(g.yoy.iloc[-21], 2),
                  "avg_yoy_last_5y": round(g.yoy.iloc[-20:].mean(), 2),
                  "avg_yoy_2010_2019": round(g.loc["2010":"2019"].yoy.mean(), 2),
                  "pandemic_trough": {"period": quarter_label(g.loc["2020"].yoy.idxmin()), "yoy": round(g.loc["2020"].yoy.min(), 2)}}
    pk = c.loc["2021":].yoy.idxmax()
    out["core_cpi"] = {"latest": latest("CPILFESL"), "peak_since_2021": {"month": pk.strftime("%b %Y"), "yoy": round(c.yoy[pk], 2)},
                       "avg_yoy_2010_2019": round(c.loc["2010":"2019"].yoy.mean(), 2),
                       "yoy_12m_ago": round(c.yoy.iloc[-13], 2),
                       "direction_last_12m": "falling" if c.yoy.iloc[-1] < c.yoy.iloc[-13] - 0.15 else "rising" if c.yoy.iloc[-1] > c.yoy.iloc[-13] + 0.15 else "roughly flat"}
    out["relationship"] = relationship(20)
    return out
