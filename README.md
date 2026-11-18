# Conversational AI for FRED GDP & Core CPI

Chat in natural language with two FRED series: **GDP** and **CPILFESL** (Core CPI).
Latest/historical values, growth & inflation rates, trends, GDP-vs-CPI relationship, charts.

## Run
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...      # optional: enables the Claude LLM agent
.venv/bin/streamlit run app.py           # web chat UI
.venv/bin/python cli.py                  # terminal chat
.venv/bin/python -m pytest               # tests
```
No FRED API key is needed (public CSV endpoint; cached in `data/`). Without `ANTHROPIC_API_KEY` the app runs an
offline keyword router over the same tools (all seven required questions work). Model override: `ECON_CHAT_MODEL`.

## Layout
- `econ_chat/fred.py` data fetch + cache · `analytics.py` indicators · `charts.py` matplotlib · `tools.py` Claude tool schemas · `agent.py` tool-use loop
- `docs/architecture.png`, `docs/sample_conversations.md`, `docs/REPORT.md` · `outputs/*.png` visualizations
