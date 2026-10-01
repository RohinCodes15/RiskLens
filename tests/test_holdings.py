"""Holdings CSV parsing and share/dollar conversion to weights."""

import numpy as np
import pandas as pd
import pytest

from risklens.holdings import holdings_to_weights, parse_holdings_csv


def test_reads_shares_in_file_order() -> None:
    kind, amounts = parse_holdings_csv("ticker,shares\nmsft,4.5\nAAPL,10\n")
    assert kind == "shares"
    pd.testing.assert_series_equal(amounts, pd.Series({"MSFT": 4.5, "AAPL": 10.0}, name="shares"))


def test_reads_dollar_values_with_symbols_and_thousands_separators() -> None:
    kind, amounts = parse_holdings_csv('Ticker,Value\nAAPL,"$1,250.50"\nTLT,$800\nSPY,0\n')
    assert kind == "value"
    assert amounts.to_dict() == {"AAPL": 1250.5, "TLT": 800.0, "SPY": 0.0}


def test_accepts_excel_bytes_extra_columns_and_blank_lines() -> None:
    content = "\ufeffTicker,Account,Shares\r\n\r\nbrk-b,IRA,3\r\n,\r\nAAPL,Taxable,2\r\n"
    kind, amounts = parse_holdings_csv(content.encode("utf-8"))
    assert kind == "shares"
    assert amounts.to_dict() == {"BRK-B": 3.0, "AAPL": 2.0}


def test_reads_old_mac_line_endings() -> None:
    kind, amounts = parse_holdings_csv(b"ticker,shares\rAAPL,10\rMSFT,4\r")
    assert kind == "shares"
    assert amounts.to_dict() == {"AAPL": 10.0, "MSFT": 4.0}


@pytest.mark.parametrize(
    "header",
    ["symbol,shares", "ticker,quantity", "ticker,shares,value", "ticker"],
)
def test_rejects_a_header_without_ticker_and_one_amount_column(header: str) -> None:
    with pytest.raises(ValueError, match="ticker column and either a shares or a value"):
        parse_holdings_csv(f"{header}\nAAPL,1\n")


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("", "empty"),
        ("\n \n", "empty"),
        ("ticker,shares\n", "no rows below the header"),
        (b"ticker,shares\nAAPL,\xff\n", "UTF-8"),
        ("ticker,shares\nAAPL," + "9" * 200_000, "not valid CSV"),  # over csv's field limit
    ],
)
def test_rejects_unusable_files(content: str | bytes, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        parse_holdings_csv(content)


def test_rejects_more_than_the_ticker_limit() -> None:
    rows = "".join(f"T{index},1\n" for index in range(26))
    with pytest.raises(ValueError, match=r"Too many holdings \(26\); the limit is 25"):
        parse_holdings_csv("ticker,shares\n" + rows)


@pytest.mark.parametrize(
    ("row", "message"),
    [
        (",5", "Line 2: Ticker is missing."),
        ("AAPL", "Line 2: Shares is missing."),
        ("AAPL,$", "Line 2: Shares must be a number; got '$'."),
        ("$$$,5", "Line 2: Invalid ticker symbol"),
        ("AAPL,ten", "Line 2: Shares must be a number; got 'ten'."),
        ("AAPL,$10", "Line 2: Shares must be a number; got '$10'."),
        ('AAPL,"0,500"', "Line 2: Shares must be a number; got '0,500'."),
        ('AAPL,"1,5"', "Line 2: Shares must be a number; got '1,5'."),
        ("AAPL,-3", "Line 2: Shares must be a finite number of zero or more; got '-3'."),
        ("AAPL,nan", "Line 2: Shares must be a finite number of zero or more"),
        ("AAPL,inf", "Line 2: Shares must be a finite number of zero or more"),
    ],
)
def test_names_the_line_and_problem_of_a_bad_row(row: str, message: str) -> None:
    with pytest.raises(ValueError) as excinfo:
        parse_holdings_csv(f"ticker,shares\n{row}\n")
    assert str(excinfo.value).startswith(message)


def test_lists_every_bad_row_including_repeated_tickers() -> None:
    content = "ticker,value\nAAPL,100\n\nMSFT,abc\naapl,50\nTLT,-1\n"
    with pytest.raises(ValueError) as excinfo:
        parse_holdings_csv(content)
    assert str(excinfo.value) == (
        "Line 4: Value must be a number; got 'abc'. "
        "Line 5: AAPL is already listed on line 2. "
        "Line 6: Value must be a finite number of zero or more; got '-1'."
    )


@pytest.fixture
def prices() -> pd.DataFrame:
    index = pd.bdate_range("2026-03-02", periods=3)
    return pd.DataFrame({"AAPL": [190.0, 195.0, 200.0], "MSFT": [410.0, 405.0, 400.0]}, index=index)


def test_shares_are_valued_at_the_last_price_in_price_column_order(
    prices: pd.DataFrame,
) -> None:
    weights, total = holdings_to_weights(pd.Series({"MSFT": 5.0, "AAPL": 10.0}), "shares", prices)
    assert total == pytest.approx(10 * 200.0 + 5 * 400.0)
    np.testing.assert_allclose(weights, [0.5, 0.5])


def test_dollar_values_ignore_prices(prices: pd.DataFrame) -> None:
    weights, total = holdings_to_weights(pd.Series({"AAPL": 750.0, "MSFT": 250.0}), "value", prices)
    assert total == pytest.approx(1000.0)
    np.testing.assert_allclose(weights, [0.75, 0.25])


def test_zero_holdings_keep_a_zero_weight(prices: pd.DataFrame) -> None:
    weights, total = holdings_to_weights(pd.Series({"AAPL": 0.0, "MSFT": 3.0}), "shares", prices)
    assert total == pytest.approx(1200.0)
    np.testing.assert_allclose(weights, [0.0, 1.0])


@pytest.mark.parametrize(
    ("amounts", "kind", "message"),
    [
        ({"AAPL": 1.0, "MSFT": 1.0}, "percent", "shares or value"),
        ({"AAPL": 1.0}, "shares", "each priced ticker exactly once"),
        ({"AAPL": 1.0, "TLT": 1.0}, "shares", "each priced ticker exactly once"),
        ({"AAPL": 1.0, "MSFT": -1.0}, "shares", "finite numbers of zero or more"),
        ({"AAPL": 1.0, "MSFT": float("nan")}, "value", "finite numbers of zero or more"),
        ({"AAPL": "ten", "MSFT": 1.0}, "value", "Value must be numbers"),
        ({"AAPL": 0.0, "MSFT": 0.0}, "shares", "at least one holding above zero"),
    ],
)
def test_rejects_unusable_holdings(
    prices: pd.DataFrame, amounts: dict[str, object], kind: str, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        holdings_to_weights(pd.Series(amounts), kind, prices)


def test_rejects_unusable_prices(prices: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="positive"):
        holdings_to_weights(pd.Series({"AAPL": 1.0, "MSFT": 1.0}), "shares", -prices)
