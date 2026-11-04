"""Streamlit portfolio analysis using daily adjusted prices and shared analytics."""

from datetime import date, timedelta
from math import isfinite

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from risklens.analytics import (
    EWMA_LAMBDA,
    FACTOR_COLUMNS,
    HISTORICAL_SCENARIOS,
    KUPIEC_SIGNIFICANCE,
    MAX_FORECAST_DAYS,
    ROLLING_WINDOWS,
    SHOCK_PROXIES,
    VAR_BACKTEST_WINDOWS,
    EfficientFrontier,
    OptimizedPortfolio,
    ShockImpact,
    analyze_portfolio,
    benchmark_statistics,
    compare_portfolios,
    compare_to_benchmark,
    cornish_fisher_var,
    correlation_matrix,
    cumulative_wealth,
    custom_scenario,
    drawdown_series,
    effective_holdings,
    efficient_frontier,
    ewma_volatility,
    factor_exposure,
    fit_garch,
    frontier_point_within_risk,
    garch_forecast,
    group_breakdown,
    herfindahl_index,
    horizon_volatility,
    max_sharpe_portfolio,
    min_volatility_portfolio,
    normal_var,
    portfolio_returns,
    risk_contributions,
    rolling_metrics,
    shock_impact,
    simulate_portfolio,
    stress_test,
    tail_risk_summary,
    trade_cost,
    trade_weights,
    var_backtest,
)
from risklens.analytics.simulation import (
    DEFAULT_SEED,
    MAX_HORIZON_DAYS,
    MAX_PATHS,
    MIN_HORIZON_DAYS,
    MIN_PATHS,
)
from risklens.data import (
    DataFetchError,
    fetch_benchmark_prices,
    fetch_classifications,
    fetch_factors,
    fetch_price_history,
    fetch_prices,
    to_returns,
)
from risklens.holdings import holdings_to_weights, parse_holdings_csv
from risklens.validation import MAX_COST_BPS, validate_tickers, validate_weights


def model_var(model: object, daily: pd.Series, confidence: float) -> float:
    """A VaR model's one-day loss, or NaN when the history is too short to fit it."""
    try:
        return model(daily, confidence)
    except ValueError:  # the returns were already validated; only the sample size can fail
        return float("nan")


def render_tail_risk(analysis: dict) -> None:
    """Show backend one-day loss fractions and observed daily return fractions."""
    st.divider()
    st.subheader("Tail Risk")
    confidence = st.selectbox(
        "Tail risk confidence",
        [0.95, 0.99],
        format_func=lambda value: f"{value:.0%}",
        help="Historical one-day loss threshold at the selected confidence; not a guarantee.",
    )
    daily = analysis.get("daily_returns")
    if daily is None:
        st.info("Select Analyze portfolio to load historical daily returns.")
        return
    try:
        summary = tail_risk_summary(daily, (confidence,)).loc[confidence]
    except (ValueError, NotImplementedError) as exc:
        st.warning(f"Tail risk is unavailable. {exc}")
        return
    portfolio_value = analysis.get("portfolio_value")
    estimates = (
        (
            "One-day VaR",
            summary["var"],
            "Historical Value at Risk: positive values represent losses; negative values mean the threshold was a gain.",
        ),
        (
            "One-day CVaR",
            summary["cvar"],
            "Conditional VaR / Expected Shortfall: average loss among observations at or below the VaR return cutoff, including ties.",
        ),
        (
            "Normal VaR",
            model_var(normal_var, daily, confidence),
            "Parametric VaR: the one-day loss at this confidence if daily returns were normal with this history's mean and volatility.",
        ),
        (
            "Cornish-Fisher VaR",
            model_var(cornish_fisher_var, daily, confidence),
            "Normal VaR adjusted for this history's skewness and kurtosis (Cornish-Fisher). Negative skew raises it; fat tails raise it at 99% but can lower it at 95%. Equals Normal VaR when one extreme day puts the adjustment outside its valid range; N/A with fewer than 4 returns.",
        ),
    )
    for column, (label, loss, help_text) in zip(st.columns(4), estimates, strict=True):
        with column.container(border=True):
            st.metric(
                label,
                f"{loss:.2%}" if isfinite(loss) else "N/A",
                delta=dollar_change(-loss, portfolio_value),
                help=help_text,
            )
    in_dollars = (
        f" Dollar amounts are the same changes on your ${portfolio_value:,.2f} portfolio."
        if portfolio_value is not None
        else ""
    )
    st.caption(
        f"{confidence:.0%} confidence · {len(daily):,} observed daily returns. Positive card values mean losses; negative values mean gains. Figures are one-day estimates, not annualized. Historical VaR and CVaR read the observed returns; Normal and Cornish-Fisher VaR fit a distribution to them.{in_dollars}"
    )
    if not summary["sufficient_sample"]:
        st.warning(
            "Small historical sample: the selected tail contains less than one full expected observation. These estimates are fragile; use a longer history, especially at 99% confidence."
        )
    histogram = px.histogram(
        x=daily,
        labels={"x": "Historical daily portfolio return", "y": "Trading-day count"},
        color_discrete_sequence=["#264653"],
    )
    histogram.update_layout(
        template="plotly_white",
        title="Actual historical daily returns",
        height=400,
        showlegend=False,
        bargap=0.05,
    )
    histogram.update_xaxes(tickformat=".1%")
    histogram.update_yaxes(title_text="Trading-day count", rangemode="tozero")
    histogram.add_vline(
        x=-summary["var"],
        line_color="#e76f51",
        line_dash="dash",
        annotation_text=f"{confidence:.0%} VaR return cutoff",
        annotation_position="top left",
    )
    st.plotly_chart(histogram, key="tail_risk_histogram", width="stretch")
    st.caption(
        "CVaR measures average loss in the worst historical tail beyond the marked return cutoff. Historical estimates can understate future losses; VaR is not a maximum possible loss."
    )
    render_var_backtest(daily, confidence)


def render_benchmark_ratios(analysis: dict) -> None:
    """Information ratio and up/down capture against SPY on the shared daily returns."""
    stats = analysis.get("benchmark_stats")
    if stats is None:
        reason = analysis.get("benchmark_error", "Select Analyze portfolio to compute them.")
        st.info(f"Information ratio and capture are unavailable. {reason}")
        return
    ratios = (
        (
            "Information ratio",
            stats.information_ratio,
            ".2f",
            "Annual return above SPY ÷ tracking error: excess return per unit of risk taken "
            "relative to SPY. N/A when the portfolio tracks SPY exactly.",
        ),
        (
            "Upside capture",
            stats.upside_capture,
            ".0%",
            "Geometric mean daily return on days SPY rose, as a share of SPY's. Above 100% "
            "means the portfolio gained more than SPY on those days.",
        ),
        (
            "Downside capture",
            stats.downside_capture,
            ".0%",
            "Geometric mean daily return on days SPY fell, as a share of SPY's. Below 100% "
            "means it lost less than SPY on those days; lower is better.",
        ),
    )
    for column, (label, value, spec, help_text) in zip(st.columns(3), ratios, strict=True):
        with column.container(border=True):
            st.metric(label, format(value, spec) if isfinite(value) else "N/A", help=help_text)
    st.caption(
        "From daily returns on the shared dates, net of the selected rebalancing and trading "
        "costs. Capture compares average returns on SPY's up days and down days separately."
    )


VAR_METHOD_LABELS = {
    "historical": "Historical",
    "normal": "Normal",
    "cornish_fisher": "Cornish-Fisher",
}
DEFAULT_BACKTEST_WINDOW = 126  # half a year, so the default one-year period has test days
# Below this many expected tail days per window, historical VaR is mostly noise.
MIN_WINDOW_TAIL_DAYS = 5


def backtest_result(row: pd.Series) -> str:
    """Plain-language Kupiec verdict for one VaR method's backtest row."""
    if not row["sufficient_sample"]:
        return "Too few test days to judge"
    if row["p_value"] >= KUPIEC_SIGNIFICANCE:
        return "Plausible"
    if row["breaches"] > row["expected_breaches"]:
        return "Too many breaches: VaR too low"
    return "Too few breaches: VaR too high"


