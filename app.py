"""Streamlit portfolio analysis using daily adjusted prices and shared analytics."""

from datetime import date, timedelta
from math import isfinite

import numpy as np
import plotly.express as px
import streamlit as st

from risklens.analytics import (
    annualized_return,
    annualized_volatility,
    max_drawdown,
    portfolio_returns,
    sharpe_ratio,
)
from risklens.data import DataFetchError, fetch_prices, to_returns
from risklens.validation import validate_tickers, validate_weights


st.set_page_config(page_title="RiskLens Quant", page_icon="◈", layout="wide")

with st.sidebar:
    st.title("◈ RiskLens")
    st.caption("QUANT · PORTFOLIO ANALYTICS")
    st.divider()
    raw_tickers = st.text_input(
        "Stock tickers", "AAPL, MSFT",
        help="Separate tickers with commas or spaces; maximum 25.",
    )
    try:
        tickers = validate_tickers(raw_tickers)
    except ValueError as exc:
        tickers = []
        st.error(str(exc))

    with st.form("portfolio_request"):
        st.markdown("**Portfolio weights**")
        st.caption("Long-only allocation: percentages must total 100%.")
        weights_pct = []
        for index, ticker in enumerate(tickers):
            equal_weight = round(100 / len(tickers), 2)
            default_weight = (
                100 - equal_weight * index
                if index == len(tickers) - 1 else equal_weight
            )
            weights_pct.append(st.number_input(
                f"{ticker} weight (%)", min_value=0.0, max_value=100.0,
                value=default_weight, step=1.0, format="%.2f",
                key=f"weight:{','.join(tickers)}:{ticker}",
            ))
        today = date.today()
        start = st.date_input(
            "Start date", today - timedelta(days=365),
            min_value=date(1900, 1, 1), max_value=today,
        )
        end = st.date_input(
            "End date (inclusive)", today,
            min_value=date(1900, 1, 1), max_value=today,
        )
        submitted = st.form_submit_button("Analyze portfolio", disabled=not tickers)

st.caption("PORTFOLIO INTELLIGENCE / OVERVIEW")
st.title("RiskLens Quant")
st.markdown("Explore your portfolio’s historical returns and risk.")

analysis = st.session_state.get("analysis")
if analysis is not None and list(analysis["prices"].columns) != tickers:
    st.session_state.pop("analysis", None)

if submitted:
    st.session_state.pop("analysis", None)
    try:
        try:
            weights = validate_weights([value / 100 for value in weights_pct], len(tickers))
        except ValueError as exc:
            raise ValueError(
                f"Use non-negative weights totaling 100%. Current total: {sum(weights_pct):.2f}%."
            ) from exc
        if start >= end:
            raise ValueError("Start date must be before end date.")
        with st.spinner("Loading prices and calculating portfolio metrics…"):
            # Yahoo's end date is exclusive; the UI includes the selected day.
            prices = fetch_prices(tickers, start, end + timedelta(days=1))
            if not np.isfinite(prices.to_numpy()).all() or (prices <= 0).to_numpy().any():
                raise ValueError("Price history contains invalid prices. Try another ticker or period.")
            returns = to_returns(prices)
            if len(returns) < 2:
                raise ValueError("Choose a longer period: at least three overlapping price dates are needed.")
            daily_returns = portfolio_returns(returns, weights)
            metrics = (
                annualized_return(daily_returns),
                annualized_volatility(daily_returns),
                sharpe_ratio(daily_returns),
                max_drawdown(daily_returns),
            )
            if not all(isfinite(value) for value in (metrics[0], metrics[1], metrics[3])):
                raise ValueError("These prices could not produce finite metrics. Try a different period.")
            st.session_state["analysis"] = {
                "prices": prices, "weights": weights, "metrics": metrics,
            }
    except (ValueError, DataFetchError) as exc:
        st.error(f"Unable to analyze this portfolio. {exc}")

analysis = st.session_state.get("analysis")
if analysis is None:
    if not submitted:
        st.info("Choose tickers, set weights totaling 100%, and select Analyze portfolio.")
else:
    prices = analysis["prices"]
    st.subheader("Portfolio snapshot")
    allocation = " · ".join(
        f"{ticker} {weight:.2%}"
        for ticker, weight in zip(prices.columns, analysis["weights"])
    )
    st.caption(
        f"{allocation} | {prices.index.min():%b %d, %Y} – "
        f"{prices.index.max():%b %d, %Y} | {len(prices):,} price observations"
    )
    descriptions = (
        ("Annualized return", "Mean daily portfolio return × 252; arithmetic annualization.", ".2%"),
        ("Annualized volatility", "Sample daily standard deviation × √252.", ".2%"),
        ("Sharpe ratio", "Annualized excess return / volatility. Assumes a 0% annual risk-free rate.", ".2f"),
        ("Maximum drawdown", "Worst peak-to-trough decline, including initial wealth; negative means loss.", ".2%"),
    )
    for column, (label, help_text, spec), value in zip(
        st.columns(4), descriptions, analysis["metrics"],
    ):
        with column.container(border=True):
            st.metric(label, format(value, spec) if isfinite(value) else "N/A", help=help_text)
    if not isfinite(analysis["metrics"][2]):
        st.caption("Sharpe ratio is unavailable because portfolio volatility is zero or too close to zero.")
    st.caption("Fixed weights, rebalanced daily. Annualized figures use 252 trading days.")

    st.divider()
    st.subheader("Historical prices")
    fig = px.line(prices, labels={"index": "Date", "value": "Adjusted closing price", "variable": "Ticker"})
    # TODO(human): Add the 12 optional chart-formatting lines here (four spaces).
    st.plotly_chart(fig)
    st.caption("Daily adjusted closing prices. Use tickers quoted in the same currency; no currency conversion is applied.")

st.divider()
st.caption(
    "Disclaimer: For educational and informational purposes only. "
    "This is not investment advice or a recommendation to buy or sell securities. "
    "Past performance does not guarantee future results. "
    "Historical estimates may understate future losses."
)
