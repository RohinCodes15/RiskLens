"""Unit tests for the report export: tables, CSV zip, and HTML page."""

import io
import zipfile

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    COST_LABEL,
    analyze_portfolio,
    benchmark_statistics,
    drawdown_series,
    historical_var,
    rebalanced_risk_contributions,
)
from risklens.data import to_returns
from risklens.report import report_csv_zip, report_tables


@pytest.fixture
def prices() -> pd.DataFrame:
    rng = np.random.default_rng(2)
    daily = rng.normal(0.0005, [0.015, 0.01, 0.009], (200, 3))
    return pd.DataFrame(
        100 * np.cumprod(1 + daily, axis=0),
        index=pd.bdate_range("2025-01-02", periods=200),
        columns=["AAPL", "MSFT", "SPY"],
    )


@pytest.fixture
def tables(prices: pd.DataFrame) -> dict[str, pd.DataFrame]:
    stats = benchmark_statistics(
        prices[["AAPL", "MSFT"]], [0.6, 0.4], prices["SPY"], rebalance="monthly", cost_bps=5.0
    )
    return report_tables(prices[["AAPL", "MSFT"]], [0.6, 0.4], "monthly", 5.0, 25_000.0, stats)


def test_tables_match_the_analytics(prices: pd.DataFrame, tables: dict) -> None:
    assets = prices[["AAPL", "MSFT"]]
    result = analyze_portfolio(assets, [0.6, 0.4], rebalance="monthly", cost_bps=5.0)
    assert list(tables) == ["settings", "metrics", "holdings", "benchmark", "daily"]
    metrics = tables["metrics"]["value"]
    assert metrics["Annualized volatility"] == pytest.approx(result.annualized_volatility)
    assert metrics["Annual turnover"] == pytest.approx(result.annual_turnover)
    assert metrics["One-day VaR (99%)"] == pytest.approx(historical_var(result.daily_returns, 0.99))
    shares = rebalanced_risk_contributions(to_returns(assets), [0.6, 0.4], "monthly", 5.0)
    holdings = tables["holdings"]
    np.testing.assert_allclose(holdings["risk_share"], shares)
    assert holdings.loc["AAPL", "value"] == pytest.approx(15_000.0)
    assert holdings.loc["MSFT", "last_price"] == pytest.approx(prices["MSFT"].iloc[-1])
    assert holdings.loc[COST_LABEL, "weight"] == 0.0
    daily = tables["daily"]
    pd.testing.assert_series_equal(
        daily["drawdown"], drawdown_series(result.daily_returns), check_names=False
    )
    assert daily["wealth"].iloc[-1] == pytest.approx((1 + result.daily_returns).prod())
    assert tables["settings"].loc["Rebalancing", "value"] == "monthly"


def test_optional_parts_are_left_out(prices: pd.DataFrame) -> None:
    tables = report_tables(prices[["AAPL", "MSFT"]], [0.5, 0.5])
    assert "benchmark" not in tables
    assert "value" not in tables["holdings"]
    assert COST_LABEL not in tables["holdings"].index
    assert tables["settings"].loc["Portfolio value ($)", "value"] == ""


def test_csv_zip_holds_one_file_per_table(tables: dict) -> None:
    archive = zipfile.ZipFile(io.BytesIO(report_csv_zip(tables)))
    assert archive.namelist() == [f"{name}.csv" for name in tables]
    daily = pd.read_csv(archive.open("daily.csv"), index_col="date", parse_dates=True)
    np.testing.assert_allclose(daily["return"], tables["daily"]["return"])
    assert archive.read("daily.csv").decode().splitlines()[1].startswith("2025-01-03,")
