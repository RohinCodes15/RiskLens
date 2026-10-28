"""RiskLens Quant dashboard shell; no portfolio metrics are calculated yet."""

import streamlit as st


st.set_page_config(page_title="RiskLens Quant", page_icon="◈", layout="wide")

with st.sidebar:
    st.title("◈ RiskLens")
    st.caption("QUANT · PORTFOLIO ANALYTICS")
    st.divider()
    st.info("Preview mode · No market data loaded")
    # TODO(human): Insert the 12 sidebar UI lines here, indented four spaces.

st.caption("PORTFOLIO INTELLIGENCE / OVERVIEW")
st.title("RiskLens Quant")
st.markdown(
    "### See the risk behind your returns.\n"
    "Explore portfolio volatility, downside exposure, and historical performance "
    "in one focused workspace."
)
st.info("Dashboard preview — all metrics are placeholders, not calculated results.")

st.subheader("Portfolio snapshot")
for column, label, help_text in zip(
    st.columns(4),
    ("Annualized return", "Annualized volatility", "Historical VaR", "Maximum drawdown"),
    (
        "Annualized portfolio growth, expressed as a percent when calculated.",
        "Annualized dispersion of daily returns, expressed as a percent.",
        "Daily loss threshold; confidence and sign convention will accompany results.",
        "Largest historical peak-to-trough decline, expressed as a percent.",
    ),
):
    column.metric(label, "—", help=help_text)

st.divider()
overview, methodology = st.columns([2, 1])
with overview:
    st.subheader("Your portfolio, in perspective")
    with st.container(border=True):
        st.markdown("**Performance & drawdown**")
        st.caption("Historical charts will appear here once portfolio analysis is connected.")
        st.write("No portfolio has been analyzed yet.")
with methodology:
    st.subheader("How it will work")
    st.markdown(
        "1. Choose tickers and portfolio weights.\n"
        "2. Select a historical analysis period.\n"
        "3. Review returns and risk together."
    )

st.divider()
st.caption(
    "Disclaimer: For educational and informational purposes only. "
    "This is not investment advice or a recommendation to buy or sell securities. "
    "Past performance does not guarantee future results. "
    "Historical estimates may understate future losses."
)