def render_var_backtest(daily: pd.Series, confidence: float) -> None:
    """Score each VaR method on the days after its estimation window."""
    st.markdown("**VaR backtest**")
    window = st.selectbox(
        "VaR estimation window",
        VAR_BACKTEST_WINDOWS,
        index=VAR_BACKTEST_WINDOWS.index(DEFAULT_BACKTEST_WINDOW),
        format_func=lambda days: f"{days} trading days",
        help="Each day's VaR is estimated from this many earlier returns, then compared "
        "with that day's actual return.",
    )
    if len(daily) <= window:
        st.info(
            f"A {window}-day backtest needs more than {window} daily returns; this period "
            f"has {len(daily):,}. Choose an earlier start date or a shorter window."
        )
        return
    try:
        backtest = var_backtest(daily, window, confidence)
    except ValueError as exc:
        st.warning(f"The VaR backtest is unavailable. {exc}")
        return
    table = pd.DataFrame(
        {
            "Days tested": backtest["days"],
            "Breaches": backtest["breaches"],
            "Expected": backtest["expected_breaches"],
            "Breach rate": backtest["breach_rate"],
            "Kupiec p-value": backtest["p_value"],
            "Result": backtest.apply(backtest_result, axis=1),
        }
    ).rename(index=VAR_METHOD_LABELS)
    st.table(
        table.rename_axis("VaR method").style.format(
            {"Expected": "{:.1f}", "Breach rate": "{:.2%}", "Kupiec p-value": "{:.3f}"}
        )
    )
    st.caption(
        f"A breach is a day whose loss exceeded that day's {confidence:.0%} VaR, estimated "
        f"only from the {window} returns before it. A correct VaR is breached on about "
        f"{1 - confidence:.0%} of days; the Kupiec test flags breach counts that are "
        f"implausibly high or low (p-value below {KUPIEC_SIGNIFICANCE:.0%}). With few test "
        "days the test has little power, especially at 99%."
    )
    tail_days = window * (1 - confidence)
    if tail_days < MIN_WINDOW_TAIL_DAYS:
        st.caption(
            f"A {window}-day window holds only about {tail_days:.1f} days beyond the "
            f"{confidence:.0%} cutoff, so historical VaR from it is noisy and tends to be "
            "breached too often. A longer window gives it a fairer test."
        )


REBALANCE_CHOICES = {
    "Daily": "daily",
    "Monthly": "monthly",
    "Quarterly": "quarterly",
    "Annually": "annual",
    "Never (buy and hold)": "never",
}
REBALANCE_DESCRIPTIONS = {
    "daily": "Weights reset to target every trading day",
    "monthly": "Weights drift with prices and reset to target each month",
    "quarterly": "Weights drift with prices and reset to target each quarter",
    "annual": "Weights drift with prices and reset to target each year",
    "never": "Buy and hold: weights drift with prices and are never reset",
}


HOLDING_INPUTS = {
    "Percent weights": "weight",
    "Shares": "shares",
    "Dollar values": "value",
}
HOLDING_CAPTIONS = {
    "weight": "Long-only allocation: percentages must total 100%.",
    "shares": "Shares held in each stock, valued at its last close in the selected period.",
    "value": "Market value of each holding in dollars.",
}


def holding_inputs(tickers: list[str], kind: str) -> list[float]:
    """Render one input per ticker: a percent weight, a share count, or a dollar value."""
    amounts = []
    for index, ticker in enumerate(tickers):
        key = f"{kind}:{','.join(tickers)}:{ticker}"
        if kind == "weight":
            equal_weight = round(100 / len(tickers), 2)
            default = 100 - equal_weight * index if index == len(tickers) - 1 else equal_weight
            amount = st.number_input(
                f"{ticker} weight (%)",
                min_value=0.0,
                max_value=100.0,
                value=default,
                step=1.0,
                format="%.2f",
                key=key,
            )
        elif kind == "shares":
            amount = st.number_input(
                f"{ticker} shares", min_value=0.0, value=0.0, step=1.0, format="%.4f", key=key
            )
        else:
            amount = st.number_input(
                f"{ticker} value ($)", min_value=0.0, value=0.0, step=100.0, format="%.2f", key=key
            )
        amounts.append(amount)
    return amounts


def plain_text(text: str) -> str:
    """Escape "$" in user-supplied text so Streamlit markdown does not read it as math."""
    return text.replace("$", "\\$")


def dollar_change(fraction: float, portfolio_value: float | None) -> str | None:
    """Signed whole-dollar change for a return fraction, or None without a portfolio value."""
    if portfolio_value is None or not isfinite(fraction):
        return None
    amount = round(fraction * portfolio_value)
    # st.metric colors a delta red with a down arrow when it starts with an ASCII "-".
    sign = "-" if amount < 0 else "+" if amount > 0 else ""
    return f"{sign}${abs(amount):,}"


def cost_text(cost_bps: float) -> str:
    """Describe the trading cost applied to rebalance trades, taxes always excluded."""
    if cost_bps == 0:
        return "trading costs and taxes excluded"
    return f"{cost_bps:g} bps trading cost per dollar traded; taxes excluded"


ROLLING_VIEWS = {
    "Volatility": ("volatility", "Annualized volatility", ".0%"),
    "Sharpe ratio": ("sharpe", "Annualized Sharpe ratio", ".2f"),
    "Drawdown": ("drawdown", "Drawdown from the window's peak", ".0%"),
}


def render_rolling(analysis: dict) -> None:
    """Chart one dated rolling metric over a trailing trading-day window."""
    st.divider()
    st.subheader("Rolling risk")
    window_column, metric_column = st.columns(2)
    window = window_column.selectbox(
        "Rolling window", ROLLING_WINDOWS, format_func=lambda days: f"{days} trading days"
    )
    view = metric_column.selectbox("Rolling metric", list(ROLLING_VIEWS))
    daily = analysis["daily_returns"]
    if len(daily) < window:
        st.info(
            f"A {window}-day window needs at least {window} daily returns; this period has {len(daily):,}. Choose a longer period or a shorter window."
        )
        return
    try:
        rolling = rolling_metrics(daily, window)
    except ValueError as exc:
        st.warning(f"Rolling risk is unavailable. {exc}")
        return
    column, axis_title, spec = ROLLING_VIEWS[view]
    series = rolling[column].dropna()
    rolling_fig = px.line(
        x=series.index,
        y=series,
        labels={"x": "Date", "y": axis_title},
        color_discrete_sequence=["#264653"],
    )
    rolling_fig.update_layout(
        template="plotly_white",
        title=f"{view} · trailing {window} trading days",
        hovermode="x unified",
        height=380,
        showlegend=False,
    )
    rolling_fig.update_yaxes(title_text=axis_title, tickformat=spec)
    rolling_fig.update_traces(
        line_width=2, hovertemplate=f"%{{x|%b %d, %Y}}<br>%{{y:{spec}}}<extra></extra>"
    )
    st.plotly_chart(rolling_fig, key="rolling_chart")
    st.caption(
        "Each date uses only the trailing window ending that day. Sharpe assumes a 0% risk-free rate and is blank when a window's volatility is zero. Drawdown is measured from the highest wealth inside the window."
    )


VOLATILITY_HORIZON_DAYS = 21  # about one month of trading days


def volatility_chart(ewma: pd.Series, garch: pd.Series | None) -> go.Figure:
    """Dated next-day volatility from EWMA, and from GARCH when it could be fitted."""
    lines = {f"EWMA (λ = {EWMA_LAMBDA})": ewma}
    if garch is not None:
        lines["GARCH(1,1)"] = garch
    frame = pd.DataFrame(lines).rename_axis("Date")
    figure = px.line(
        frame,
        labels={"Date": "Date", "value": "Annualized volatility", "variable": "Model"},
        color_discrete_sequence=["#264653", "#e76f51"],
    )
    figure.update_layout(
        template="plotly_white",
        title="Next-day volatility estimate on each date",
        hovermode="x unified",
        height=380,
        legend_title_text="Model",
    )
    figure.update_yaxes(tickformat=".0%")
    figure.update_traces(
        line_width=2, hovertemplate="%{x|%b %d, %Y}<br>%{y:.1%}<extra>%{fullData.name}</extra>"
    )
    return figure


