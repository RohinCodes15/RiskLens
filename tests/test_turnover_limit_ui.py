"""Dashboard optimization with a turnover limit: inputs, calls, table row, and caption."""

from unittest.mock import patch

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest
from test_risk_ui import analyzed_app, make_prices
from test_smoke import click_button

from risklens.analytics import (
    efficient_frontier,
    max_sharpe_portfolio,
    min_volatility_portfolio,
    one_way_turnover,
)

LABEL = "Turnover limit (% of portfolio)"


def optimize(prices: pd.DataFrame, limit_pct: float | None = None) -> AppTest:
    app = analyzed_app(prices)
    if limit_pct is not None:
        next(n for n in app.number_input if n.label == LABEL).set_value(limit_pct)
    return click_button(app, "Optimize portfolio")


def test_default_runs_without_a_limit() -> None:
    prices = make_prices()
    with (
        patch("risklens.analytics.min_volatility_portfolio", wraps=min_volatility_portfolio) as mv,
        patch("risklens.analytics.efficient_frontier", wraps=efficient_frontier) as frontier,
    ):
        app = optimize(prices)
    assert not app.exception and not app.error
    assert mv.call_args.kwargs == {}
    assert frontier.call_args.kwargs["min_volatility"] is not None
    table = app.dataframe[0].value
    assert table.loc["Turnover from current", "Current"] == 0.0
    weights = app.session_state["analysis"]["weights"]
    assert table.loc["Turnover from current", "Minimum volatility"] == (
        one_way_turnover(weights, table["Minimum volatility"].iloc[:3])
    )
    assert not any("one-way turnover" in caption.value for caption in app.caption)


def test_limit_reaches_both_optimizers_and_the_table() -> None:
    prices = make_prices()
    with patch("risklens.analytics.efficient_frontier", wraps=efficient_frontier) as frontier:
        app = optimize(prices, 10.0)
    assert not app.exception and not app.error
    weights = app.session_state["analysis"]["weights"]
    table = app.dataframe[0].value
    for column, optimizer in (
        ("Minimum volatility", min_volatility_portfolio),
        ("Maximum Sharpe", max_sharpe_portfolio),
    ):
        expected = optimizer(prices, current_weights=weights, max_turnover=0.1)
        np.testing.assert_allclose(table[column].iloc[:3], expected.weights, atol=1e-6)
        assert table.loc["Turnover from current", column] <= 0.1 + 1e-6
    assert frontier.call_args.kwargs["min_volatility"] is None  # frontier stays unlimited
    assert any("limited to 10% one-way turnover" in c.value for c in app.caption)


def test_zero_limit_keeps_the_current_weights() -> None:
    app = optimize(make_prices(), 0.0)
    assert not app.exception
    table = app.dataframe[0].value
    np.testing.assert_allclose(
        table["Minimum volatility"].iloc[:3], table["Current"].iloc[:3], atol=1e-6
    )
