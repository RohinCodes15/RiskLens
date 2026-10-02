"""Dashboard Sortino/Calmar cards, VaR models and backtest, and SPY ratios."""

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
    benchmark_statistics,
    cornish_fisher_var,
    normal_var,
    var_backtest,
)

APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture
def prices() -> pd.DataFrame:
    """300 trading days of two fat-tailed stocks and SPY, served by ticker."""
    rng = np.random.default_rng(21)
    index = pd.bdate_range("2025-01-02", periods=300, name="Date")
    returns = rng.standard_t(4, (300, 3)) * [0.012, 0.009, 0.008] + [0.0006, 0.0003, 0.0004]
    return pd.DataFrame(
        np.cumprod(1 + returns, axis=0) * [150.0, 300.0, 450.0],
        index=index,
        columns=["AAPL", "MSFT", "SPY"],
    )


@pytest.fixture(autouse=True)
def download(prices: pd.DataFrame) -> Iterator[MagicMock]:
    def fake_download(tickers: list[str], **_: object) -> pd.DataFrame:
        return pd.concat({"Close": prices[list(tickers)]}, axis=1)

    with patch("yfinance.download", side_effect=fake_download) as mock:
        yield mock


def widget(widgets: object, label: str) -> object:
    return next(item for item in widgets if item.label == label)


def analyze(rebalance: str | None = None, cost_bps: float | None = None) -> AppTest:
    app = AppTest.from_file(APP_PATH).run()
    if rebalance is not None:
        widget(app.selectbox, "Rebalancing").select(rebalance)
    if cost_bps is not None:
        widget(app.number_input, "Trading cost (bps)").set_value(cost_bps)
    app.date_input[0].set_value(date(2025, 1, 1))
    return widget(app.button, "Analyze portfolio").click().run()


def cards(app: AppTest) -> dict[str, str]:
    return {card.label: card.value for card in app.metric}


def test_ratio_cards_follow_rebalancing_and_costs(prices: pd.DataFrame) -> None:
    app = analyze("Monthly", 25.0)
    assert not app.exception and not app.error
    expected = analyze_portfolio(
        prices[["AAPL", "MSFT"]], [0.5, 0.5], rebalance="monthly", cost_bps=25.0
    )
    assert cards(app)["Sortino ratio"] == f"{expected.sortino_ratio:.2f}"
    assert cards(app)["Calmar ratio"] == f"{expected.calmar_ratio:.2f}"
    labels = [card.label for card in app.metric]
    assert labels.index("Sortino ratio") == labels.index("Maximum drawdown") + 1


def test_tail_risk_shows_normal_and_cornish_fisher_var_in_percent_and_dollars(
    prices: pd.DataFrame,
) -> None:
    app = AppTest.from_file(APP_PATH).run()
    widget(app.number_input, "Portfolio value ($)").set_value(50_000.0)
    app.date_input[0].set_value(date(2025, 1, 1))
    app = widget(app.button, "Analyze portfolio").click().run()
    app = widget(app.selectbox, "Tail risk confidence").select(0.99).run()
    assert not app.exception and not app.error
    daily = analyze_portfolio(prices[["AAPL", "MSFT"]], [0.5, 0.5]).daily_returns
    normal, modified = normal_var(daily, 0.99), cornish_fisher_var(daily, 0.99)
    assert modified > normal > 0  # the fixture's returns have fat tails
    assert cards(app)["Normal VaR"] == f"{normal:.2%}"
    assert cards(app)["Cornish-Fisher VaR"] == f"{modified:.2%}"
    deltas = {card.label: card.delta for card in app.metric}
    assert deltas["Normal VaR"] == f"-${round(normal * 50_000):,}"
    assert deltas["Cornish-Fisher VaR"] == f"-${round(modified * 50_000):,}"


def test_cornish_fisher_var_is_na_with_fewer_than_four_returns(
    prices: pd.DataFrame, download: MagicMock
) -> None:
    download.side_effect = lambda tickers, **_: pd.concat(
        {"Close": prices[list(tickers)].iloc[:3]}, axis=1
    )
    app = analyze()
    assert not app.exception and not app.error
    assert cards(app)["Cornish-Fisher VaR"] == "N/A"
    assert cards(app)["Normal VaR"] != "N/A"


def serve(download: MagicMock, prices: pd.DataFrame) -> None:
    download.side_effect = lambda tickers, **_: pd.concat({"Close": prices[list(tickers)]}, axis=1)