def render_volatility_forecast(analysis: dict) -> None:
    """Compare historical volatility with RiskMetrics EWMA and GARCH(1,1) forecasts."""
    st.divider()
    st.subheader("Volatility forecast")
    daily = analysis["daily_returns"]
    horizon = st.number_input(
        "Volatility forecast horizon (trading days)",
        min_value=1,
        max_value=MAX_FORECAST_DAYS,
        value=VOLATILITY_HORIZON_DAYS,
        help="Days ahead the GARCH forecast averages over; EWMA and historical volatility "
        "are the same for every day.",
    )
    try:
        ewma = ewma_volatility(daily)
    except ValueError as exc:
        st.info(f"Volatility forecasts are unavailable. {exc}")
        return
    try:
        garch, garch_error = fit_garch(daily), None
    except ValueError as exc:
        garch, garch_error = None, str(exc)
    historical_column, ewma_column, garch_column, long_run_column = st.columns(4)
    with historical_column.container(border=True):
        st.metric(
            "Historical volatility",
            f"{analysis['metrics'][1]:.2%}",
            help="Sample daily standard deviation × √252 over the whole period.",
        )
    with ewma_column.container(border=True):
        st.metric(
            "EWMA volatility (next day)",
            f"{ewma.iloc[-1]:.2%}",
            help=f"RiskMetrics exponentially weighted volatility, λ = {EWMA_LAMBDA}: recent "
            "days count most. Its forecast is the same for every future day.",
        )
    if garch is None:
        st.info(f"The GARCH(1,1) forecast is unavailable. {garch_error}")
    else:
        forecast = garch_forecast(garch, horizon)
        with garch_column.container(border=True):
            st.metric(
                f"GARCH volatility (next {horizon} days)",
                f"{horizon_volatility(forecast):.2%}",
                help="Square root of the average forecast daily variance over the horizon, "
                "annualized.",
            )
        with long_run_column.container(border=True):
            st.metric(
                "GARCH long-run volatility",
                f"{garch.long_run_volatility:.2%}",
                help="The level the GARCH forecast moves back to over long horizons.",
            )
    st.plotly_chart(
        volatility_chart(ewma, None if garch is None else garch.conditional_volatility),
        key="volatility_chart",
    )
    fitted = (
        ""
        if garch is None
        else f" GARCH fit on {garch.observations:,} daily returns: α = {garch.alpha:.3f}, "
        f"β = {garch.beta:.3f}, persistence α + β = {garch.persistence:.3f}; the closer "
        "persistence is to 1, the slower the forecast moves toward its long-run level."
    )
    st.caption(
        "Each line's value on a date uses returns up to that date and estimates the next "
        f"day's volatility, annualized.{fitted} Returns follow your rebalancing and trading "
        "cost. Estimates from past returns, not predictions."
    )


def render_risk_attribution(analysis: dict) -> None:
    """Compare each stock's share of portfolio variance with its allocation weight."""
    st.markdown("**Risk attribution**")
    try:
        shares = risk_contributions(to_returns(analysis["prices"]), analysis["weights"])
    except ValueError as exc:
        st.info(f"Risk attribution is unavailable. {exc}")
        return
    attribution = pd.DataFrame(
        {"Allocation weight": analysis["weights"], "Share of portfolio risk": shares.to_numpy()},
        index=shares.index,
    )
    attribution_fig = px.bar(
        attribution,
        barmode="group",
        labels={"index": "Ticker", "value": "Share of portfolio", "variable": "Measure"},
        color_discrete_sequence=["#8ab17d", "#e76f51"],
    )
    attribution_fig.update_layout(template="plotly_white", height=380, legend_title_text="Measure")
    attribution_fig.update_yaxes(tickformat=".0%")
    attribution_fig.update_traces(hovertemplate="%{x}<br>%{y:.2%}<extra>%{fullData.name}</extra>")
    st.plotly_chart(attribution_fig, key="risk_attribution_chart")
    st.caption(
        "Share of portfolio risk = weight × the stock's covariance with the portfolio ÷ portfolio variance; shares sum to 100%. A stock can carry more risk than its weight, and a negative share means it reduces total risk."
    )


FACTOR_NAMES = {
    "Mkt-RF": "Market",
    "SMB": "Size (small − big)",
    "HML": "Value (high − low)",
    "Mom": "Momentum",
}


def render_risk_sources(analysis: dict) -> None:
    """Show Fama-French factor betas and the sector/country split of weight and risk."""
    st.divider()
    st.subheader("Where risk comes from")
    st.caption(
        "Factor data comes from the Kenneth R. French Data Library; sectors and countries from Yahoo Finance profiles."
    )
    if st.button("Load factor and sector data"):
        analysis.pop("risk_sources_error", None)
        prices = analysis["prices"]
        try:
            with st.spinner("Downloading factor returns and company profiles…"):
                factors = fetch_factors(
                    prices.index.min().date(), prices.index.max().date() + timedelta(days=1)
                )
                labels = fetch_classifications(list(prices.columns))
            analysis["risk_sources"] = (factors, labels)
        except (ValueError, DataFetchError) as exc:
            analysis["risk_sources_error"] = str(exc)
    if "risk_sources_error" in analysis:
        st.warning(f"Factor and sector data are unavailable. {analysis['risk_sources_error']}")
        return
    if "risk_sources" not in analysis:
        st.info("Select Load factor and sector data to see factor betas and sector exposure.")
        return
    factors, labels = analysis["risk_sources"]
    render_factor_exposure(analysis["daily_returns"], factors)
    returns = to_returns(analysis["prices"])
    for column, title in (("sector", "Sector"), ("country", "Country")):
        try:
            table = group_breakdown(returns, analysis["weights"], labels[column].rename(title))
        except ValueError as exc:
            st.info(f"{title} breakdown is unavailable. {exc}")
            continue
        st.markdown(f"**{title} breakdown**")
        st.dataframe(
            table.rename(columns={"weight": "Weight", "risk_share": "Share of risk"}).style.format(
                "{:.2%}"
            ),
            key=f"{column}_breakdown",
        )
    st.caption(
        "Share of risk sums each holding's share of portfolio variance, as in Risk attribution above. Funds have no Yahoo sector and are grouped by type (e.g. ETF)."
    )


def render_factor_exposure(daily: pd.Series, factors: pd.DataFrame) -> None:
    """Show Fama-French-Carhart betas, annualized alpha, and R² for the portfolio."""
    st.markdown("**Fama-French factor exposure**")
    try:
        exposure = factor_exposure(daily, factors)
    except ValueError as exc:
        st.info(f"Factor exposure is unavailable. {exc}")
        return
    columns = st.columns(len(FACTOR_COLUMNS) + 2)
    for column, factor in zip(columns, FACTOR_COLUMNS, strict=False):
        with column.container(border=True):
            st.metric(f"{FACTOR_NAMES[factor]} beta", f"{exposure.betas[factor]:.2f}")
    with columns[-2].container(border=True):
        st.metric(
            "Alpha (annualized)",
            f"{exposure.alpha:.2%}",
            help="Return not explained by the factors: daily regression intercept × 252.",
        )
    with columns[-1].container(border=True):
        st.metric(
            "R²",
            f"{exposure.r_squared:.2f}",
            help="Share of daily excess-return variance the four factors explain.",
        )
    st.caption(
        f"OLS of daily portfolio returns minus the risk-free rate on the market, size, value and momentum factors, over {exposure.observations} days ({exposure.first_date:%b %d, %Y} – {exposure.last_date:%b %d, %Y}). The factor library is published with a lag, so recent days may be left out."
    )


def render_optimization(analysis: dict) -> None:
    """Compare the current weights with long-only minimum-volatility and maximum-Sharpe weights."""
    st.divider()
    st.subheader("Portfolio optimization")
    st.caption(
        "Long-only, fully invested weights fit to the selected history. Assumes a 0% risk-free rate."
    )
    prices = analysis["prices"]
    if len(prices.columns) == 1:
        st.info("Optimization needs at least two stocks. Add another stock to compare allocations.")
        return
    if st.button("Optimize portfolio"):
        analysis.pop("optimization", None)
        analysis.pop("optimization_error", None)
        analysis["optimization_errors"] = {}
        results = []
        with st.spinner("Solving optimized portfolios…"):
            for label, optimizer in (
                ("Minimum volatility", min_volatility_portfolio),
                ("Maximum Sharpe", max_sharpe_portfolio),
                # Reuse the minimum-volatility result; None makes the frontier solve it.
                ("Efficient frontier", lambda p: efficient_frontier(p, min_volatility=results[0])),
            ):
                try:
                    results.append(optimizer(prices))
                except ValueError as exc:
                    results.append(None)
                    analysis["optimization_errors"][label] = str(exc)
        analysis["optimization"] = tuple(results)
    for label, message in analysis.get("optimization_errors", {}).items():
        st.warning(f"{label} is unavailable. {message}")
    if "optimization" not in analysis:
        st.info("Select Optimize portfolio to compare your weights with optimized allocations.")
        return
    if any(result is not None for result in analysis["optimization"]):
        render_optimization_results(analysis)


