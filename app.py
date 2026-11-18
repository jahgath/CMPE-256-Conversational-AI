"""Streamlit chat UI:  streamlit run app.py"""
import streamlit as st
from econ_chat.agent import Agent

st.set_page_config(page_title="FRED Economy Chat", page_icon="📈")
st.title("📈 Chat with U.S. GDP & Core CPI")
if "agent" not in st.session_state:
    st.session_state.agent, st.session_state.log = Agent(), []
a = st.session_state.agent
st.caption(f"Data: FRED GDP & CPILFESL · Mode: {a.mode}")
with st.sidebar:
    st.subheader("Try asking")
    ex = ["What is the latest reported U.S. GDP?", "How has U.S. GDP changed over the past 10 years?",
          "What is the current Core CPI inflation rate?", "How has Core CPI inflation changed over the past five years?",
          "What is the relationship between GDP growth and Core CPI inflation?",
          "Generate a visualization comparing GDP growth and Core CPI inflation over time.",
          "Summarize the key economic trends observed in both datasets."]
    picked = [q for q in ex if st.button(q)]
for role, text, imgs in st.session_state.log:
    with st.chat_message(role):
        st.markdown(text)
        for i in imgs: st.image(i)
q = (picked[0] if picked else None) or st.chat_input("Ask about GDP or Core CPI…")
if q:
    st.session_state.log.append(("user", q, []))
    with st.chat_message("user"): st.markdown(q)
    n = len(a.charts)
    with st.chat_message("assistant"), st.spinner("Analyzing FRED data…"):
        ans = a.ask(q); new = a.charts[n:]
        st.markdown(ans)
        for i in new: st.image(i)
    st.session_state.log.append(("assistant", ans, new))