def test_backtest_table_matches_var_backtest_for_the_chosen_window(prices: pd.DataFrame) -> None:
    app = analyze()
    assert widget(app.selectbox, "VaR estimation window").value == 126
    app = widget(app.selectbox, "VaR estimation window").select(63).run()
    assert not app.exception and not app.error
    daily = analyze_portfolio(prices[["AAPL", "MSFT"]], [0.5, 0.5]).daily_returns
    expected = var_backtest(daily, 63, 0.95)
    table = app.table[0].value
    assert list(table.index) == ["Historical", "Normal", "Cornish-Fisher"]
    assert table["Days tested"].tolist() == expected["days"].tolist() == [236] * 3
    assert table["Breaches"].tolist() == expected["breaches"].tolist()
    np.testing.assert_allclose(table["Expected"], expected["expected_breaches"])
    np.testing.assert_allclose(table["Breach rate"], expected["breach_rate"])
    np.testing.assert_allclose(table["Kupiec p-value"], expected["p_value"])


@pytest.mark.parametrize(
    ("calm_first", "result"),
    [(True, "Too many breaches: VaR too low"), (False, "Too few breaches: VaR too high")],
)
def test_backtest_flags_var_that_was_too_low_or_too_high(
    download: MagicMock, calm_first: bool, result: str
) -> None:
    rng = np.random.default_rng(8)
    calm, wild = rng.normal(0, 0.002, (150, 3)), rng.normal(0, 0.03, (150, 3))
    returns = np.vstack([calm, wild] if calm_first else [wild, calm])
    index = pd.bdate_range("2025-01-02", periods=300, name="Date")
    serve(
        download,
        pd.DataFrame(100 * np.cumprod(1 + returns, axis=0), index, ["AAPL", "MSFT", "SPY"]),
    )
    app = analyze()
    # Only historical and normal VaR are pinned: at 95%, Cornish-Fisher shrinks its
    # VaR when kurtosis is high, so windows mixing both regimes can still pass.
    assert app.table[0].value["Result"].tolist()[:2] == [result] * 2


def test_backtest_explains_when_the_period_is_shorter_than_the_window(
    prices: pd.DataFrame, download: MagicMock
) -> None:
    serve(download, prices.iloc[:100])
    app = analyze()
    assert not app.table
    assert any(
        "A 126-day backtest needs more than 126 daily returns; this period has 99." in note.value
        for note in app.info
    )
    app = widget(app.selectbox, "VaR estimation window").select(63).run()
    assert app.table[0].value["Days tested"].tolist() == [36] * 3


def test_spy_section_shows_information_ratio_and_capture(prices: pd.DataFrame) -> None:
    app = analyze("Quarterly", 10.0)
    assert not app.exception and not app.error
    expected = benchmark_statistics(
        prices[["AAPL", "MSFT"]],
        [0.5, 0.5],
        prices["SPY"],
        rebalance="quarterly",
        cost_bps=10.0,
    )
    assert cards(app)["Information ratio"] == f"{expected.information_ratio:.2f}"
    assert cards(app)["Upside capture"] == f"{expected.upside_capture:.0%}"
    assert cards(app)["Downside capture"] == f"{expected.downside_capture:.0%}"


def test_ratios_explain_why_they_are_missing_when_spy_is_flat(
    prices: pd.DataFrame, download: MagicMock
) -> None:
    serve(download, prices.assign(SPY=450.0))
    app = analyze()
    assert not app.exception and not app.error
    assert app.get("plotly_chart")  # the SPY growth chart still shows
    assert "Information ratio" not in cards(app)
    assert any(
        "Information ratio and capture are unavailable. Benchmark returns are constant"
        in note.value
        for note in app.info
    )


def test_backtest_withholds_a_verdict_with_too_few_test_days(
    prices: pd.DataFrame, download: MagicMock
) -> None:
    serve(download, prices.iloc[:65])  # 64 returns: one test day after a 63-day window
    app = analyze()
    app = widget(app.selectbox, "VaR estimation window").select(63).run()
    assert not app.exception and not app.error
    assert app.table[0].value["Result"].tolist() == ["Too few test days to judge"] * 3


def test_backtest_warns_that_short_windows_leave_historical_var_few_tail_days() -> None:
    app = analyze()
    app = widget(app.selectbox, "Tail risk confidence").select(0.99).run()
    notes = " ".join(caption.value for caption in app.caption)
    assert "A 126-day window holds only about 1.3 days beyond the 99% cutoff" in notes
    app = widget(app.selectbox, "Tail risk confidence").select(0.95).run()
    notes = " ".join(caption.value for caption in app.caption)
    assert "days beyond the" not in notes  # 126 x 5% = 6.3 tail days is enough
