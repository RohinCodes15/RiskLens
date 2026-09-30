"""Holdings CSV parsing and share/dollar conversion to weights."""

import pandas as pd
import pytest

from risklens.holdings import parse_holdings_csv


def test_reads_shares_in_file_order() -> None:
    kind, amounts = parse_holdings_csv("ticker,shares\nmsft,4.5\nAAPL,10\n")
    assert kind == "shares"
    pd.testing.assert_series_equal(amounts, pd.Series({"MSFT": 4.5, "AAPL": 10.0}, name="shares"))


def test_reads_dollar_values_with_symbols_and_thousands_separators() -> None:
    kind, amounts = parse_holdings_csv('Ticker,Value\nAAPL,"$1,250.50"\nTLT,$800\nSPY,0\n')
    assert kind == "value"
    assert amounts.to_dict() == {"AAPL": 1250.5, "TLT": 800.0, "SPY": 0.0}


def test_accepts_excel_bytes_extra_columns_and_blank_lines() -> None:
    content = "﻿Account,Ticker,Shares\r\n\r\nIRA,brk-b,3\r\n,\r\nTaxable,AAPL,2\r\n"
    kind, amounts = parse_holdings_csv(content.encode("utf-8"))
    assert kind == "shares"
    assert amounts.to_dict() == {"BRK-B": 3.0, "AAPL": 2.0}


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
        ("AAPL,$", "Line 2: Shares is missing."),
        ("$$$,5", "Line 2: Invalid ticker symbol"),
        ("AAPL,ten", "Line 2: Shares must be a number; got 'ten'."),
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
