# Technical Report: Conversational AI for FRED GDP and Core CPI

## 1. Overview
A chat application that answers natural-language questions about U.S. GDP (FRED `GDP`, quarterly, nominal, SAAR, $B)
and Core CPI (`CPILFESL`, monthly index, 1982-84=100, SA). Data vintage in this report: GDP through 2026 Q3, Core CPI through October 2026.

## 2. Architecture (see `architecture.png`)
1. **UI** – Streamlit chat (`app.py`) and CLI (`cli.py`); charts render inline.
2. **Agent** – Claude with tool use. The system prompt forces the model to fetch every number through tools (no recalled figures), cite period labels, and flag that GDP is nominal. A loop of up to 8 tool rounds runs until the model gives a final answer. With no API key, a deterministic keyword router calls the same tools.
3. **Tools** – `get_latest`, `get_history`, `get_relationship`, `make_chart`, `summarize_trends`. Errors are returned to the model as data so it can recover.
4. **Analytics** – pandas: QoQ annualized and YoY GDP growth; MoM, YoY and 3-month-annualized Core CPI; CAGR; peaks/troughs; correlation and lead/lag.
5. **Data** – FRED public CSV, cached on disk (6 h TTL, falls back to stale cache offline).

Design choice: the LLM does language understanding and explanation; all arithmetic is deterministic code, which keeps figures reproducible and testable.

## 3. Method for comparing GDP and CPI
Monthly Core CPI YoY is averaged to quarters and aligned with quarterly GDP YoY (81 overlapping quarters, 2006 Q3-2026 Q3). Lags of 0/2/4/8 quarters (GDP leading CPI) are tested. Because GDP is nominal it contains price effects, so the correlation is partly mechanical.

## 4. Findings (live data)
- **GDP:** $33.01T in 2026 Q3, +5.87% YoY (5.61% annualized QoQ). Over 10 years GDP grew +74.7% (5.74%/yr), with a -6.73% YoY trough in 2020 Q2 and a +17.5% peak in 2021 Q2; 2010-19 averaged 4.06% YoY.
- **Core CPI:** 2.87% YoY in Oct 2026 (0.3% MoM; 3-month annualized 3.75%). Over five years prices rose 20.7%; YoY peaked at 6.62% (Sep 2022), fell to 2.67% (Mar 2026), and has since drifted slightly up. Still above the 1.85% 2010-19 average.
- **Relationship:** correlation 0.65 (0.68 excluding 2020-21); strongest (0.72) when GDP leads CPI by two quarters; weak at 8 quarters (0.18). Consistent with demand-driven inflation (growth leads prices) but not proof of causation.
- **Narrative:** pre-2020 steady growth with inflation near/below 2% → pandemic collapse and rebound → 2021-22 inflation surge → disinflation to ~3% with growth still above trend.

## 5. Limitations
- Nominal, not real, GDP; real GDP (`GDPC1`) would isolate output growth.
- Correlation over a window dominated by the pandemic; no causal model.
- Offline router handles the supported question types only; open-ended questions need the LLM.
- The latest GDP quarter is an initial estimate that FRED may revise.
- The LLM path needs `ANTHROPIC_API_KEY`; it was not exercised in this build environment (no key available), only the tool layer and offline path were run and tested.

## 6. Testing
`pytest` unit tests verify growth/inflation math against synthetic series. The seven required questions were run end-to-end (`sample_conversations.md`).
