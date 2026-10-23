"""Deterministic unit tests for dated rolling volatility, Sharpe, and drawdown."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    ROLLING_WINDOWS,
    TRADING_DAYS_PER_YEAR,
    annualized_volatility,
    drawdown_series,
    rolling_drawdown,
    rolling_max_drawdown,
    rolling_sharpe,
    rolling_volatility,
    sharpe_ratio,
)

ROLLING_FUNCTIONS = [rolling_volatility, rolling_sharpe, rolling_drawdown, rolling_max_drawdown]


def dated(values: list[float] | np.ndarray) -> pd.Series:
    return pd.Series(values, index=pd.bdate_range("2024-01-02", periods=len(values)), name="r")


def noisy(n: int = 300) -> pd.Series:
    return dated(np.random.default_rng(0).normal(0.0005, 0.01, n))


# --- windows, alignment, and input validation ---------------------------------


def test_default_windows_are_one_month_quarter_and_half_year() -> None:
    assert ROLLING_WINDOWS == (21, 63, 126)


@pytest.mark.parametrize("func", ROLLING_FUNCTIONS)
@pytest.mark.parametrize("window", ROLLING_WINDOWS)
def test_output_dates_match_input_and_lead_is_nan(func: object, window: int) -> None:
    returns = noisy()
    result = func(returns, window)  # type: ignore[operator]

    assert result.index.equals(returns.index)
    assert result.iloc[: window - 1].isna().all()
    assert result.iloc[window - 1 :].notna().all()


@pytest.mark.parametrize("func", ROLLING_FUNCTIONS)
def test_input_returns_are_not_mutated(func: object) -> None:
    returns = noisy(30)
    before = returns.copy()

    func(returns, 21)  # type: ignore[operator]

    pd.testing.assert_series_equal(returns, before)


@pytest.mark.parametrize("func", ROLLING_FUNCTIONS)
@pytest.mark.parametrize(
    ("window", "message"),
    [(1, "at least 2"), (0, "at least 2"), (-21, "at least 2"), (21.0, "whole number"),
     ("21", "whole number"), (True, "whole number"), (None, "whole number")],
)
def test_invalid_windows_are_rejected(func: object, window: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        func(noisy(30), window)  # type: ignore[operator]


@pytest.mark.parametrize("func", ROLLING_FUNCTIONS)
def test_numpy_integer_window_is_accepted(func: object) -> None:
    result = func(noisy(30), np.int64(21))  # type: ignore[operator]

    assert result.notna().sum() == 10


@pytest.mark.parametrize("func", ROLLING_FUNCTIONS)
@pytest.mark.parametrize(
    ("bad", "message"),
    [([0.01, np.nan, 0.02], "NaN"), ([0.01, np.inf, 0.02], "infinite"),
     ([0.01, -1.5, 0.02], "below -100%")],
)
def test_nonfinite_or_impossible_returns_are_rejected(func: object, bad: list[float], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        func(dated(bad), 2)  # type: ignore[operator]


@pytest.mark.parametrize("func", ROLLING_FUNCTIONS)
def test_undated_or_unsorted_returns_are_rejected(func: object) -> None:
    with pytest.raises(ValueError, match="indexed by date"):
        func(pd.Series([0.01, 0.02, 0.03]), 2)  # type: ignore[operator]
    with pytest.raises(ValueError, match="sorted and unique"):
        func(noisy(5).iloc[::-1], 2)  # type: ignore[operator]


@pytest.mark.parametrize("func", ROLLING_FUNCTIONS)
def test_fewer_returns_than_window_is_rejected(func: object) -> None:
    with pytest.raises(ValueError, match="at least 21 daily returns"):
        func(noisy(20), 21)  # type: ignore[operator]
    with pytest.raises(ValueError, match="No returns"):
        func(dated([]), 21)  # type: ignore[operator]


def test_exactly_window_returns_gives_one_value() -> None:
    assert rolling_volatility(noisy(21), 21).notna().sum() == 1


# --- rolling volatility --------------------------------------------------------


@pytest.mark.parametrize("window", ROLLING_WINDOWS)
def test_volatility_matches_annualized_volatility_on_each_window(window: int) -> None:
    returns = noisy()
    result = rolling_volatility(returns, window)

    for end in range(window, len(returns) + 1, 17):
        expected = annualized_volatility(returns.iloc[end - window : end])
        assert result.iloc[end - 1] == pytest.approx(expected, rel=1e-12)


def test_volatility_hand_calculation() -> None:
    result = rolling_volatility(dated([0.01, -0.01, 0.03]), 2)

    expected = [np.nan, np.std([0.01, -0.01], ddof=1), np.std([-0.01, 0.03], ddof=1)]
    np.testing.assert_allclose(result, np.array(expected) * np.sqrt(TRADING_DAYS_PER_YEAR))


def test_constant_window_has_exactly_zero_volatility() -> None:
    returns = dated([0.02, -0.01] + [0.001] * 21)  # last window is constant

    assert rolling_volatility(returns, 21).iloc[-1] == 0.0


# --- rolling Sharpe ratio --------------------------------------------------------


@pytest.mark.parametrize("rate", [0.0, 0.04, -0.01])
@pytest.mark.parametrize("window", ROLLING_WINDOWS)
def test_sharpe_matches_sharpe_ratio_on_each_window(window: int, rate: float) -> None:
    returns = noisy()
    result = rolling_sharpe(returns, window, risk_free_rate=rate)

    for end in range(window, len(returns) + 1, 17):
        expected = sharpe_ratio(returns.iloc[end - window : end], rate)
        assert result.iloc[end - 1] == pytest.approx(expected, rel=1e-12)


def test_sharpe_hand_calculation_with_risk_free_rate() -> None:
    window = [0.01, -0.01, 0.03]
    result = rolling_sharpe(dated(window), 3, risk_free_rate=0.04)

    vol = np.std(window, ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)
    assert result.iloc[-1] == pytest.approx((np.mean(window) * TRADING_DAYS_PER_YEAR - 0.04) / vol)


def test_zero_volatility_window_gives_nan_sharpe() -> None:
    returns = dated([0.03, -0.02] + [0.001] * 5)
    result = rolling_sharpe(returns, 5)

    assert np.isnan(result.iloc[-1])
    assert np.isfinite(result.iloc[4])  # earlier window still had variation
    assert np.isnan(sharpe_ratio(returns.iloc[-5:]))


@pytest.mark.parametrize("rate", ["4%", 4.0, float("nan"), True])
def test_invalid_risk_free_rate_is_rejected(rate: object) -> None:
    with pytest.raises(ValueError, match="Risk-free rate"):
        rolling_sharpe(noisy(30), 21, risk_free_rate=rate)  # type: ignore[arg-type]


# --- rolling drawdown (local peak) ----------------------------------------------------


def test_drawdown_uses_local_peak_not_all_time_high() -> None:
    # Wealth: 1.0 -> 2.0 -> 1.0 -> 1.0 -> 1.0. All-time drawdown stays -50%;
    # a 2-day window ending on day 4 only sees levels 1.0, 1.0, 1.0.
    returns = dated([1.0, -0.5, 0.0, 0.0])

    assert drawdown_series(returns).iloc[-1] == pytest.approx(-0.5)
    np.testing.assert_allclose(rolling_drawdown(returns, 2), [np.nan, -0.5, -0.5, 0.0])


def test_drawdown_counts_the_level_before_the_window() -> None:
    # A 2-day window of -10% then +5% ends 5.5% below its starting level.
    result = rolling_drawdown(dated([0.0, -0.10, 0.05]), 2)

    assert result.iloc[-1] == pytest.approx(0.9 * 1.05 - 1)


@pytest.mark.parametrize("window", ROLLING_WINDOWS)
def test_drawdown_matches_drawdown_series_on_each_window(window: int) -> None:
    returns = noisy()
    result = rolling_drawdown(returns, window)

    for end in range(window, len(returns) + 1, 17):
        expected = drawdown_series(returns.iloc[end - window : end]).iloc[-1]
        assert result.iloc[end - 1] == pytest.approx(expected, abs=1e-12)


def test_drawdown_is_never_positive_and_total_loss_is_minus_one() -> None:
    assert (rolling_drawdown(noisy(), 21).dropna() <= 0).all()
    assert rolling_drawdown(dated([0.01, -1.0, 0.0]), 2).iloc[1] == -1.0
