"""Report export: the core analysis as CSV tables (in a zip) and one HTML page.

``report_tables`` recomputes the portfolio's metrics from prices and weights,
with the same rebalancing and trading cost as the dashboard, so the export
never disagrees with the analytics. Rates are fractions (0.05 = 5%) in the
CSV files; the HTML page shows them as percents.

Charts are passed in as ready-made HTML snippets, so this module stays free of
Streamlit and Plotly. Results of on-demand tools (simulations, stress tests,
optimization, factors, what-if trades, shocks) are not included.
"""

import io
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import date
from html import escape

import pandas as pd

from risklens.analytics.attribution import rebalanced_risk_contributions
from risklens.analytics.benchmark import BenchmarkStatistics
from risklens.analytics.engine import PortfolioMetrics, analyze_portfolio
from risklens.analytics.metrics import cumulative_wealth, drawdown_series, tail_risk_summary
from risklens.data import to_returns

REPORT_TITLE = "RiskLens portfolio report"
RATIO_METRICS = ("Sharpe ratio", "Sortino ratio", "Calmar ratio")
BENCHMARK_RATIOS = (
    "beta",
    "correlation",
    "information_ratio",
    "upside_capture",
    "downside_capture",
)


def _settings(
    prices: pd.DataFrame, rebalance: str, cost_bps: float, portfolio_value: float | None
) -> pd.DataFrame:
    """Analysis settings as text, one row each."""
    rows = {
        "Start date": f"{prices.index[0]:%Y-%m-%d}",
        "End date": f"{prices.index[-1]:%Y-%m-%d}",
        "Price dates": f"{len(prices)}",
        "Rebalancing": rebalance,
        "Trading cost (bps)": f"{cost_bps:g}",
        "Portfolio value ($)": "" if portfolio_value is None else f"{portfolio_value:.2f}",
    }
    return pd.DataFrame({"value": rows}).rename_axis("setting")


def _metrics(result: PortfolioMetrics) -> pd.DataFrame:
    """Headline risk metrics plus one-day historical VaR and CVaR at 95% and 99%."""
    rows = {
        "Annualized return": result.annualized_return,
        "Annualized volatility": result.annualized_volatility,
        "Sharpe ratio": result.sharpe_ratio,
        "Sortino ratio": result.sortino_ratio,
        "Calmar ratio": result.calmar_ratio,
        "Maximum drawdown": result.max_drawdown,
        "Annual turnover": result.annual_turnover,
    }
    for confidence, row in tail_risk_summary(result.daily_returns).iterrows():
        rows[f"One-day VaR ({confidence:.0%})"] = row["var"]
        rows[f"One-day CVaR ({confidence:.0%})"] = row["cvar"]
    return pd.DataFrame({"value": rows}).rename_axis("metric")


def _holdings(
    prices: pd.DataFrame,
    weights: Sequence[float],
    rebalance: str,
    cost_bps: float,
    portfolio_value: float | None,
) -> pd.DataFrame:
    """Weight, last price, value, and share of risk per holding (plus trading costs)."""
    shares = rebalanced_risk_contributions(to_returns(prices), weights, rebalance, cost_bps)
    weight = pd.Series(list(weights), index=prices.columns).reindex(shares.index, fill_value=0.0)
    table = pd.DataFrame(
        {
            "weight": weight,
            "last_price": prices.iloc[-1].reindex(shares.index),
            "risk_share": shares,
        }
    )
    if portfolio_value is not None:
        table.insert(2, "value", weight * portfolio_value)
    return table.rename_axis("holding")