def render_optimization_results(analysis: dict) -> None:
    """Show successful allocations and frontier with annualized fractional rates."""
    min_vol, max_sharpe, frontier = analysis["optimization"]
    current_return, current_volatility, current_sharpe = analysis.get(
        "optimization_baseline", analysis["metrics"][:3]
    )
    allocations = {
        "Current": [*analysis["weights"], current_return, current_volatility, current_sharpe],
    }
    for label, result in (("Minimum volatility", min_vol), ("Maximum Sharpe", max_sharpe)):
        if result is not None:
            allocations[label] = [
                *result.weights,
                result.expected_return,
                result.volatility,
                result.sharpe_ratio,
            ]
    table = pd.DataFrame(
        allocations,
        index=[
            *(f"{ticker} weight" for ticker in analysis["prices"].columns),
            "Annualized return",
            "Annualized volatility",
            "Sharpe ratio",
        ],
    )
    st.dataframe(
        table.style.format("{:.2%}").format("{:.2f}", subset=pd.IndexSlice[["Sharpe ratio"], :]),
        key="optimization_table",
    )
    if any(
        result is not None and result.diagnostics.singular_covariance
        for result in (min_vol, max_sharpe)
    ):
        st.warning(
            "The covariance matrix is singular (duplicate or constant-price stocks), so these weights are not unique."
        )
    st.caption(
        "In-sample results: weights are fit to the same history used to score them, so these figures are optimistic and not a forecast. Maximum-Sharpe weights are especially sensitive to the chosen period."
    )
    if "optimization_baseline" in analysis:
        st.caption(
            "Every column, including Current, assumes daily rebalancing with no trading costs, "
            "so it can differ from the risk cards above."
        )
    if frontier is not None:
        render_frontier(
            frontier,
            min_vol,
            max_sharpe,
            current_return,
            current_volatility,
            list(analysis["prices"].columns),
        )


def render_frontier(
    frontier: EfficientFrontier,
    min_vol: OptimizedPortfolio | None,
    max_sharpe: OptimizedPortfolio | None,
    current_return: float,
    current_volatility: float,
    tickers: list[str],
) -> None:
    """Plot the efficient frontier with the current, optimized, and same-risk portfolios."""
    points = frontier.points
    frontier_fig = go.Figure(
        go.Scatter(
            x=points["volatility"],
            y=points["expected_return"],
            mode="lines+markers",
            name="Efficient frontier",
            line={"color": "#264653", "width": 2},
            marker={"size": 5},
        )
    )
    markers = [
        ("Current", current_volatility, current_return, "#e76f51", "x"),
    ]
    for label, result, color, symbol in (
        ("Minimum volatility", min_vol, "#2a9d8f", "diamond"),
        ("Maximum Sharpe", max_sharpe, "#e9c46a", "star"),
    ):
        if result is not None:
            markers.append((label, result.volatility, result.expected_return, color, symbol))
    suggested = frontier_point_within_risk(frontier, current_volatility)
    if suggested is not None:
        point = points.loc[suggested]
        markers.append(
            (
                "Best return at your risk",
                point["volatility"],
                point["expected_return"],
                "#8ab17d",
                "circle-open",
            )
        )
    for name, volatility, expected_return, color, symbol in markers:
        frontier_fig.add_trace(
            go.Scatter(
                x=[volatility],
                y=[expected_return],
                mode="markers",
                name=name,
                marker={"color": color, "symbol": symbol, "size": 14, "line": {"width": 2}},
            )
        )
    frontier_fig.update_layout(
        template="plotly_white",
        title="Efficient frontier (in-sample)",
        height=450,
        legend_title_text="Portfolio",
    )
    frontier_fig.update_xaxes(title_text="Annualized volatility", tickformat=".0%")
    frontier_fig.update_yaxes(title_text="Annualized expected return", tickformat=".0%")
    frontier_fig.update_traces(
        hovertemplate="Volatility %{x:.2%}<br>Return %{y:.2%}<extra>%{fullData.name}</extra>"
    )
    st.plotly_chart(frontier_fig, key="frontier_chart")
    if suggested is None:
        st.info(
            "Every frontier portfolio is riskier than your current weights, so no same-risk alternative is shown."
        )
    else:
        weights = " · ".join(
            f"{ticker} {weight:.2%}"
            for ticker, weight in zip(tickers, frontier.weights.loc[suggested], strict=True)
        )
        st.caption(
            f"Best return at no more than your current volatility: {points.loc[suggested, 'expected_return']:.2%} return at {points.loc[suggested, 'volatility']:.2%} volatility with {weights}."
        )
    if frontier.infeasible_targets:
        st.caption(
            f"{frontier.infeasible_targets} frontier target(s) could not be solved and are omitted."
        )


def render_stress_test(analysis: dict) -> None:
    """Display historical stress outcomes as fractions and normalized wealth."""
    st.divider()
    st.subheader("Historical Stress Testing")
    st.caption(
        "Hypothetical replay: current target weights and rebalancing applied to past adjusted prices, not your actual historical holdings. Not a prediction."
    )
    names = [scenario.name for scenario in HISTORICAL_SCENARIOS]
    selected = st.selectbox("Historical scenario", names + ["Custom date range"])
    if selected == "Custom date range":
        start_date = st.date_input(
            "Scenario start date",
            analysis["prices"].index.min().date(),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )
        end_date = st.date_input(
            "Scenario end date (inclusive)",
            analysis["prices"].index.max().date(),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )
        try:
            scenario = custom_scenario(start_date, end_date)
        except ValueError as exc:
            st.warning(str(exc))
            return
    else:
        scenario = HISTORICAL_SCENARIOS[names.index(selected)]
        st.caption(scenario.description)
    st.caption(
        f"Requested window: {scenario.start:%b %d, %Y} – {scenario.end:%b %d, %Y} (inclusive)."
    )
    request = (scenario.name, scenario.start, scenario.end)
    rebalance = analysis.get("rebalance", "daily")
    cost_bps = analysis.get("cost_bps", 0.0)
    if st.button("Run historical stress test"):
        analysis.pop("stress", None)
        analysis.pop("stress_error", None)
        try:
            with st.spinner("Loading scenario prices and replaying historical returns…"):
                history = fetch_price_history(
                    list(analysis["prices"].columns),
                    scenario.start.date(),
                    scenario.end.date() + timedelta(days=1),
                )
                result = stress_test(history, analysis["weights"], scenario, rebalance, cost_bps)
                curve = None
                if result.available:
                    window = history.loc[result.first_date : result.last_date].dropna(how="any")
                    daily = portfolio_returns(
                        to_returns(window), analysis["weights"], rebalance, cost_bps
                    )
                    curve = cumulative_wealth(daily).reindex(window.index, fill_value=1.0)
                analysis["stress"] = (request, result, curve)
        except (ValueError, DataFetchError, NotImplementedError) as exc:
            analysis["stress_error"] = (request, str(exc))
    if analysis.get("stress_error", (None,))[0] == request:
        st.warning(f"Scenario unavailable: {analysis['stress_error'][1]}")
        return
    saved = analysis.get("stress")
    if saved is None or saved[0] != request:
        st.info(
            "Run the selected scenario to check availability. Every stock needs history spanning the window and at least three common price dates. Recently listed stocks may make older scenarios unavailable; no prices are invented or filled."
        )
        return
    result = saved[1]
    if not result.available:
        st.warning(f"Scenario unavailable — {result.scenario.name}. {result.reason}")
        st.caption(
            "Try a later custom start date or a portfolio whose stocks traded throughout the window. At least three common price dates are required."
        )
        return
    render_stress_result(saved, rebalance, cost_bps, analysis.get("portfolio_value"))


