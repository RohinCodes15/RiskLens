"""Dashboard rebalancing and trading-cost controls reach every analysis."""

from collections.abc import Iterator
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from risklens.analytics import (
    analyze_portfolio,
    compare_to_benchmark,
    custom_scenario,
    stress_test,
)

APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")
WEIGHTS = [0.5, 0.5]


@pytest.fixture
def prices() -> pd.DataFrame:
    """Four months of prices for two stocks that drift apart, crossing month ends."""
    rng = np.random.default_rng(3)
    index = pd.bdate_range("2026-01-05", periods=80, name="Date")
    growth = np.cumprod(1 + rng.normal([0.002, -0.001], 0.015, (80, 2)), axis=0)
    return pd.DataFrame(100 * growth, index=index, columns=["AAPL", "MSFT"])


@pytest.fixture
def spy(prices: pd.DataFrame) -> pd.Series:
    return pd.Series(np.linspace(500.0, 520.0, len(prices)), index=prices.index, name="SPY")


@pytest.fixture(autouse=True)
def download(prices: pd.DataFrame, spy: pd.Series) -> Iterator[MagicMock]:
    """Serve SPY or the portfolio prices without touching Yahoo Finance."""

    def fake_download(tickers: list[str], **_: object) -> pd.DataFrame:
        frame = spy.to_frame() if list(tickers) == ["SPY"] else prices
        return pd.concat({"Close": frame}, axis=1)

    with patch("yfinance.download", side_effect=fake_download) as mock:
        yield mock


def widget(widgets: object, label: str) -> object:
    return next(item for item in widgets if item.label == label)


def analyze(rebalance: str | None = None, cost_bps: float | None = None) -> AppTest:
    """Submit the sidebar with optional rebalancing and cost choices."""
    app = AppTest.from_file(APP_PATH).run()
    if rebalance is not None:
        widget(app.selectbox, "Rebalancing").select(rebalance)
    if cost_bps is not None:
        widget(app.number_input, "Trading cost (bps)").set_value(cost_bps)
    app.date_input[0].set_value(date(2026, 1, 1))
    app.date_input[1].set_value(date(2026, 4, 30))
    return widget(app.button, "Analyze portfolio").click().run()


def card_values(app: AppTest) -> dict[str, str]:
    return {card.label: card.value for card in app.metric}


def test_controls_default_to_daily_rebalancing_without_costs() -> None:
    app = AppTest.from_file(APP_PATH).run()
    assert widget(app.selectbox, "Rebalancing").value == "Daily"
    assert widget(app.number_input, "Trading cost (bps)").value == 0.0
    assert widget(app.selectbox, "Rebalancing").options == [
        "Daily",
        "Monthly",
        "Quarterly",
        "Annually",
        "Never (buy and hold)",
    ]


def test_default_analysis_passes_daily_and_zero_cost(prices: pd.DataFrame) -> None:
    with patch("risklens.analytics.analyze_portfolio", wraps=analyze_portfolio) as engine:
        app = analyze()
    assert not app.exception and not app.error
    assert engine.call_args.kwargs == {"rebalance": "daily", "cost_bps": 0.0}
    assert any("Weights reset to target every trading day" in c.value for c in app.caption)
    assert any("Annual turnover:" in c.value for c in app.caption)


@pytest.mark.parametrize(
    ("label", "rebalance"),
    [
        ("Monthly", "monthly"),
        ("Quarterly", "quarterly"),
        ("Annually", "annual"),
        ("Never (buy and hold)", "never"),
    ],
)
def test_risk_cards_follow_the_chosen_rebalancing_and_cost(
    prices: pd.DataFrame, label: str, rebalance: str
) -> None:
    expected = analyze_portfolio(prices, WEIGHTS, rebalance=rebalance, cost_bps=10)
    app = analyze(label, 10.0)
    assert not app.exception and not app.error
    cards = card_values(app)
    assert cards["Annualized return"] == f"{expected.annualized_return:.2%}"
    assert cards["Annualized volatility"] == f"{expected.annualized_volatility:.2%}"
    assert cards["Maximum drawdown"] == f"{expected.max_drawdown:.2%}"
    turnover = f"Annual turnover: {expected.annual_turnover:.1%}"
    assert any(turnover in caption.value for caption in app.caption)
    assert any("10 bps trading cost" in caption.value for caption in app.caption)


def test_spy_comparison_uses_the_chosen_rebalancing_and_cost(
    prices: pd.DataFrame, spy: pd.Series
) -> None:
    curves = compare_to_benchmark(prices, WEIGHTS, spy, rebalance="quarterly", cost_bps=25)
    app = analyze("Quarterly", 25.0)
    assert not app.exception and not app.error
    expected = curves["portfolio"].iloc[-1] - 1.0
    assert card_values(app)["Portfolio ending return"] == f"{expected:.2%}"


def test_stress_replay_uses_the_chosen_rebalancing_and_cost(prices: pd.DataFrame) -> None:
    app = analyze("Monthly", 20.0)
    widget(app.selectbox, "Historical scenario").select("Custom date range").run()
    scenario = custom_scenario(prices.index[0], prices.index[-1])
    expected = stress_test(prices, WEIGHTS, scenario, "monthly", 20.0)
    widget(app.button, "Run historical stress test").click().run()
    assert not app.exception and not app.error
    assert card_values(app)["Scenario return"] == f"{expected.cumulative_return:.2%}"
    assert any(
        "reset to target each month; 20 bps trading cost" in caption.value
        for caption in app.caption
    )


def test_optimization_compares_with_a_daily_cost_free_current_portfolio(
    prices: pd.DataFrame,
) -> None:
    baseline = analyze_portfolio(prices, WEIGHTS)
    app = analyze("Annually", 30.0)
    widget(app.button, "Optimize portfolio").click().run()
    assert not app.exception and not app.error
    table = app.dataframe[0].value
    assert table.loc["Annualized return", "Current"] == pytest.approx(baseline.annualized_return)
    assert any("assumes daily rebalancing with no trading costs" in c.value for c in app.caption)


def test_daily_cost_free_optimization_has_no_baseline_note() -> None:
    app = analyze()
    widget(app.button, "Optimize portfolio").click().run()
    assert not app.exception and not app.error
    assert "optimization_baseline" not in app.session_state["analysis"]
    assert not any("assumes daily rebalancing" in c.value for c in app.caption)
