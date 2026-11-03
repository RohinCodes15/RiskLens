"""Unit tests for Ken French factor parsing and Yahoo classifications (no network)."""

import io
import zipfile
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from risklens.data import DataFetchError, fetch_factors

FACTORS_CSV = """This file was created by CMPT_ME_BEME_RETS_DAILY.

,Mkt-RF,SMB,HML,RF
20250102,  -0.50,   0.20,   0.10,   0.02
20250103,   1.00,  -0.10,   0.00,   0.02
20250106,   0.40,   0.30,  -0.20,   0.02

Copyright 2025 Eugene F. Fama and Kenneth R. French
"""
MOMENTUM_CSV = """Momentum factor daily

,Mom   
20250102,   0.70
20250103,  -0.30
20250106,   0.10
"""


def zipped(text: str) -> MagicMock:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("data.CSV", text)
    response = MagicMock()
    response.__enter__.return_value.read.return_value = buffer.getvalue()
    return response


def test_parses_percent_tables_into_fractions_and_joins_momentum() -> None:
    with patch("risklens.data.urlopen", side_effect=[zipped(FACTORS_CSV), zipped(MOMENTUM_CSV)]):
        factors = fetch_factors("2025-01-03", "2025-01-07")
    assert list(factors.columns) == ["Mkt-RF", "SMB", "HML", "RF", "Mom"]
    assert list(factors.index) == list(pd.to_datetime(["2025-01-03", "2025-01-06"]))
    assert factors.loc["2025-01-03", "Mkt-RF"] == pytest.approx(0.01)
    assert factors.loc["2025-01-06", "Mom"] == pytest.approx(0.001)


def test_download_errors_and_files_without_data_raise_data_fetch_error() -> None:
    with patch("risklens.data.urlopen", side_effect=OSError("offline")):
        with pytest.raises(DataFetchError, match="offline"):
            fetch_factors("2025-01-01")
    with patch("risklens.data.urlopen", side_effect=[zipped("no table here"), zipped("")]):
        with pytest.raises(DataFetchError, match="no daily data"):
            fetch_factors("2025-01-01")
