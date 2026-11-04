"""Unit tests for turnover limits on minimum-volatility and maximum-Sharpe weights."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    one_way_turnover,
    validate_turnover_limit,
)
from risklens.analytics.turnover_limit import turnover_constraints

CURRENT = [0.7, 0.1, 0.1, 0.1]


@pytest.fixture(scope="module")
def prices() -> pd.DataFrame:
    rng = np.random.default_rng(3)
    daily = rng.normal([0.0008, 0.0003, 0.0005, 0.0002], [0.02, 0.008, 0.015, 0.01], (500, 4))
    return pd.DataFrame(
        100 * np.cumprod(1 + daily, axis=0),
        index=pd.bdate_range("2023-01-02", periods=500),
        columns=["A", "B", "C", "D"],
    )


def test_one_way_turnover_counts_what_is_bought() -> None:
    assert one_way_turnover([0.5, 0.5], [0.7, 0.3]) == pytest.approx(0.2)
    assert one_way_turnover([1.0, 0.0], [0.0, 1.0]) == pytest.approx(1.0)
    assert one_way_turnover(CURRENT, CURRENT) == 0.0
    with pytest.raises(ValueError, match="Expected 4"):
        one_way_turnover(CURRENT, [0.5, 0.5])


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (-0.1, "between 0 and 1"),
        (1.5, "between 0 and 1"),
        (np.nan, "between 0 and 1"),
        (True, "a number"),
        ("0.2", "a number"),
    ],
)
def test_validate_turnover_limit_rejects_bad_values(value: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        validate_turnover_limit(value)  # type: ignore[arg-type]


def test_constraints_hold_exactly_at_the_current_weights() -> None:
    current = np.array(CURRENT)
    rows = turnover_constraints(current, 0.2)
    assert rows.shape == (9, 8)
    assert np.all(rows @ np.concatenate([current, np.zeros(4)]) >= -1e-12)  # 0 up to rounding
    moved = np.array([0.4, 0.2, 0.2, 0.2])  # turnover 0.3, over the 0.2 limit
    assert (rows @ np.concatenate([moved, np.abs(moved - current)]))[-1] < 0
