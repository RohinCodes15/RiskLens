"""Streamlit portfolio analysis using daily adjusted prices and shared analytics."""

from datetime import date, timedelta
from math import isfinite

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from risklens.analytics import (
    analyze_portfolio, compare_to_benchmark, correlation_matrix, drawdown_series,
    effective_holdings, herfindahl_index, simulate_portfolio,
    HISTORICAL_SCENARIOS, custom_scenario, stress_test,
    cumulative_wealth, portfolio_returns,
)
from risklens.analytics.simulation import (
    DEFAULT_SEED, MAX_HORIZON_DAYS, MAX_PATHS, MIN_HORIZON_DAYS, MIN_PATHS,
)
from risklens.data import DataFetchError, fetch_benchmark_prices, fetch_prices, to_returns
from risklens.validation import validate_tickers, validate_weights


def render_stress_test(analysis: dict) -> None:
    """Display historical stress outcomes as fractions and normalized wealth."""
    st.divider()
    st.subheader("Historical Stress Testing")
    st.caption("Hypothetical replay: current fixed weights applied to past adjusted prices, not your actual historical holdings. Not a prediction.")
    names = [scenario.name for scenario in HISTORICAL_SCENARIOS]
    selected = st.selectbox("Historical scenario", names + ["Custom date range"])
    if selected == "Custom date range":
        start_date = st.date_input("Scenario start date", analysis["prices"].index.min().date(), min_value=date(1900, 1, 1), max_value=date.today())
        end_date = st.date_input("Scenario end date (inclusive)", analysis["prices"].index.max().date(), min_value=date(1900, 1, 1), max_value=date.today())
        try:
            scenario = custom_scenario(start_date, end_date)
        except ValueError as exc:
            st.warning(str(exc))
            return
    else:
        scenario = HISTORICAL_SCENARIOS[names.index(selected)]
        st.caption(scenario.description)
    st.caption(f"Requested window: {scenario.start:%b %d, %Y} – {scenario.end:%b %d, %Y} (inclusive).")
    request = (scenario.name, scenario.start, scenario.end)
    if st.button("Run historical stress test"):
        analysis.pop("stress", None)
        try:
            with st.spinner("Loading scenario prices and replaying historical returns…"):
                history = fetch_prices(list(analysis["prices"].columns), scenario.start.date(), scenario.end.date() + timedelta(days=1))
                result = stress_test(history, analysis["weights"], scenario)
                curve = None
                if result.available:
                    window = history.loc[result.first_date:result.last_date]
                    daily = portfolio_returns(to_returns(window), analysis["weights"])
                    curve = cumulative_wealth(daily).reindex(window.index, fill_value=1.0)
                analysis["stress"] = (request, result, curve)
        except (ValueError, DataFetchError, NotImplementedError) as exc:
            st.warning(f"Scenario unavailable: {exc}")
    saved = analysis.get("stress")
    if saved is None or saved[0] != request:
        st.info("Run the selected scenario to check availability. Every stock needs history spanning the window and at least three common price dates. Recently listed stocks may make older scenarios unavailable; no prices are invented or filled.")
        return
    _, result, curve = saved
    if not result.available:
        st.warning(f"Scenario unavailable — {result.scenario.name}. {result.reason}")
        st.caption("Try a later custom start date or a portfolio whose stocks traded throughout the window. At least three common price dates are required.")
        return
    st.caption(f"Actual price dates: {result.first_date:%b %d, %Y} – {result.last_date:%b %d, %Y} · {result.n_returns:,} return observations.")


