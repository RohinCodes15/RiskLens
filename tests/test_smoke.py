"""Network-free smoke coverage for the dashboard shell."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_renders_placeholder_metrics_and_disclaimer() -> None:
    """The initial UI renders without presenting placeholders as actual returns."""
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()

    assert not app.exception
    assert any(title.value == "RiskLens Quant" for title in app.title)
    assert [metric.label for metric in app.metric] == [
        "Annualized return", "Annualized volatility", "Historical VaR", "Maximum drawdown"
    ]
    assert all(metric.value == "—" for metric in app.metric)
    assert any("all metrics are placeholders" in notice.value for notice in app.info)
    assert any("not investment advice" in caption.value for caption in app.caption)
