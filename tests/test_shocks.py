"""Unit tests for custom shocks: proxy betas, capped holding moves, and portfolio impact."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import SHOCK_PROXIES, shock_impact


@pytest.fixture
def proxies() -> pd.DataFrame:
    rng = np.random.default_rng(5)
    data = rng.normal(0, 0.01, (150, 3))
    return pd.DataFrame(
        data,
        index=pd.bdate_range("2025-01-02", periods=150),
        columns=["Technology", "Long-term bonds", "Gold"],
    )


@pytest.fixture
def assets(proxies: pd.DataFrame) -> pd.DataFrame:
    """Holdings built from known betas: A = 1.5·tech + 0.5·bonds, B = −0.4·bonds."""
    tech, bonds = proxies["Technology"], proxies["Long-term bonds"]
    return pd.DataFrame({"A": 0.0002 + 1.5 * tech + 0.5 * bonds, "B": -0.4 * bonds})


def test_proxy_list_names_one_etf_per_shock() -> None:
    assert SHOCK_PROXIES["Technology"] == "XLK"
    assert SHOCK_PROXIES["Long-term bonds"] == "TLT"
    assert len(set(SHOCK_PROXIES.values())) == len(SHOCK_PROXIES)


def test_recovers_known_betas_and_applies_the_shocks(
    assets: pd.DataFrame, proxies: pd.DataFrame
) -> None:
    shocks = {"Technology": -0.2, "Long-term bonds": 0.05}
    result = shock_impact(assets, proxies, [0.6, 0.4], shocks)
    np.testing.assert_allclose(result.betas.loc["A"], [1.5, 0.5], atol=1e-10)
    np.testing.assert_allclose(result.betas.loc["B"], [0.0, -0.4], atol=1e-10)
    expected = {"A": 1.5 * -0.2 + 0.5 * 0.05, "B": -0.4 * 0.05}
    assert result.holdings["impact"].to_dict() == pytest.approx(expected)
    assert result.holdings["contribution"].to_dict() == pytest.approx(
        {"A": 0.6 * expected["A"], "B": 0.4 * expected["B"]}
    )
    assert result.portfolio_impact == pytest.approx(0.6 * expected["A"] + 0.4 * expected["B"])
    assert result.holdings["r_squared"].to_numpy() == pytest.approx([1.0, 1.0])
    assert result.observations == 150


def test_only_shocked_proxies_enter_the_regression(
    assets: pd.DataFrame, proxies: pd.DataFrame
) -> None:
    result = shock_impact(assets, proxies, [0.5, 0.5], {"Technology": -0.1, "Gold": 0.0})
    assert list(result.betas.columns) == ["Technology"]
    assert result.shocks.to_dict() == {"Technology": -0.1}
    assert result.holdings.loc["A", "r_squared"] < 1.0
    assert result.betas.loc["A", "Technology"] == pytest.approx(1.5, abs=0.15)


def test_holding_moves_are_capped_at_a_total_loss(proxies: pd.DataFrame) -> None:
    assets = pd.DataFrame({"LEV": 3.0 * proxies["Technology"], "CASH": 0.0 * proxies["Gold"]})
    result = shock_impact(assets, proxies, [0.5, 0.5], {"Technology": -0.5})
    assert result.holdings.loc["LEV", "impact"] == -1.0
    assert result.portfolio_impact == pytest.approx(-0.5)
    assert np.isnan(result.holdings.loc["CASH", "r_squared"])


def test_uses_only_dates_both_tables_share(assets: pd.DataFrame, proxies: pd.DataFrame) -> None:
    result = shock_impact(assets.iloc[40:], proxies.iloc[:-10], [0.5, 0.5], {"Technology": 0.1})
    assert result.observations == 100
    assert result.first_date == proxies.index[40]
    assert result.last_date == proxies.index[-11]


def test_a_holding_that_is_the_proxy_has_beta_one(proxies: pd.DataFrame) -> None:
    assets = pd.DataFrame({"XLK": proxies["Technology"]})
    result = shock_impact(assets, proxies, [1.0], {"Technology": -0.2})
    assert result.portfolio_impact == pytest.approx(-0.2)