def render_stress_result(
    saved: tuple, rebalance: str, cost_bps: float, portfolio_value: float | None
) -> None:
    """Show backend scenario metrics as fractions, dollars when known, and wealth as a multiple."""
    _, result, curve = saved
    st.caption(
        f"Actual price dates: {result.first_date:%b %d, %Y} – {result.last_date:%b %d, %Y} · {result.n_returns:,} return observations."
    )
    return_column, drawdown_column, volatility_column = st.columns(3)
    with return_column.container(border=True):
        st.metric(
            "Scenario return",
            f"{result.cumulative_return:.2%}",
            delta=dollar_change(result.cumulative_return, portfolio_value),
            help="Cumulative return over the actual scenario price dates.",
        )
    with drawdown_column.container(border=True):
        st.metric(
            "Scenario maximum drawdown",
            f"{result.max_drawdown:.2%}",
            delta=dollar_change(result.max_drawdown, portfolio_value),
            help="Worst peak-to-trough decline; negative values represent losses.",
        )
    with volatility_column.container(border=True):
        st.metric(
            "Scenario annualized volatility",
            f"{result.annualized_volatility:.2%}",
            help="Sample daily volatility annualized using 252 trading days.",
        )
    stress_fig = px.line(
        x=curve.index,
        y=curve,
        labels={"x": "Date", "y": "Portfolio wealth"},
        color_discrete_sequence=["#264653"],
    )
    stress_fig.update_layout(
        template="plotly_white",
        title=f"Hypothetical replay · {result.scenario.name}",
        hovermode="x unified",
        height=450,
        showlegend=False,
    )
    stress_fig.update_xaxes(title_text="Historical date", rangeslider_visible=True)
    stress_fig.update_yaxes(
        title_text="Wealth multiple (starting wealth = 1.0)", tickformat=".2f", ticksuffix="×"
    )
    stress_fig.update_traces(
        line_width=2, hovertemplate="%{x|%b %d, %Y}<br>Portfolio wealth: %{y:.3f}×<extra></extra>"
    )
    st.plotly_chart(stress_fig, key="stress_chart")
    in_dollars = (
        f" Dollar amounts apply the scenario to your ${portfolio_value:,.2f} portfolio."
        if portfolio_value is not None
        else ""
    )
    st.caption(
        f"{result.note} {REBALANCE_DESCRIPTIONS[rebalance]}; {cost_text(cost_bps)}. "
        f"Missing trading dates are omitted.{in_dollars}"
    )


COMPARISON_LABELS = {  # metric: (row label, value format, change format)
    "annualized_return": ("Annualized return", "{:.2%}", "{:+.2%}"),
    "annualized_volatility": ("Annualized volatility", "{:.2%}", "{:+.2%}"),
    "sharpe_ratio": ("Sharpe ratio", "{:.2f}", "{:+.2f}"),
    "sortino_ratio": ("Sortino ratio", "{:.2f}", "{:+.2f}"),
    "max_drawdown": ("Maximum drawdown", "{:.2%}", "{:+.2%}"),
    "var": ("One-day VaR (95%)", "{:.2%}", "{:+.2%}"),
    "cvar": ("One-day CVaR (95%)", "{:.2%}", "{:+.2%}"),
    "annual_turnover": ("Annual turnover", "{:.2%}", "{:+.2%}"),
}


def format_number(value: float, pattern: str) -> str:
    """Format a finite number with ``pattern``; NaN and infinities show as N/A."""
    return pattern.format(value) if isfinite(value) else "N/A"


def comparison_table(table: pd.DataFrame) -> pd.DataFrame:
    """Before, after, and change columns of ``compare_portfolios`` as labeled display text."""
    rows = {}
    for metric, row in table.iterrows():
        label, value_format, change_format = COMPARISON_LABELS[metric]
        rows[label] = {
            "Before": format_number(row["before"], value_format),
            "After": format_number(row["after"], value_format),
            "Change": format_number(row["change"], change_format),
        }
    return pd.DataFrame.from_dict(rows, orient="index").rename_axis("Metric")


WHAT_IF_DEFAULT_BUY = "TLT"  # long-term Treasury ETF, a common diversifier


def run_what_if(analysis: dict, sell: str, buy_text: str, amount: float) -> tuple:
    """Compare one trade on shared prices: (metrics table, weights table, (first, last, rows)).

    ``amount`` is a fraction of the portfolio. A ticker not yet held is
    downloaded for the analysis dates, and both portfolios use the dates every
    ticker shares.
    """
    buy = validate_tickers(buy_text)
    if len(buy) != 1:
        raise ValueError("Enter one ticker to buy.")
    prices = analysis["prices"]
    before = pd.Series(analysis["weights"], index=prices.columns)
    after = trade_weights(before, sell, buy[0], amount)
    if buy[0] not in prices.columns:
        prices = fetch_prices(
            list(after.index),
            prices.index.min().date(),
            prices.index.max().date() + timedelta(days=1),
        )
    table = compare_portfolios(
        prices,
        before,
        after,
        rebalance=analysis.get("rebalance", "daily"),
        cost_bps=analysis.get("cost_bps", 0.0),
    )
    weights = pd.DataFrame(
        {"Before": before.reindex(after.index, fill_value=0.0), "After": after}
    ).rename_axis("Ticker")
    return table, weights, (prices.index.min(), prices.index.max(), len(prices))


def render_what_if(analysis: dict) -> None:
    """Compare risk metrics before and after moving part of the portfolio to another ticker."""
    st.divider()
    st.subheader("What-if trade")
    st.caption(
        "Sell part of one holding and buy another ticker, then replay both portfolios on the same past prices with your rebalancing and trading cost. Hypothetical: not a prediction of how the trade will do."
    )
    sell_column, buy_column, amount_column = st.columns(3)
    sell = sell_column.selectbox("Sell", list(analysis["prices"].columns))
    buy_text = buy_column.text_input(
        "Buy",
        WHAT_IF_DEFAULT_BUY,
        help="A ticker you hold or a new one; a new one is downloaded for the same dates.",
    )
    amount_pct = amount_column.number_input(
        "Amount (% of portfolio)",
        min_value=0.01,
        max_value=100.0,
        value=10.0,
        step=1.0,
        format="%.2f",
        help="Share of total portfolio value moved, not of the holding sold.",
    )
    request = (sell, buy_text.strip().upper(), amount_pct)
    if st.button("Simulate trade"):
        analysis.pop("what_if", None)
        analysis.pop("what_if_error", None)
        try:
            with st.spinner("Replaying the portfolio before and after the trade…"):
                result = run_what_if(analysis, sell, buy_text, amount_pct / 100)
            analysis["what_if"] = (request, *result)
        except (ValueError, DataFetchError) as exc:
            analysis["what_if_error"] = (request, str(exc))
    if analysis.get("what_if_error", (None,))[0] == request:
        st.warning(plain_text(f"Trade simulation unavailable. {analysis['what_if_error'][1]}"))
        return
    saved = analysis.get("what_if")
    if saved is None or saved[0] != request:
        st.info(
            "Choose a trade and select Simulate trade to compare the portfolio before and after."
        )
        return
    render_what_if_result(analysis, saved)


def render_what_if_result(analysis: dict, saved: tuple) -> None:
    """Show before/after weights and metrics for a simulated trade, with its one-time cost."""
    (sell, buy, amount_pct), table, weights, (first, last, rows) = saved
    weights_column, metrics_column = st.columns([1, 2])
    with weights_column:
        st.markdown("**Weights**")
        st.dataframe(weights.style.format("{:.2%}"), key="what_if_weights")
    with metrics_column:
        st.markdown("**Metrics**")
        st.dataframe(comparison_table(table), key="what_if_metrics")
    amount = amount_pct / 100
    rebalance = analysis.get("rebalance", "daily")
    cost_bps = analysis.get("cost_bps", 0.0)
    cost = trade_cost(amount, cost_bps)
    value = analysis.get("portfolio_value")
    moved = f" (${amount * value:,.2f})" if value is not None else ""
    paid = f" (${cost * value:,.2f})" if value is not None else ""
    st.caption(
        plain_text(
            f"Moves {amount:.2%} of the portfolio{moved} from {sell} to {buy}. Both columns use "
            f"the same {rows:,} price dates ({first:%b %d, %Y} – {last:%b %d, %Y}). "
            f"{REBALANCE_DESCRIPTIONS[rebalance]}; {cost_text(cost_bps)}. Change is after minus "
            "before; VaR and CVaR are one-day historical losses. The one-time cost of the trade "
            f"itself, {cost:.3%} of the portfolio{paid}, is not in the metrics."
        )
    )


