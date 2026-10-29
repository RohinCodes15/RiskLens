"""Unit tests for cumulative wealth, SPY download, and benchmark comparison."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import compare_to_benchmark, cumulative_wealth
from risklens.data import BENCHMARK_TICKER, fetch_benchmark_prices


def dates(n: int, start: str = "2024-01-02") -> pd.DatetimeIndex:
    return pd.bdate_range(start, periods=n)


def test_cumulative_wealth_compounds_from_one() -> None:
    returns = pd.Series([0.10, -0.10], index=dates(2))

    result = cumulative_wealth(returns)

    np.testing.assert_allclose(result.to_numpy(), [1.10, 0.99])
    assert result.index.equals(returns.index)


def test_fetch_benchmark_prices_downloads_spy_adjusted_close() -> None:
    close = pd.DataFrame({BENCHMARK_TICKER: [400.0, 404.0, 402.0]}, index=dates(3))
    raw = pd.concat({"Close": close}, axis=1)

    with patch("yfinance.download", return_value=raw) as download:
        result = fetch_benchmark_prices("2024-01-02", "2024-01-05")

    assert download.call_args.args[0] == [BENCHMARK_TICKER]
    assert download.call_args.kwargs["auto_adjust"] is True
    pd.testing.assert_series_equal(result, close[BENCHMARK_TICKER])


def test_both_curves_start_at_one_on_first_shared_date() -> None:
    assets = pd.DataFrame({"A": [100.0, 110.0, 121.0], "B": [50.0, 50.0, 55.0]}, index=dates(3))
    spy = pd.Series([400.0, 420.0, 399.0], index=dates(3), name="SPY")

    result = compare_to_benchmark(assets, [0.5, 0.5], spy)

    assert list(result.columns) == ["portfolio", "benchmark"]
    assert result.index.equals(dates(3))
    assert result.iloc[0].tolist() == [1.0, 1.0]
    # Day 1: A +10%, B 0% -> +5%. Day 2: A +10%, B +10% -> +10%.
    np.testing.assert_allclose(result["portfolio"], [1.0, 1.05, 1.155])
    np.testing.assert_allclose(result["benchmark"], [1.0, 1.05, 0.9975])


def test_uses_only_dates_shared_by_assets_and_benchmark() -> None:
    assets = pd.DataFrame({"A": [100.0, 101.0, 102.0, 103.0]}, index=dates(4))
    spy = pd.Series([400.0, 404.0, 408.0, 412.0], index=dates(4, "2024-01-03"))

    result = compare_to_benchmark(assets, [1.0], spy)

    assert result.index.equals(dates(3, "2024-01-03"))
    assert result["portfolio"].iloc[0] == 1.0
    assert result["portfolio"].iloc[-1] == pytest.approx(103.0 / 101.0)


def test_drops_dates_with_missing_prices() -> None:
    assets = pd.DataFrame({"A": [100.0, np.nan, 120.0], "B": [10.0, 11.0, 12.0]}, index=dates(3))
    spy = pd.Series([400.0, np.nan, 440.0], index=dates(3))

    result = compare_to_benchmark(assets, [0.5, 0.5], spy)

    assert result.index.equals(dates(3)[[0, 2]])
    assert result["benchmark"].iloc[-1] == pytest.approx(1.10)
    assert not result.isna().to_numpy().any()


def test_does_not_mutate_inputs() -> None:
    assets = pd.DataFrame({"A": [100.0, np.nan, 120.0]}, index=dates(3))
    spy = pd.Series([400.0, 410.0, 440.0], index=dates(3))
    assets_before, spy_before = assets.copy(), spy.copy()

    compare_to_benchmark(assets, [1.0], spy)

    pd.testing.assert_frame_equal(assets, assets_before)
    pd.testing.assert_series_equal(spy, spy_before)


def test_rejects_fewer_than_two_shared_dates() -> None:
    assets = pd.DataFrame({"A": [100.0, 101.0]}, index=dates(2))
    spy = pd.Series([400.0, 404.0], index=dates(2, "2024-01-03"))

    with pytest.raises(ValueError, match="at least 2 shared price dates"):
        compare_to_benchmark(assets, [1.0], spy)


def test_rejects_invalid_weights() -> None:
    assets = pd.DataFrame({"A": [100.0, 101.0], "B": [50.0, 51.0]}, index=dates(2))
    spy = pd.Series([400.0, 404.0], index=dates(2))

    with pytest.raises(ValueError, match="sum to 1"):
        compare_to_benchmark(assets, [0.7, 0.7], spy)
