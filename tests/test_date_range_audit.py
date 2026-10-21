"""Edge cases for validate_date_range beyond the basic accept/reject table."""

from datetime import date, timedelta

import pandas as pd
import pytest

from risklens.validation import validate_date_range


def test_today_is_a_valid_start_date() -> None:
    assert validate_date_range(date.today()) == (pd.Timestamp(date.today()), None)


def test_tomorrow_is_rejected_as_future() -> None:
    with pytest.raises(ValueError, match="future"):
        validate_date_range(date.today() + timedelta(days=1))


def test_matching_time_zones_are_accepted() -> None:
    start, end = pd.Timestamp("2024-01-02", tz="UTC"), pd.Timestamp("2024-02-01", tz="UTC")

    assert validate_date_range(start, end) == (start, end)


def test_mixed_time_zones_raise_value_error() -> None:
    with pytest.raises(ValueError, match="time zone"):
        validate_date_range(pd.Timestamp("2024-01-02", tz="UTC"), "2024-02-01")


@pytest.mark.parametrize("bad", [float("nan"), pd.NaT, "", 12.5j])
def test_missing_or_nonsense_start_is_rejected(bad: object) -> None:
    with pytest.raises(ValueError, match="valid date"):
        validate_date_range(bad)  # type: ignore[arg-type]
