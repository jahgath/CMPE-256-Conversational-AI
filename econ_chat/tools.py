"""Tool layer: JSON-schema definitions for Claude + dispatcher."""
from __future__ import annotations
import json
from . import analytics as A, charts

TOOLS = [
    {"name": "get_latest", "description": "Latest observation for a series with growth/inflation rates. GDP: level, QoQ annualized and YoY growth. CPILFESL: index, YoY inflation, MoM, 3-month annualized.",
     "input_schema": {"type": "object", "properties": {"series": {"type": "string", "enum": ["GDP", "CPILFESL"]}}, "required": ["series"]}},
    {"name": "get_history", "description": "Summary of how a series changed over the past N years (start/end, total change, CAGR or avg inflation, peaks, troughs, yearly samples).",
     "input_schema": {"type": "object", "properties": {"series": {"type": "string", "enum": ["GDP", "CPILFESL"]}, "years": {"type": "number", "description": "lookback in years (default 10)"}}, "required": ["series"]}},
    {"name": "get_relationship", "description": "Statistical relationship (correlation, lead/lag, averages) between GDP YoY growth and Core CPI YoY inflation.",
     "input_schema": {"type": "object", "properties": {"years": {"type": "number", "description": "lookback window, default 20"}}}},
    {"name": "make_chart", "description": "Create a PNG visualization. kinds: comparison (GDP growth vs core CPI over time), gdp_level, cpi_inflation, scatter.",
     "input_schema": {"type": "object", "properties": {"kind": {"type": "string", "enum": charts.KINDS}, "years": {"type": "number"}}, "required": ["kind"]}},
    {"name": "summarize_trends", "description": "Bundle of key facts about both datasets (latest, pre-pandemic baselines, peaks, direction, relationship) for a trends summary.",
     "input_schema": {"type": "object", "properties": {}}},
]


def run_tool(name: str, args: dict) -> dict:
    try:
        if name == "get_latest":
            return A.latest(args["series"])
        if name == "get_history":
            return A.history(args["series"], args.get("years", 10))
        if name == "get_relationship":
            return A.relationship(args.get("years", 20))
        if name == "make_chart":
            return {"chart_path": charts.make_chart(args["kind"], args.get("years", 20))}
        if name == "summarize_trends":
            return A.trends()
        return {"error": f"unknown tool {name}"}
    except Exception as e:  # surfaced to the model so it can recover
        return {"error": f"{type(e).__name__}: {e}"}


def to_json(x) -> str:
    return json.dumps(x, default=str)
