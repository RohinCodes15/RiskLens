"""Unit tests for factor regression and sector/country breakdowns (no network)."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    FACTOR_COLUMNS,
    MIN_FACTOR_OBS,
    factor_exposure,
)


def factors(n: int = 250, seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data = rng.normal(0, 0.01, (n, len(FACTOR_COLUMNS)))
    frame = pd.DataFrame(
        data, index=pd.bdate_range("2024-01-02", periods=n), columns=FACTOR_COLUMNS
    )
    return frame.assign(RF=0.0001)


def test_recovers_known_betas_and_alpha_without_noise() -> None:
    f = factors()
    betas = np.array([1.1, 0.4, -0.3, 0.2])
    returns = f["RF"] + 0.0002 + f[list(FACTOR_COLUMNS)].to_numpy() @ betas
    exposure = factor_exposure(pd.Series(returns, index=f.index), f)
    np.testing.assert_allclose(exposure.betas.to_numpy(), betas, atol=1e-10)
    assert exposure.alpha == pytest.approx(0.0002 * 252)
    assert exposure.r_squared == pytest.approx(1.0)
    assert exposure.observations == 250


def test_noise_lowers_r_squared_and_only_shared_dates_are_used() -> None:
    f = factors()
    noise = np.random.default_rng(9).normal(0, 0.01, len(f))
    returns = pd.Series(f["Mkt-RF"].to_numpy() + noise, index=f.index).iloc[50:]
    exposure = factor_exposure(returns, f)
    assert 0.2 < exposure.r_squared < 0.8
    assert exposure.observations == 200
    assert exposure.first_date == f.index[50]


def test_rejects_short_overlap_missing_columns_and_constant_returns() -> None:
    f = factors()
    with pytest.raises(ValueError, match="at least"):
        factor_exposure(pd.Series(0.01, index=f.index[: MIN_FACTOR_OBS - 1]), f)
    with pytest.raises(ValueError, match="Mom"):
        factor_exposure(pd.Series(0.01, index=f.index), f.drop(columns="Mom"))
    with pytest.raises(ValueError, match="constant"):
        factor_exposure(f["RF"], f)