def render_simulation(analysis: dict) -> None:
    """Display hypothetical wealth multiples and cumulative terminal return fractions."""
    st.divider()
    st.subheader("Monte Carlo · hypothetical simulations")
    st.caption("Scenarios based on historical returns, not predictions or guarantees.")
    with st.form("simulation_request"):
        horizon = st.number_input("Forecast horizon (trading days)", MIN_HORIZON_DAYS, MAX_HORIZON_DAYS, 252, help="Simulation steps; future dates are weekdays, including exchange holidays.")
        paths = st.number_input("Simulation count", MIN_PATHS, MAX_PATHS, MIN_PATHS, step=1000)
        seed = st.number_input("Random seed", 0, 2**32 - 1, DEFAULT_SEED, help="Identical history and settings reproduce the same scenarios.")
        run = st.form_submit_button("Run hypothetical simulations")
    if run:
        analysis.pop("simulation", None)
        try:
            with st.spinner("Generating hypothetical portfolio scenarios…"):
                result = simulate_portfolio(analysis["daily_returns"], horizon_days=horizon, n_paths=paths, seed=seed)
                analysis["simulation"] = (result, horizon, paths, seed)
        except (ValueError, NotImplementedError, MemoryError) as exc:
            st.error(f"Unable to simulate this portfolio. {exc or 'Try fewer simulations or a shorter horizon.'}")
    saved = analysis.get("simulation")
    if saved is None:
        if not run:
            st.info("Choose simulation settings and run to explore hypothetical outcomes.")
        return
    result, used_horizon, used_paths, used_seed = saved
    bands = result.percentile_paths
    st.caption(f"Displayed run: {used_horizon:,} trading days · {used_paths:,} simulations · seed {used_seed}. Run again to apply changes.")
    median_column, loss_column = st.columns(2)
    with median_column.container(border=True):
        st.metric("Hypothetical terminal median return", f"{bands['median'].iloc[-1] - 1.0:.2%}", help="Ending median wealth from the simulation API, displayed as cumulative return from the starting wealth of 1.0.")
    with loss_column.container(border=True):
        st.metric("Hypothetical probability of loss", f"{result.loss_probability:.2%}", help="Share of simulated paths ending below their starting wealth; not a real-world loss forecast.")
    fan = go.Figure()
    for lower, upper, label, color in (
        ("p5", "p95", "5th–95th percentiles", "rgba(42,157,143,0.15)"),
        ("p25", "p75", "25th–75th percentiles", "rgba(42,157,143,0.35)"),
    ):
        fan.add_trace(go.Scatter(x=bands.index, y=bands[lower], mode="lines", line_width=0, showlegend=False, name=lower, hovertemplate="%{x|%b %d, %Y}<br>Wealth: %{y:.3f}×<extra>%{fullData.name}</extra>"))
        fan.add_trace(go.Scatter(x=bands.index, y=bands[upper], mode="lines", line_width=0, fill="tonexty", fillcolor=color, name=label, hovertemplate="%{x|%b %d, %Y}<br>Upper wealth: %{y:.3f}×<extra>%{fullData.name}</extra>"))
    fan.add_trace(go.Scatter(x=bands.index, y=bands["median"], mode="lines", line={"color": "#264653", "width": 3}, name="Median", hovertemplate="%{x|%b %d, %Y}<br>Median wealth: %{y:.3f}×<extra></extra>"))
    fan.update_layout(template="plotly_white", title="Hypothetical portfolio wealth scenarios", hovermode="x unified", height=450, legend_title_text="Simulated percentiles")
    fan.update_xaxes(title_text="Simulation date", rangeslider_visible=True)
    fan.update_yaxes(title_text="Wealth multiple (starting wealth = 1.0)", tickformat=".2f", ticksuffix="×")
    fan.add_hline(y=1.0, line_dash="dot", line_color="gray")
    st.plotly_chart(fan, key="simulation_chart")
    st.caption("Bands are pointwise percentiles across hypothetical paths, not confidence bounds or individual paths. The median line is not one simulated path.")
    st.caption("Assumes independent normally distributed daily log returns fitted to historical data. Short histories are unreliable; crashes, changing markets, fees, taxes and cash flows are not captured. Dates include weekdays without excluding exchange holidays.")


st.set_page_config(page_title="RiskLens Quant", page_icon="◈", layout="wide")

