"""Unit tests for what-if trades: trade weights, trade cost, and before/after metrics."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import trade_weights


@pytest.fixture
def weights() -> pd.Series:
    return pd.Series([0.5, 0.3, 0.2], index=["AAPL", "MSFT", "KO"])


@pytest.fixture
def prices() -> pd.DataFrame:
    rng = np.random.default_rng(11)
    returns = rng.normal(0.0004, [0.015, 0.012, 0.008, 0.006], (120, 4))
    return pd.DataFrame(
        np.cumprod(1 + returns, axis=0) * 100.0,
        index=pd.bdate_range("2025-01-02", periods=120),
        columns=["AAPL", "MSFT", "KO", "TLT"],
    )


# --- trade_weights ---------------------------------------------------------------------


def test_moves_a_share_of_the_whole_portfolio_between_held_tickers(weights: pd.Series) -> None:
    after = trade_weights(weights, "AAPL", "KO", 0.1)
    assert after.to_dict() == pytest.approx({"AAPL": 0.4, "MSFT": 0.3, "KO": 0.3})
    assert after.sum() == pytest.approx(1.0)


def test_buying_a_new_ticker_appends_it(weights: pd.Series) -> None:
    after = trade_weights(weights, "MSFT", "TLT", 0.1)
    assert list(after.index) == ["AAPL", "MSFT", "KO", "TLT"]
    assert after.to_dict() == pytest.approx({"AAPL": 0.5, "MSFT": 0.2, "KO": 0.2, "TLT": 0.1})


def test_selling_the_whole_position_keeps_a_zero_weight(weights: pd.Series) -> None:
    after = trade_weights(weights, "KO", "TLT", 0.2)
    assert after["KO"] == 0.0
    assert after["TLT"] == pytest.approx(0.2)


def test_rounding_above_the_position_sells_exactly_all_of_it() -> None:
    weights = pd.Series([1 / 3, 1 / 3, 1 / 3], index=["A", "B", "C"])
    after = trade_weights(weights, "A", "B", 0.3333333334)
    assert after["A"] == 0.0
    assert after.sum() == pytest.approx(1.0)


def test_input_weights_are_not_modified(weights: pd.Series) -> None:
    original = weights.copy()
    trade_weights(weights, "AAPL", "TLT", 0.25)
    pd.testing.assert_series_equal(weights, original)


@pytest.mark.parametrize(
    ("sell", "buy", "amount", "message"),
    [
        ("NVDA", "TLT", 0.1, "not in the portfolio"),
        ("AAPL", "AAPL", 0.1, "different ticker"),
        ("AAPL", "  ", 0.1, "ticker to buy"),
        ("KO", "TLT", 0.25, "it is only 20.00%"),
        ("AAPL", "TLT", 0.0, "greater than 0"),
        ("AAPL", "TLT", -0.1, "greater than 0"),
        ("AAPL", "TLT", float("nan"), "greater than 0"),
        ("AAPL", "TLT", True, "must be a number"),
        ("AAPL", "TLT", "0.1", "must be a number"),
    ],
)
def test_rejects_impossible_trades(
    weights: pd.Series, sell: str, buy: str, amount: object, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        trade_weights(weights, sell, buy, amount)  # type: ignore[arg-type]


def test_rejects_invalid_weights() -> None:
    with pytest.raises(ValueError, match="sum to 1"):
        trade_weights(pd.Series([0.5, 0.4], index=["A", "B"]), "A", "B", 0.1)
    with pytest.raises(ValueError, match="only once"):
        trade_weights(pd.Series([0.5, 0.5], index=["A", "A"]), "A", "B", 0.1)
    with pytest.raises(ValueError, match="pandas Series"):
        trade_weights([0.5, 0.5], "A", "B", 0.1)  # type: ignore[arg-type]
