"""Dashboard report export: Prepare report builds the HTML page and the CSV zip."""

import io
import zipfile
from collections.abc import Iterator
from datetime import date
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from test_smoke import APP_PATH, click_button

from risklens.report import REPORT_TITLE, report_tables


@pytest.fixture
def prices() -> pd.DataFrame:
    rng = np.random.default_rng(71)
    daily = rng.normal(0.0004, [0.014, 0.010, 0.009], (150, 3))
    return pd.DataFrame(
        100 * np.cumprod(1 + daily, axis=0),
        index=pd.bdate_range("2025-01-02", periods=150, name="Date"),
        columns=["AAPL", "MSFT", "SPY"],
    )


@pytest.fixture(autouse=True)
def download(prices: pd.DataFrame) -> Iterator[MagicMock]:
    def fake_download(tickers: list[str], **_: object) -> pd.DataFrame:
        return pd.concat({"Close": prices[list(tickers)]}, axis=1)

    with patch("yfinance.download", side_effect=fake_download) as mock:
        yield mock


def analyzed() -> AppTest:
    app = AppTest.from_file(APP_PATH).run()
    app.date_input[0].set_value(date(2025, 1, 1))
    return click_button(app, "Analyze portfolio")


def test_waits_for_the_button() -> None:
    app = analyzed()
    assert "report" not in app.session_state["analysis"]
    assert any("Select Prepare report" in info.value for info in app.info)


def test_prepare_report_builds_both_downloads(prices: pd.DataFrame) -> None:
    app = click_button(analyzed(), "Prepare report")
    assert not app.exception and not app.error
    analysis = app.session_state["analysis"]
    page, archive = analysis["report"]
    html = page.decode("utf-8")
    assert f"<title>{REPORT_TITLE}</title>" in html
    assert "<h2>Portfolio wealth</h2>" in html and "<h2>Drawdown</h2>" in html
    assert html.count("plotly.js v") == 1  # plotly.js embedded once, so it works offline
    expected = report_tables(
        analysis["prices"],
        analysis["weights"],
        analysis["rebalance"],
        analysis["cost_bps"],
        analysis["portfolio_value"],
        analysis["benchmark_stats"],
    )
    files = zipfile.ZipFile(io.BytesIO(archive))
    assert files.namelist() == [f"{name}.csv" for name in expected]
    metrics = pd.read_csv(files.open("metrics.csv"), index_col="metric")["value"]
    np.testing.assert_allclose(metrics, expected["metrics"]["value"])
    labels = [button.label for button in app.get("download_button")]
    assert labels == ["Download HTML report", "Download CSV tables (.zip)"]


def test_new_analysis_drops_the_old_report() -> None:
    app = click_button(analyzed(), "Prepare report")
    app = click_button(app, "Analyze portfolio")
    assert "report" not in app.session_state["analysis"]


def test_report_failure_shows_a_warning() -> None:
    app = analyzed()
    with patch("risklens.report.report_tables", side_effect=ValueError("bad report")):
        app = click_button(app, "Prepare report")
    assert not app.exception
    assert any("bad report" in warning.value for warning in app.warning)