with st.sidebar:
    st.title("◈ RiskLens")
    st.caption("QUANT · PORTFOLIO ANALYTICS")
    st.divider()
    raw_tickers = st.text_input(
        "Stock tickers", "AAPL, MSFT",
        help="Separate tickers with commas or spaces; maximum 25.",
    )
    try:
        tickers = validate_tickers(raw_tickers)
    except ValueError as exc:
        tickers = []
        st.error(str(exc))

    with st.form("portfolio_request"):
        st.markdown("**Portfolio weights**")
        st.caption("Long-only allocation: percentages must total 100%.")
        weights_pct = []
        for index, ticker in enumerate(tickers):
            equal_weight = round(100 / len(tickers), 2)
            default_weight = (
                100 - equal_weight * index
                if index == len(tickers) - 1 else equal_weight
            )
            weights_pct.append(st.number_input(
                f"{ticker} weight (%)", min_value=0.0, max_value=100.0,
                value=default_weight, step=1.0, format="%.2f",
                key=f"weight:{','.join(tickers)}:{ticker}",
            ))
        today = date.today()
        start = st.date_input(
            "Start date", today - timedelta(days=365),
            min_value=date(1900, 1, 1), max_value=today,
        )
        end = st.date_input(
            "End date (inclusive)", today,
            min_value=date(1900, 1, 1), max_value=today,
        )
        submitted = st.form_submit_button("Analyze portfolio", disabled=not tickers)

st.caption("PORTFOLIO INTELLIGENCE / OVERVIEW")
st.title("RiskLens Quant")
st.markdown("Explore your portfolio’s historical returns and risk.")

analysis = st.session_state.get("analysis")
if analysis is not None and list(analysis["prices"].columns) != tickers:
    st.session_state.pop("analysis", None)

if submitted:
    st.session_state.pop("analysis", None)
    try:
        try:
            weights = validate_weights([value / 100 for value in weights_pct], len(tickers))
        except ValueError as exc:
            raise ValueError(
                f"Use non-negative weights totaling 100%. Current total: {sum(weights_pct):.2f}%."
            ) from exc
        if start >= end:
            raise ValueError("Start date must be before end date.")
        with st.spinner("Loading prices and calculating portfolio metrics…"):
            # Yahoo's end date is exclusive; the UI includes the selected day.
            prices = fetch_prices(tickers, start, end + timedelta(days=1))
            if prices.empty:
                raise ValueError("No price history was returned. Try different tickers or dates.")
            result = analyze_portfolio(prices, weights)
            metrics = (
                result.annualized_return,
                result.annualized_volatility,
                result.sharpe_ratio,
                result.max_drawdown,
            )
            if not all(isfinite(value) for value in (metrics[0], metrics[1], metrics[3])):
                raise ValueError("Choose a longer period: these prices could not produce finite risk metrics.")
            st.session_state["analysis"] = {
                "prices": prices, "weights": weights, "metrics": metrics,
                "drawdown": drawdown_series(result.daily_returns),
                "daily_returns": result.daily_returns,
            }
            try:
                benchmark_prices = fetch_benchmark_prices(start, end + timedelta(days=1))
                st.session_state["analysis"]["benchmark"] = compare_to_benchmark(
                    prices, weights, benchmark_prices,
                )
            except (ValueError, DataFetchError, NotImplementedError) as exc:
                st.session_state["analysis"]["benchmark_error"] = str(exc)
    except NotImplementedError:
        st.error("Portfolio analytics is not ready. Save Claude’s completed analytics engine and try again.")
    except (ValueError, DataFetchError) as exc:
        st.error(f"Unable to analyze this portfolio. {exc}")

analysis = st.session_state.get("analysis")
if analysis is None:
    if not submitted:
        st.info("Choose tickers, set weights totaling 100%, and select Analyze portfolio.")