def report_tables(
    prices: pd.DataFrame,
    weights: Sequence[float],
    rebalance: str = "daily",
    cost_bps: float = 0.0,
    portfolio_value: float | None = None,
    benchmark: BenchmarkStatistics | None = None,
) -> dict[str, pd.DataFrame]:
    """Tables for export, keyed ``settings``, ``metrics``, ``holdings``, (``benchmark``), ``daily``.

    ``holdings`` has a ``Trading costs`` row when ``cost_bps`` > 0 (see
    ``rebalanced_risk_contributions``) and a ``value`` column when
    ``portfolio_value`` is given. ``daily`` holds each date's net return,
    wealth (starting at 1.0), and drawdown.

    Raises:
        ValueError: on inputs ``analyze_portfolio`` or
            ``rebalanced_risk_contributions`` rejects.
    """
    result = analyze_portfolio(prices, weights, rebalance=rebalance, cost_bps=cost_bps)
    daily = result.daily_returns
    tables = {
        "settings": _settings(prices, rebalance, cost_bps, portfolio_value),
        "metrics": _metrics(result),
        "holdings": _holdings(prices, weights, rebalance, cost_bps, portfolio_value),
    }
    if benchmark is not None:
        tables["benchmark"] = pd.DataFrame({"value": asdict(benchmark)}).rename_axis("statistic")
    tables["daily"] = pd.DataFrame(
        {
            "return": daily,
            "wealth": cumulative_wealth(daily).reindex(daily.index),
            "drawdown": drawdown_series(daily),
        }
    ).rename_axis("date")
    return tables


def report_csv_zip(tables: Mapping[str, pd.DataFrame]) -> bytes:
    """A zip archive with one ``<name>.csv`` file per table; dates as YYYY-MM-DD."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, table in tables.items():
            archive.writestr(f"{name}.csv", table.to_csv(date_format="%Y-%m-%d"))
    return buffer.getvalue()


def _number(value: float, ratio: bool) -> str:
    """A ratio with two decimals or a fraction as a percent; NaN shows as N/A."""
    if pd.isna(value):
        return "N/A"
    return f"{value:.2f}" if ratio else f"{value:.2%}"


def _display(name: str, table: pd.DataFrame) -> pd.DataFrame:
    """A copy of ``table`` formatted as text for the HTML page."""
    if name == "metrics":
        return table.assign(
            value=[_number(v, m in RATIO_METRICS) for m, v in table["value"].items()]
        )
    if name == "benchmark":
        values = [_number(v, s in BENCHMARK_RATIOS) for s, v in table["value"].items()]
        return table.assign(value=values)
    if name == "holdings":
        shown = table.assign(
            weight=[_number(v, False) for v in table["weight"]],
            risk_share=[_number(v, False) for v in table["risk_share"]],
            last_price=["" if pd.isna(v) else f"{v:,.2f}" for v in table["last_price"]],
        )
        if "value" in shown:
            shown = shown.assign(value=[f"${v:,.2f}" for v in table["value"]])
        return shown
    return table


def report_html(
    tables: Mapping[str, pd.DataFrame], charts: Mapping[str, str], generated_on: date
) -> str:
    """One HTML page with every table except ``daily``, then the given charts.

    ``charts`` maps a title to an HTML snippet (such as Plotly's
    ``to_html(full_html=False)``); snippets are trusted and inserted as is.
    Table cells and titles are escaped.
    """
    sections = [
        f"<h2>{escape(name.capitalize())}</h2>\n{_display(name, table).to_html(escape=True)}"
        for name, table in tables.items()
        if name != "daily"
    ]
    sections += [f"<h2>{escape(title)}</h2>\n{snippet}" for title, snippet in charts.items()]
    body = "\n".join(sections)
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        f"<title>{escape(REPORT_TITLE)}</title>"
        "<style>body{font-family:sans-serif;margin:2rem;max-width:960px}"
        "table{border-collapse:collapse;margin-bottom:1rem}"
        "th,td{border:1px solid #ccc;padding:4px 10px;text-align:right}</style></head>"
        f"<body><h1>{escape(REPORT_TITLE)}</h1>"
        f"<p>Generated {generated_on:%B %d, %Y}. Historical analysis for education only; "
        "not investment advice. Daily figures are in the CSV export.</p>\n"
        f"{body}\n</body></html>\n"
    )