def run_shocks(analysis: dict, shocks: dict[str, float]) -> ShockImpact:
    """Download the shocked proxies for the analysis dates and estimate the portfolio move."""
    prices = analysis["prices"]
    proxy_prices = fetch_prices(
        [SHOCK_PROXIES[name] for name in shocks],
        prices.index.min().date(),
        prices.index.max().date() + timedelta(days=1),
    )
    names = {ticker: name for name, ticker in SHOCK_PROXIES.items()}
    proxy_returns = to_returns(proxy_prices).rename(columns=names)
    return shock_impact(to_returns(prices), proxy_returns, analysis["weights"], shocks)


def render_shocks(analysis: dict) -> None:
    """Estimate the portfolio's move if market proxies such as tech or bonds move by set amounts."""
    st.divider()
    st.subheader("Custom shocks")
    st.caption(
        "Enter a move for one or more market proxies, e.g. Technology −20% and Long-term bonds +5%. Each holding's move comes from its betas to those proxies over your analysis period. Hypothetical: not a prediction."
    )
    columns = st.columns(3)
    moves = {
        name: columns[i % len(columns)].number_input(
            f"{name} ({ticker}) move (%)",
            min_value=-99.0,
            max_value=200.0,
            value=0.0,
            step=1.0,
            format="%.1f",
        )
        for i, (name, ticker) in enumerate(SHOCK_PROXIES.items())
    }
    shocks = {name: move / 100 for name, move in moves.items() if move != 0}
    request = tuple(shocks.items())
    if st.button("Apply shocks", disabled=not shocks):
        analysis.pop("shock", None)
        analysis.pop("shock_error", None)
        try:
            with st.spinner("Downloading proxy prices and estimating betas…"):
                analysis["shock"] = (request, run_shocks(analysis, shocks))
        except (ValueError, DataFetchError) as exc:
            analysis["shock_error"] = (request, str(exc))
    if analysis.get("shock_error", (None,))[0] == request:
        st.warning(plain_text(f"Shock estimate unavailable. {analysis['shock_error'][1]}"))
        return
    saved = analysis.get("shock")
    if saved is None or saved[0] != request:
        st.info("Enter at least one non-zero move and select Apply shocks.")
        return
    render_shock_result(saved[1], analysis.get("portfolio_value"))


def render_shock_result(impact: ShockImpact, portfolio_value: float | None) -> None:
    """Show the estimated portfolio move and each holding's move, contribution, and betas."""
    with st.container(border=True):
        st.metric(
            "Estimated portfolio move",
            f"{impact.portfolio_impact:.2%}",
            delta=dollar_change(impact.portfolio_impact, portfolio_value),
            help="Weighted sum of each holding's estimated move.",
        )
    holdings = impact.holdings.rename(
        columns={
            "weight": "Weight",
            "impact": "Estimated move",
            "contribution": "Contribution",
            "r_squared": "R²",
        }
    )
    betas = impact.betas.rename(columns=lambda name: f"Beta to {name}")
    percent = dict.fromkeys(["Weight", "Estimated move", "Contribution"], "{:.2%}")
    st.dataframe(
        pd.concat([holdings, betas], axis=1)
        .rename_axis("Ticker")
        .style.format(
            {**percent, "R²": "{:.2f}", **dict.fromkeys(betas.columns, "{:.2f}")}, na_rep="N/A"
        ),
        key="shock_holdings",
    )
    applied = ", ".join(f"{name} {move:+.1%}" for name, move in impact.shocks.items())
    st.caption(
        f"Shocks: {applied}. Betas come from a least-squares regression of each holding's daily returns on the shocked proxies' daily returns over {impact.observations} shared days ({impact.first_date:%b %d, %Y} – {impact.last_date:%b %d, %Y}). Proxies left at 0% are not used, so a beta also carries whatever moves with that proxy. Linear, instantaneous estimate on your target weights; a holding's move is capped at −100%. Not a prediction."
    )


def render_simulation(analysis: dict) -> None:
    """Display hypothetical wealth multiples and cumulative terminal return fractions."""
    st.divider()
    st.subheader("Monte Carlo · hypothetical simulations")
    st.caption("Scenarios based on historical returns, not predictions or guarantees.")
    with st.form("simulation_request"):
        horizon = st.number_input(
            "Forecast horizon (trading days)",
            MIN_HORIZON_DAYS,
            MAX_HORIZON_DAYS,
            252,
            help="Simulation steps; future dates are weekdays, including exchange holidays.",
        )
        paths = st.number_input(
            "Simulation count",
            MIN_PATHS,
            MAX_PATHS,
            MIN_PATHS,
            step=1000,
            help="More paths reduce sampling noise but require more time and memory.",
        )
        seed = st.number_input(
            "Random seed",
            0,
            2**32 - 1,
            DEFAULT_SEED,
            help="Identical history and settings reproduce the same scenarios.",
        )
        run = st.form_submit_button("Run hypothetical simulations")
    if run:
        analysis.pop("simulation", None)
        analysis.pop("simulation_error", None)
        try:
            with st.spinner("Generating hypothetical portfolio scenarios…"):
                result = simulate_portfolio(
                    analysis["daily_returns"], horizon_days=horizon, n_paths=paths, seed=seed
                )
                analysis["simulation"] = (result, horizon, paths, seed)
        except (ValueError, NotImplementedError, MemoryError) as exc:
            analysis["simulation_error"] = str(exc) or "Try fewer simulations or a shorter horizon."
    if analysis.get("simulation_error"):
        st.error(f"Unable to simulate this portfolio. {analysis['simulation_error']}")
        return
    saved = analysis.get("simulation")
    if saved is None:
        st.info("Choose simulation settings and run to explore hypothetical outcomes.")
        return
    result, used_horizon, used_paths, used_seed = saved
    bands = result.percentile_paths
    st.caption(
        f"Displayed run: {used_horizon:,} trading days · {used_paths:,} simulations · seed {used_seed}. Run again to apply changes."
    )
    median_column, loss_column = st.columns(2)
    with median_column.container(border=True):
        st.metric(
            "Hypothetical terminal median return",
            f"{bands['median'].iloc[-1] - 1.0:.2%}",
            help="Ending median wealth from the simulation API, displayed as cumulative return from the starting wealth of 1.0.",
        )
    with loss_column.container(border=True):
        st.metric(
            "Hypothetical probability of loss",
            f"{result.loss_probability:.2%}",
            help="Share of simulated paths ending below their starting wealth; not a real-world loss forecast.",
        )
    fan = go.Figure()
    for lower, upper, label, color in (
        ("p5", "p95", "5th–95th percentiles", "rgba(42,157,143,0.15)"),
        ("p25", "p75", "25th–75th percentiles", "rgba(42,157,143,0.35)"),
    ):
        fan.add_trace(
            go.Scatter(
                x=bands.index,
                y=bands[lower],
                mode="lines",
                line_width=0,
                showlegend=False,
                name=lower,
                hovertemplate="%{x|%b %d, %Y}<br>Wealth: %{y:.3f}×<extra>%{fullData.name}</extra>",
            )
        )
        fan.add_trace(
            go.Scatter(
                x=bands.index,
                y=bands[upper],
                mode="lines",
                line_width=0,
                fill="tonexty",
                fillcolor=color,
                name=label,
                hovertemplate="%{x|%b %d, %Y}<br>Upper wealth: %{y:.3f}×<extra>%{fullData.name}</extra>",
            )
        )
    fan.add_trace(
        go.Scatter(
            x=bands.index,
            y=bands["median"],
            mode="lines",
            line={"color": "#264653", "width": 3},
            name="Median",
            hovertemplate="%{x|%b %d, %Y}<br>Median wealth: %{y:.3f}×<extra></extra>",
        )
    )
    fan.update_layout(
        template="plotly_white",
        title="Hypothetical portfolio wealth scenarios",
        hovermode="x unified",
        height=450,
        legend_title_text="Simulated percentiles",
    )
    fan.update_xaxes(title_text="Simulation date", rangeslider_visible=True)
    fan.update_yaxes(
        title_text="Wealth multiple (starting wealth = 1.0)", tickformat=".2f", ticksuffix="×"
    )
    fan.add_hline(y=1.0, line_dash="dot", line_color="gray")
    st.plotly_chart(fan, key="simulation_chart", width="stretch")
    st.caption(
        "Bands are pointwise percentiles across hypothetical paths, not confidence bounds or individual paths. The median line is not one simulated path."
    )
    st.caption(
        "Assumes independent normally distributed daily log returns fitted to historical data. Short histories are unreliable; crashes, changing markets, fees, taxes and cash flows are not captured. Dates include weekdays without excluding exchange holidays."
    )