else:
    prices = analysis["prices"]
    st.subheader("Portfolio snapshot")
    allocation = " · ".join(
        f"{ticker} {weight:.2%}"
        for ticker, weight in zip(prices.columns, analysis["weights"])
    )
    st.caption(
        f"{allocation} | {prices.index.min():%b %d, %Y} – "
        f"{prices.index.max():%b %d, %Y} | {len(prices):,} price observations"
    )
    descriptions = (
        ("Annualized return", "Mean daily portfolio return × 252; arithmetic annualization.", ".2%"),
        ("Annualized volatility", "Sample daily standard deviation × √252.", ".2%"),
        ("Sharpe ratio", "Annualized excess return / volatility. Assumes a 0% annual risk-free rate.", ".2f"),
        ("Maximum drawdown", "Worst peak-to-trough decline, including initial wealth; negative means loss.", ".2%"),
    )
    for column, (label, help_text, spec), value in zip(
        st.columns(4), descriptions, analysis["metrics"],
    ):
        with column.container(border=True):
            st.metric(label, format(value, spec) if isfinite(value) else "N/A", help=help_text)
    if not isfinite(analysis["metrics"][2]):
        st.caption("Sharpe ratio is unavailable because portfolio volatility is zero or too close to zero.")
    st.caption("Fixed weights, rebalanced daily. Annualized figures use 252 trading days.")

    st.divider()
    st.subheader("Historical prices")
    fig = px.line(prices, labels={"index": "Date", "value": "Adjusted closing price", "variable": "Ticker"})
    fig.update_layout(
        title="Historical adjusted closing prices", template="plotly_white",
        hovermode="x unified", legend_title_text="Ticker", height=450,
    )
    fig.update_xaxes(title_text="Date", showgrid=False)
    fig.update_yaxes(title_text="Adjusted closing price", tickformat=".2f")
    fig.update_traces(
        line_width=2, hovertemplate="%{y:.2f}<extra>%{fullData.name}</extra>",
    )
    st.plotly_chart(fig)
    st.caption("Daily adjusted closing prices. Use tickers quoted in the same currency; no currency conversion is applied.")


    st.divider()
    st.subheader("Historical drawdown")
    drawdown = analysis.get("drawdown")
    if drawdown is None or drawdown.empty:
        st.info("No drawdown history is available. Select Analyze portfolio to reload it.")
    else:
        drawdown_fig = px.area(
            x=drawdown.index, y=drawdown,
            labels={"x": "Date", "y": "Drawdown"},
            color_discrete_sequence=["#e76f51"],
        )
        st.caption("Drawdown measures the decline below the portfolio’s prior peak.")
        show_slider = st.checkbox("Show date range slider", value=True)
        drawdown_fig.update_xaxes(rangeslider_visible=show_slider)
        drawdown_fig.update_yaxes(tickformat=".0%", title_text="Drawdown")
        drawdown_fig.update_traces(
            hovertemplate="%{x|%b %d, %Y}<br>%{y:.2%}<extra></extra>",
        )
        drawdown_fig.update_layout(hovermode="x unified", height=380, showlegend=False)
        drawdown_fig.add_hline(y=0, line_dash="dot", line_color="gray")
        st.plotly_chart(drawdown_fig, key="drawdown_chart")
        st.caption("Drag to zoom; double-click to reset.")
        st.caption("Initial wealth is included, so a first-day loss counts.")

    st.divider()
    st.subheader("Portfolio Diversification")
    st.caption("Allocation balance and how your stocks move together.")
    try:
        hhi = herfindahl_index(analysis["weights"])
        holdings = effective_holdings(analysis["weights"])
    except ValueError as exc:
        st.warning(f"Diversification metrics are unavailable. {exc}")
    else:
        concentration_column, holdings_column = st.columns(2)
        with concentration_column.container(border=True):
            st.metric(
                "HHI concentration", f"{hhi:.3f}",
                help="Sum of squared allocation weights, on a 0–1 scale. Lower means more evenly spread; 1 means one holding has all the weight.",
            )
        with holdings_column.container(border=True):
            st.metric(
                "Effective number of holdings", f"{holdings:.2f}",
                help="1 / HHI: the number of equally weighted holdings with the same allocation concentration. Zero-weight stocks do not count.",
            )
        st.caption("These measures describe allocation balance, not stock independence. Similar stocks can still carry similar risks.")

    if len(prices.columns) == 1:
        st.info("A single-stock portfolio has no cross-stock diversification. Add another stock to compare return correlations.")
    else:
        try:
            correlations = correlation_matrix(to_returns(prices))
        except ValueError as exc:
            st.warning(f"Stock-return correlation is unavailable. {exc}")
        else:
            st.markdown("**Daily stock-return correlation**")
            st.caption("Pearson correlation: +1 = move together, 0 = no linear relationship, −1 = move oppositely. Historical correlations can change.")
            if correlations.isna().any().any():
                st.info("Blank cells indicate undefined correlation, usually because a stock's returns are constant. They do not mean zero correlation.")
            correlation_fig = px.imshow(
                correlations, zmin=-1, zmax=1, color_continuous_scale="RdBu",
                labels={"x": "Stock", "y": "Stock", "color": "Correlation"},
                text_auto=".2f", aspect="equal",
            )
            correlation_fig.update_traces(
                hovertemplate="%{y} / %{x}<br>Daily return correlation: %{z:.2f}<extra></extra>",
                hoverongaps=False,
            )
            correlation_fig.update_layout(template="plotly_white", height=500)
            st.plotly_chart(correlation_fig, key="correlation_heatmap")
            st.caption("Based on adjusted daily returns over the selected period, using dates shared by every stock. Includes entered stocks with zero allocation; this is not a weighted portfolio correlation.")

    st.divider()
    st.subheader("Portfolio vs. S&P 500 (SPY)")
    st.caption("SPY is an ETF tracking the S&P 500. Both series use adjusted prices, including splits and dividends.")
    comparison = analysis.get("benchmark")
    if comparison is None:
        reason = analysis.get("benchmark_error", "Select Analyze portfolio to load SPY history.")
        st.warning(f"Benchmark comparison is unavailable. {reason}")
    else:
        # The analytics API returns growth from 1.0; display it as return from 0%.
        performance = (comparison - 1.0).rename(
            columns={"portfolio": "Portfolio", "benchmark": "S&P 500 (SPY)"},
        )
        ending_returns = performance.iloc[-1]
        st.caption(
            f"Shared period: {performance.index.min():%b %d, %Y} – "
            f"{performance.index.max():%b %d, %Y} · {len(performance):,} aligned price dates. "
            "Both curves start at 0% on the first shared date; no missing dates are filled."
        )
        if len(performance) == 2:
            st.info("Only one shared return interval is available. Choose a longer period for a more useful comparison.")
        benchmark_fig = px.line(performance, labels={"index": "Date", "value": "Cumulative return", "variable": "Investment"}, color_discrete_sequence=["#264653", "#e76f51"])
        benchmark_fig.update_layout(template="plotly_white", hovermode="x unified", height=450, legend_title_text="Investment")
        benchmark_fig.update_xaxes(title_text="Date", showgrid=False, rangeslider_visible=True)
        benchmark_fig.update_yaxes(title_text="Cumulative return", tickformat=".1%")
        benchmark_fig.update_traces(line_width=2, hovertemplate="%{x|%b %d, %Y}<br>%{y:.2%}<extra>%{fullData.name}</extra>")
        benchmark_fig.add_hline(y=0, line_dash="dot", line_color="gray")
        st.plotly_chart(benchmark_fig, key="benchmark_chart")
        portfolio_column, benchmark_column = st.columns(2)
        with portfolio_column.container(border=True):
            st.metric("Portfolio ending return", f"{ending_returns['Portfolio']:.2%}", help="Cumulative portfolio return over the shared dates; not annualized.")
        with benchmark_column.container(border=True):
            st.metric("SPY ending return", f"{ending_returns['S&P 500 (SPY)']:.2%}", help="Cumulative adjusted SPY return over the same shared dates; not annualized.")
        st.caption("Ending returns are cumulative over this shared period, not annualized. The portfolio uses fixed weights rebalanced on the shared trading dates. Shorter SPY coverage can make this period differ from the risk cards above. Past performance does not predict future returns.")

    render_simulation(analysis)
    render_stress_test(analysis)

st.divider()
st.caption(
    "Disclaimer: For educational and informational purposes only. "
    "This is not investment advice or a recommendation to buy or sell securities. "
    "Past performance does not guarantee future results. "
    "Historical estimates may understate future losses."
)
