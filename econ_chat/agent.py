"""Conversational agent. Claude (tool use) is the primary brain; if no ANTHROPIC_API_KEY
is available a deterministic rule-based router answers the same questions from the same tools."""
from __future__ import annotations
import os, re
from .tools import TOOLS, run_tool, to_json

MODEL = os.getenv("ECON_CHAT_MODEL", "claude-sonnet-5-5")
SYSTEM = """You are an economic-data analyst assistant for two FRED series:
- GDP: U.S. nominal Gross Domestic Product, quarterly, billions of USD, seasonally adjusted annual rate.
- CPILFESL: Core CPI (all items less food and energy), monthly index (1982-84=100), seasonally adjusted.
Rules: ALWAYS call tools to get numbers; never invent or recall figures from memory. Quote period labels
(e.g. '2026 Q3', 'October 2026') with each number. GDP is NOMINAL, so its growth includes inflation - say so
when comparing with CPI. Correlation is not causation; be calibrated. Charts: call make_chart and mention the
file path. Be concise (short paragraphs or bullets), explain what the metric means, and state data vintage."""


def _years(text: str, default: float) -> float:
    m = re.search(r"(\d+)\s*[- ]?(?:year|yr)", text) or re.search(r"\b(five|ten|three|twenty)\b", text)
    if not m:
        return default
    w = {"five": 5, "ten": 10, "three": 3, "twenty": 20}
    return float(w.get(m.group(1), m.group(1)))