st.set_page_config(page_title="RiskLens Quant", page_icon="◈", layout="wide")

with st.sidebar:
    st.title("◈ RiskLens")
    st.caption("QUANT · PORTFOLIO ANALYTICS")
    st.divider()
    with st.expander("Import holdings from CSV"):
        upload = st.file_uploader(
            "Holdings CSV",
            type="csv",
            help="A header row naming ticker and either shares or value (dollars), "
            "then one row per stock; maximum 25.",
        )
    imported = None
    if upload is not None:
        try:
            imported = parse_holdings_csv(upload.getvalue())
        except ValueError as exc:
            st.error(plain_text(f"Could not import {upload.name}. {exc}"))
    if imported is not None:
        holding_kind, imported_amounts = imported
        tickers = list(imported_amounts.index)
        st.caption(
            f"Using {len(tickers)} holdings from {plain_text(upload.name)}. "
            "Remove the file to enter holdings by hand."
        )
    elif upload is not None:
        tickers, holding_kind = [], "value"  # a bad file blocks analysis instead of falling back
    else:
        raw_tickers = st.text_input(
            "Stock tickers",
            "AAPL, MSFT",
            help="Separate tickers with commas or spaces; maximum 25.",
        )
        try:
            tickers = validate_tickers(raw_tickers)
        except ValueError as exc:
            tickers = []
            st.error(plain_text(str(exc)))
        holding_kind = HOLDING_INPUTS[st.radio("Enter holdings as", list(HOLDING_INPUTS))]

    with st.form("portfolio_request"):
        st.markdown("**Portfolio holdings**")
        st.caption(HOLDING_CAPTIONS[holding_kind])
        if imported is None:
            amounts = holding_inputs(tickers, holding_kind)
        else:
            amounts = imported_amounts.tolist()
            st.dataframe(imported_amounts, key="imported_holdings")
        entered_value = None
        if holding_kind == "weight":
            entered_value = st.number_input(
                "Portfolio value ($)",
                min_value=1.0,
                value=None,
                step=1000.0,
                format="%.2f",
                placeholder="Optional",
                help="Total market value. When set, VaR, CVaR, drawdown, and stress results "
                "also show dollar amounts.",
            )
        today = date.today()
        start = st.date_input(
            "Start date",
            today - timedelta(days=365),
            min_value=date(1900, 1, 1),
            max_value=today,
        )
        end = st.date_input(
            "End date (inclusive)",
            today,
            min_value=date(1900, 1, 1),
            max_value=today,
        )
        rebalance_label = st.selectbox(
            "Rebalancing",
            list(REBALANCE_CHOICES),
            help="How often holdings are traded back to the target weights.",
        )
        cost_bps = st.number_input(
            "Trading cost (bps)",
            min_value=0.0,
            max_value=MAX_COST_BPS,
            value=0.0,
            step=1.0,
            format="%.1f",
            help="Commission plus spread per dollar bought or sold, in basis points "
            "(5 bps = 0.05%). Charged on rebalance dates; the initial purchase is free.",
        )
        submitted = st.form_submit_button("Analyze portfolio", disabled=not tickers)

st.caption("PORTFOLIO INTELLIGENCE / OVERVIEW")
st.title("RiskLens Quant")
st.markdown(
    "Explore historical risk, diversification, market comparisons, and hypothetical scenarios."
)

analysis = st.session_state.get("analysis")
if analysis is not None and (
    list(analysis["prices"].columns) != tickers
    # The CSV file and holdings type sit outside the form, so a change shows right away.
    or analysis.get("holdings") != (holding_kind, tuple(amounts))
):
    st.session_state.pop("analysis", None)

if submitted:
    st.session_state.pop("analysis", None)
    try:
        if holding_kind == "weight":
            try:
                weights = validate_weights([value / 100 for value in amounts], len(tickers))
            except ValueError as exc:
                raise ValueError(
                    f"Use non-negative weights totaling 100%. Current total: {sum(amounts):.2f}%."
                ) from exc
        if start >= end:
            raise ValueError("Start date must be before end date.")
        with st.spinner("Loading prices and calculating portfolio metrics…"):
            # Yahoo's end date is exclusive; the UI includes the selected day.
            prices = fetch_prices(tickers, start, end + timedelta(days=1))
            if prices.empty:
                raise ValueError("No price history was returned. Try different tickers or dates.")
            portfolio_value = entered_value
            if holding_kind != "weight":
                weights, portfolio_value = holdings_to_weights(
                    pd.Series(amounts, index=tickers), holding_kind, prices
                )
            rebalance = REBALANCE_CHOICES[rebalance_label]
            result = analyze_portfolio(prices, weights, rebalance=rebalance, cost_bps=cost_bps)
            metrics = (
                result.annualized_return,
                result.annualized_volatility,
                result.sharpe_ratio,
                result.max_drawdown,
                result.sortino_ratio,
                result.calmar_ratio,
            )
            if not all(isfinite(value) for value in (metrics[0], metrics[1], metrics[3])):
                raise ValueError(
                    "Choose a longer period: these prices could not produce finite risk metrics."
                )
            st.session_state["analysis"] = {
                "prices": prices,
                "weights": weights,
                "metrics": metrics,
                "drawdown": drawdown_series(result.daily_returns),
                "daily_returns": result.daily_returns,
                "rebalance": rebalance,
                "cost_bps": cost_bps,
                "annual_turnover": result.annual_turnover,
                "holding_kind": holding_kind,
                "holdings": (holding_kind, tuple(amounts)),
                "portfolio_value": portfolio_value,
            }
            if rebalance != "daily" or cost_bps > 0:
                # Optimized weights assume daily rebalancing and no costs; compare like for like.
                baseline = analyze_portfolio(prices, weights)
                st.session_state["analysis"]["optimization_baseline"] = (
                    baseline.annualized_return,
                    baseline.annualized_volatility,
                    baseline.sharpe_ratio,
                )
            try:
                benchmark_prices = fetch_benchmark_prices(start, end + timedelta(days=1))
                st.session_state["analysis"]["benchmark"] = compare_to_benchmark(
                    prices,
                    weights,
                    benchmark_prices,
                    rebalance=rebalance,
                    cost_bps=cost_bps,
                )
                st.session_state["analysis"]["benchmark_stats"] = benchmark_statistics(
                    prices,
                    weights,
                    benchmark_prices,
                    rebalance=rebalance,
                    cost_bps=cost_bps,
                )
            except (ValueError, DataFetchError, NotImplementedError) as exc:
                st.session_state["analysis"]["benchmark_error"] = str(exc)
    except NotImplementedError:
        st.error(
            "Portfolio analytics is not ready. Save Claude’s completed analytics engine and try again."
        )
    except (ValueError, DataFetchError) as exc:
        st.error(f"Unable to analyze this portfolio. {exc}")

analysis = st.session_state.get("analysis")
if analysis is None:
    if not submitted:
        st.info("Choose tickers, enter your holdings, and select Analyze portfolio.")
