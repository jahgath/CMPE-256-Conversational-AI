import pandas as pd, pytest
from econ_chat import analytics as A, fred


@pytest.fixture(autouse=True)
def fake(monkeypatch):
    g = pd.Series([100 * 1.01 ** i for i in range(40)], index=pd.date_range("2015-01-01", periods=40, freq="QS"), name="GDP")
    c = pd.Series([100 * 1.002 ** i for i in range(120)], index=pd.date_range("2015-01-01", periods=120, freq="MS"), name="CPILFESL")
    monkeypatch.setattr(A, "load", lambda s: g if s == "GDP" else c)


def test_gdp_latest_growth():
    assert A.latest("GDP")["yoy_pct"] == pytest.approx((1.01 ** 4 - 1) * 100, abs=.01)


def test_cpi_latest_yoy():
    assert A.latest("CPILFESL")["yoy_inflation_pct"] == pytest.approx((1.002 ** 12 - 1) * 100, abs=.01)


def test_history_window():
    assert A.history("GDP", 5)["total_change_pct"] == pytest.approx((1.01 ** 20 - 1) * 100, abs=.2)


def test_unknown_series():
    with pytest.raises(ValueError):
        fred.load("FOO")