class Agent:
    def __init__(self):
        self.messages: list[dict] = []
        self.charts: list[str] = []
        self.client = None
        if os.getenv("ANTHROPIC_API_KEY"):
            import anthropic
            self.client = anthropic.Anthropic()

    @property
    def mode(self) -> str:
        return f"Claude ({MODEL})" if self.client else "offline rule-based (set ANTHROPIC_API_KEY for the LLM)"

    def ask(self, text: str) -> str:
        return self._ask_llm(text) if self.client else self._ask_offline(text)

    # ---------- LLM path ----------
    def _ask_llm(self, text: str) -> str:
        self.messages.append({"role": "user", "content": text})
        for _ in range(8):
            r = self.client.messages.create(model=MODEL, max_tokens=1500, system=SYSTEM,
                                            tools=TOOLS, messages=self.messages)
            self.messages.append({"role": "assistant", "content": r.content})
            if r.stop_reason != "tool_use":
                return "".join(b.text for b in r.content if b.type == "text")
            results = []
            for b in r.content:
                if b.type == "tool_use":
                    out = run_tool(b.name, b.input)
                    if "chart_path" in out:
                        self.charts.append(out["chart_path"])
                    results.append({"type": "tool_result", "tool_use_id": b.id, "content": to_json(out)})
            self.messages.append({"role": "user", "content": results})
        return "Sorry, I could not finish that request."

    # ---------- offline path ----------
    def _ask_offline(self, text: str) -> str:
        t = text.lower()
        gdp, cpi = "gdp" in t or "output" in t, any(k in t for k in ("cpi", "inflation", "price"))
        if any(k in t for k in ("chart", "plot", "visual", "graph")):
            kind = "scatter" if "scatter" in t else "comparison" if (gdp and cpi) or "compar" in t else \
                   "gdp_level" if gdp else "cpi_inflation" if cpi else "comparison"
            p = run_tool("make_chart", {"kind": kind, "years": _years(t, 20)})["chart_path"]
            self.charts.append(p)
            return f"Here is the {kind.replace('_', ' ')} chart (saved to `{p}`). GDP growth is nominal (it includes inflation); note the 2020 shock and the 2021-22 inflation surge."
        if any(k in t for k in ("summar", "trend", "overview", "key")):
            return self._fmt_trends(run_tool("summarize_trends", {}))
        if any(k in t for k in ("relationship", "correlat", "compare", "versus", " vs")) or (gdp and cpi):
            return self._fmt_rel(run_tool("get_relationship", {"years": _years(t, 20)}))
        series = "GDP" if gdp else "CPILFESL" if cpi else None
        if series is None:
            return "I can discuss U.S. GDP and Core CPI (CPILFESL): latest values, history, relationship, charts, and trend summaries. Try 'What is the latest GDP?'"
        if any(k in t for k in ("past", "last", "over", "changed", "history", "since")):
            return self._fmt_hist(run_tool("get_history", {"series": series, "years": _years(t, 10 if series == "GDP" else 5)}))
        return self._fmt_latest(run_tool("get_latest", {"series": series}))

    @staticmethod
    def _fmt_latest(r):
        if r["series"] == "GDP":
            return (f"The latest reported U.S. GDP is **${r['value_billions_usd']:,.1f} billion** ({r['period']}, nominal, seasonally adjusted annual rate), "
                    f"≈ ${r['value_billions_usd']/1000:.2f} trillion. That is {r['qoq_annualized_pct']}% annualized growth vs the prior quarter and {r['yoy_pct']}% vs a year earlier.")
        return (f"Core CPI inflation is **{r['yoy_inflation_pct']}% year over year** ({r['period']}; index {r['index_value']}). "
                f"Month over month: {r['mom_pct']}%; 3-month annualized: {r['annualized_3m_pct']}%.")

    @staticmethod
    def _fmt_hist(r):
        if r["series"] == "GDP":
            return (f"From {r['start']} to {r['end']}, GDP rose from ${r['start_value']:,.0f}B to ${r['end_value']:,.0f}B (**+{r['total_change_pct']}%**, {r['cagr_pct']}%/yr CAGR). "
                    f"Average YoY growth was {r['avg_yoy_growth_pct']}%. Weakest: {r['trough_yoy']['period']} ({r['trough_yoy']['pct']}%); strongest: {r['peak_yoy']['period']} (+{r['peak_yoy']['pct']}%). "
                    "Note GDP here is nominal, so growth includes inflation.")
        yo = ", ".join(f"{k}: {v}%" for k, v in r["yoy_by_year_end"].items())
        return (f"From {r['start']} to {r['end']} core prices rose **{r['total_price_change_pct']}%** (index {r['index_start']} → {r['index_end']}). "
                f"YoY inflation peaked at {r['peak_yoy']['pct']}% ({r['peak_yoy']['period']}), bottomed at {r['trough_yoy']['pct']}% ({r['trough_yoy']['period']}), and is now {r['latest_yoy_pct']}%. YoY by year-end: {yo}.")

    @staticmethod
    def _fmt_rel(r):
        return (f"Over {r['window']} ({r['n_quarters']} quarters), YoY GDP growth and Core CPI inflation have a correlation of **{r['correlation_gdp_vs_cpi_yoy']}** "
                f"({r['correlation_excluding_2020_2021']} excluding 2020-21). Correlation with GDP leading CPI by 2 quarters is {r['gdp_leads_cpi_correlations_by_quarters'][2]}, the strongest lag tested. "
                f"Averages: GDP {r['avg_gdp_yoy_pct']}%, CPI {r['avg_cpi_yoy_pct']}%. Latest: GDP {r['latest']['gdp_yoy_pct']}%, CPI {r['latest']['cpi_yoy_pct']}%. "
                "Caveat: a positive link is consistent with demand-driven inflation, but nominal GDP mechanically includes prices, and correlation is not causation.")

    def _fmt_trends(self, r):
        g, c, rel = r["gdp"], r["core_cpi"], r["relationship"]
        return ("**Key trends**\n"
                f"- GDP: ${g['latest']['value_billions_usd']:,.0f}B in {g['latest']['period']}, {g['latest']['yoy_pct']}% YoY vs {g['avg_yoy_2010_2019']}% average in 2010-19; fell to {g['pandemic_trough']['yoy']}% YoY in {g['pandemic_trough']['period']}, then rebounded sharply.\n"
                f"- Core CPI: {c['latest']['yoy_inflation_pct']}% YoY ({c['latest']['period']}), down from a {c['peak_since_2021']['yoy']}% peak in {c['peak_since_2021']['month']}, but above the {c['avg_yoy_2010_2019']}% 2010-19 average; direction over the last 12 months: {c['direction_last_12m']}.\n"
                f"- Relationship: correlation {rel['correlation_gdp_vs_cpi_yoy']} over {rel['window']}; strongest when GDP leads CPI by ~2 quarters.")