else:
    prices = analysis["prices"]
    st.subheader("Portfolio snapshot")
    allocation = " · ".join(
        f"{ticker} {weight:.2%}"
        for ticker, weight in zip(prices.columns, analysis["weights"], strict=True)
    )
    st.caption(
        f"{allocation} | {prices.index.min():%b %d, %Y} – "
        f"{prices.index.max():%b %d, %Y} | {len(prices):,} price observations"
    )
    portfolio_value = analysis.get("portfolio_value")
    if portfolio_value is not None:
        valued = (
            f", with shares valued at {prices.index.max():%b %d, %Y} closes"
            if analysis.get("holding_kind") == "shares"
            else ""
        )
        st.caption(
            f"Portfolio value: ${portfolio_value:,.2f}{valued}. "
            "Dollar amounts under the cards apply each percentage to this value."
        )
    descriptions = (
        (
            "Annualized return",
            "Mean daily portfolio return × 252; arithmetic annualization.",
            ".2%",
        ),
        ("Annualized volatility", "Sample daily standard deviation × √252.", ".2%"),
        (
            "Sharpe ratio",
            "Annualized excess return / volatility. Assumes a 0% annual risk-free rate.",
            ".2f",
        ),
        (
            "Maximum drawdown",
            "Worst peak-to-trough decline, including initial wealth; negative means loss.",
            ".2%",
        ),
        (
            "Sortino ratio",
            "Annualized return / annualized downside deviation (shortfalls below 0% "
            "over every day). Like Sharpe, but only losses count as risk; N/A without "
            "a down day.",
            ".2f",
        ),
        (
            "Calmar ratio",
            "Compound annual growth rate / |maximum drawdown|: yearly growth per unit of "
            "worst decline; N/A without a drawdown.",
            ".2f",
        ),
    )
    deltas = (None, None, None, dollar_change(analysis["metrics"][3], portfolio_value), None, None)
    for column, (label, help_text, spec), value, delta in zip(
        [*st.columns(3), *st.columns(3)],
        descriptions,
        analysis["metrics"],
        deltas,
        strict=True,
    ):
        with column.container(border=True):
            st.metric(
                label,
                format(value, spec) if isfinite(value) else "N/A",
                delta=delta,
                help=help_text,
            )
    if not isfinite(analysis["metrics"][2]):
        st.caption(
            "Sharpe ratio is unavailable because portfolio volatility is zero or too close to zero."
        )
    st.caption(
        f"{REBALANCE_DESCRIPTIONS[analysis.get('rebalance', 'daily')]}; "
        f"{cost_text(analysis.get('cost_bps', 0.0))}. Annualized figures use 252 trading days."
    )
    if "annual_turnover" in analysis:
        st.caption(
            f"Annual turnover: {analysis['annual_turnover']:.1%} of the portfolio bought "
            "(and sold) per year to restore target weights."
        )

    st.divider()
    st.subheader("Historical prices")
    fig = px.line(
        prices, labels={"index": "Date", "value": "Adjusted closing price", "variable": "Ticker"}
    )
    fig.update_layout(
        title="Historical adjusted closing prices",
        template="plotly_white",
        hovermode="x unified",
        legend_title_text="Ticker",
        height=450,
    )
    fig.update_xaxes(title_text="Date", showgrid=False)
    fig.update_yaxes(title_text="Adjusted closing price", tickformat=".2f")
    fig.update_traces(
        line_width=2,
        hovertemplate="%{y:.2f}<extra>%{fullData.name}</extra>",
    )
    st.plotly_chart(fig)
    st.caption(
        "Daily adjusted closing prices. Use tickers quoted in the same currency; no currency conversion is applied."
    )

    st.divider()
    st.subheader("Historical drawdown")
    drawdown = analysis.get("drawdown")
    if drawdown is None or drawdown.empty:
        st.info("No drawdown history is available. Select Analyze portfolio to reload it.")
    else:
        drawdown_fig = px.area(
            x=drawdown.index,
            y=drawdown,
            labels={"x": "Date", "y": "Drawdown"},
            color_discrete_sequence=["#e76f51"],
        )
        st.caption("Drawdown measures the decline below the portfolio’s prior peak.")
        show_slider = st.checkbox("Show date range slider", value=True)
        drawdown_fig.update_xaxes(rangeslider_visible=show_slider)
        drawdown_fig.update_yaxes(tickformat=".0%", title_text="Drawdown")
        drawdown_fig.update_traces(
            fill="tozeroy",
            hovertemplate="%{x|%b %d, %Y}<br>%{y:.2%}<extra></extra>",
        )
        drawdown_fig.update_layout(hovermode="x unified", height=380, showlegend=False)
        drawdown_fig.add_hline(y=0, line_dash="dot", line_color="gray")
        st.plotly_chart(drawdown_fig, key="drawdown_chart")
        st.caption("Drag to zoom; double-click to reset.")
        st.caption("Initial wealth is included, so a first-day loss counts.")

    render_rolling(analysis)

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
                "HHI concentration",
                f"{hhi:.3f}",
                help="Sum of squared allocation weights, on a 0–1 scale. Lower means more evenly spread; 1 means one holding has all the weight.",
            )
        with holdings_column.container(border=True):
            st.metric(
                "Effective number of holdings",
                f"{holdings:.2f}",
                help="1 / HHI: the number of equally weighted holdings with the same allocation concentration. Zero-weight stocks do not count.",
            )
        st.caption(
            "These measures describe allocation balance, not stock independence. Similar stocks can still carry similar risks."
        )

    render_risk_attribution(analysis)
    render_risk_sources(analysis)

    if len(prices.columns) == 1:
        st.info(
            "A single-stock portfolio has no cross-stock diversification. Add another stock to compare return correlations."
        )
    else:
        try:
            correlations = correlation_matrix(to_returns(prices))
        except ValueError as exc:
            st.warning(f"Stock-return correlation is unavailable. {exc}")
        else:
            st.markdown("**Daily stock-return correlation**")
            st.caption(
                "Pearson correlation: +1 = move together, 0 = no linear relationship, −1 = move oppositely. Historical correlations can change."
            )
            if correlations.isna().any().any():
                st.info(
                    "Blank cells indicate undefined correlation, usually because a stock's returns are constant. They do not mean zero correlation."
                )
            correlation_fig = px.imshow(
                correlations,
                zmin=-1,
                zmax=1,
                color_continuous_scale="RdBu",
                labels={"x": "Stock", "y": "Stock", "color": "Correlation"},
                text_auto=".2f",
                aspect="equal",
            )
            correlation_fig.update_traces(
                hovertemplate="%{y} / %{x}<br>Daily return correlation: %{z:.2f}<extra></extra>",
                hoverongaps=False,
            )
            correlation_fig.update_layout(template="plotly_white", height=500)
            st.plotly_chart(correlation_fig, key="correlation_heatmap")
            st.caption(
                "Based on adjusted daily returns over the selected period, using dates shared by every stock. Includes entered stocks with zero allocation; this is not a weighted portfolio correlation."
            )

    st.divider()
    st.subheader("Portfolio vs. S&P 500 (SPY)")
    st.caption(
        "SPY is an ETF tracking the S&P 500. Both series use adjusted prices, including splits and dividends."
    )
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
            st.info(
                "Only one shared return interval is available. Choose a longer period for a more useful comparison."
            )
        benchmark_fig = px.line(
            performance,
            labels={"index": "Date", "value": "Cumulative return", "variable": "Investment"},
            color_discrete_sequence=["#264653", "#e76f51"],
        )
        benchmark_fig.update_layout(
            template="plotly_white",
            hovermode="x unified",
            height=450,
            legend_title_text="Investment",
        )
        benchmark_fig.update_xaxes(title_text="Date", showgrid=False, rangeslider_visible=True)
        benchmark_fig.update_yaxes(title_text="Cumulative return", tickformat=".1%")
        benchmark_fig.update_traces(
            line_width=2, hovertemplate="%{x|%b %d, %Y}<br>%{y:.2%}<extra>%{fullData.name}</extra>"
        )
        benchmark_fig.add_hline(y=0, line_dash="dot", line_color="gray")
        st.plotly_chart(benchmark_fig, key="benchmark_chart")
        portfolio_column, benchmark_column = st.columns(2)
        with portfolio_column.container(border=True):
            st.metric(
                "Portfolio ending return",
                f"{ending_returns['Portfolio']:.2%}",
                help="Cumulative portfolio return over the shared dates; not annualized.",
            )
        with benchmark_column.container(border=True):
            st.metric(
                "SPY ending return",
                f"{ending_returns['S&P 500 (SPY)']:.2%}",
                help="Cumulative adjusted SPY return over the same shared dates; not annualized.",
            )
        st.caption(
            "Ending returns are cumulative over this shared period, not annualized. The portfolio follows the selected rebalancing on the shared trading dates. Shorter SPY coverage can make this period differ from the risk cards above. Past performance does not predict future returns."
        )
        render_benchmark_ratios(analysis)

    render_tail_risk(analysis)
    render_volatility_forecast(analysis)
    simulation_tab, stress_tab, trade_tab, shock_tab = st.tabs(
        ["Simulated futures", "Historical scenarios", "What-if trade", "Custom shocks"]
    )
    with simulation_tab:
        render_simulation(analysis)
    with stress_tab:
        render_stress_test(analysis)
    with trade_tab:
        render_what_if(analysis)
    with shock_tab:
        render_shocks(analysis)
    render_optimization(analysis)

st.divider()
st.caption(
    "Disclaimer: For educational and informational purposes only. "
    "This is not investment advice or a recommendation to buy or sell securities. "
    "Past performance does not guarantee future results. "
    "Historical estimates may understate future losses."
)
