"""Dashboard Monte Carlo return distribution: normal, Student-t, and bootstrap draws."""

from collections.abc import Iterator
from datetime import date
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from test_smoke import APP_PATH, chart_spec, chart_values, click_button

from risklens.analytics import analyze_portfolio, simulate_portfolio


@pytest.fixture
def prices() -> pd.DataFrame:
    """300 days of fat-tailed (Student-t) daily returns, so every model can run."""
    rng = np.random.default_rng(51)
    returns = rng.standard_t(4, (300, 3)) * [0.009, 0.007, 0.006]
    return pd.DataFrame(
        np.cumprod(1 + returns, axis=0) * [150.0, 300.0, 450.0],
        index=pd.bdate_range("2025-01-02", periods=300, name="Date"),
        columns=["AAPL", "MSFT", "SPY"],
    )


@pytest.fixture(autouse=True)
def download(prices: pd.DataFrame) -> Iterator[MagicMock]:
    def fake_download(tickers: list[str], **_: object) -> pd.DataFrame:
        return pd.concat({"Close": prices[list(tickers)]}, axis=1)

    with patch("yfinance.download", side_effect=fake_download) as mock:
        yield mock


def run_with(distribution_label: str) -> AppTest:
    app = AppTest.from_file(APP_PATH).run()
    app.date_input[0].set_value(date(2025, 1, 1))
    app = click_button(app, "Analyze portfolio")
    next(box for box in app.selectbox if box.label == "Return distribution").select(
        distribution_label
    )
    return click_button(app, "Run hypothetical simulations")


def expected(prices: pd.DataFrame, distribution: str) -> object:
    daily = analyze_portfolio(prices[["AAPL", "MSFT"]], [0.5, 0.5]).daily_returns
    return simulate_portfolio(daily, 252, 1000, 42, distribution=distribution)


@pytest.mark.parametrize(
    ("label", "distribution"),
    [
        ("Normal", "normal"),
        ("Student-t (fat tails)", "student_t"),
        ("Bootstrap (resample past days)", "bootstrap"),
    ],
)
def test_choice_reaches_the_engine_and_chart(
    prices: pd.DataFrame, label: str, distribution: str
) -> None:
    with patch("risklens.analytics.simulate_portfolio", wraps=simulate_portfolio) as engine:
        app = run_with(label)
    assert not app.exception and not app.error
    assert engine.call_args.kwargs["distribution"] == distribution
    median = next(t for t in chart_spec(app, "simulation_chart")["data"] if t["name"] == "Median")
    np.testing.assert_allclose(
        chart_values(median["y"]), expected(prices, distribution).percentile_paths["median"]
    )
    captions = " ".join(caption.value for caption in app.caption)
    assert f"seed 42 · {label}" in captions
    assert "already follow your rebalancing and trading cost" in captions


def test_student_t_caption_reports_degrees_of_freedom(prices: pd.DataFrame) -> None:
    app = run_with("Student-t (fat tails)")
    df = expected(prices, "student_t").degrees_of_freedom
    captions = " ".join(caption.value for caption in app.caption)
    assert f"Degrees of freedom: {df:.1f}" in captions


def test_bootstrap_caption_explains_its_limit() -> None:
    app = run_with("Bootstrap (resample past days)")
    captions = " ".join(caption.value for caption in app.caption)
    assert "never produces a day worse than the worst past day" in captions
    assert "Degrees of freedom" not in captions


def test_student_t_without_fat_tails_shows_an_error() -> None:
    with patch(
        "risklens.analytics.simulate_portfolio",
        side_effect=ValueError("These returns have no fat tails"),
    ):
        app = run_with("Student-t (fat tails)")
    assert not app.exception
    assert any("no fat tails" in error.value for error in app.error)
    assert "simulation_chart" not in [chart.key for chart in app.get("plotly_chart")]
