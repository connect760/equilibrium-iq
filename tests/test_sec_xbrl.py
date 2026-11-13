"""Tests for Layer-A extraction. All fixtures are SYNTHETIC (invented numbers), never real company data."""
import copy, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import pytest
from celi.sec_xbrl import annual_series, extract, ASSUMPTIONS
from celi.methodology import v3_0

def fy(year, val, filed=None, form="10-K", start=True, accn=None):
    r = {"end": f"{year}-12-31", "val": val, "fy": year, "fp": "FY", "form": form, "filed": filed or f"{year+1}-02-15", "accn": accn or f"0000000000-{year+1-2000:02d}-000001"}
    if start: r["start"] = f"{year}-01-01"
    return r

def synthetic(years=range(2016, 2025), fin=False):
    """SYNTHETIC company: revenue grows 5%/yr, 20% operating margin."""
    f = {"cik": 999999, "entityName": "SYNTHETIC TEST CO", "facts": {"us-gaap": {}}}
    g = f["facts"]["us-gaap"]
    def put(c, rows): g[c] = {"units": {"USD": rows}}
    rev = {y: 1000 * 1.05 ** (y - 2016) for y in years}
    put("Revenues", [fy(y, rev[y]) for y in years])
    put("OperatingIncomeLoss", [fy(y, 0.2 * rev[y]) for y in years])
    put("NetIncomeLoss", [fy(y, 0.15 * rev[y]) for y in years])
    put("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest", [fy(y, 0.19 * rev[y]) for y in years])
    put("IncomeTaxExpenseBenefit", [fy(y, 0.04 * rev[y]) for y in years])
    put("NetCashProvidedByUsedInOperatingActivities", [fy(y, 0.25 * rev[y]) for y in years])
    put("PaymentsToAcquirePropertyPlantAndEquipment", [fy(y, 0.05 * rev[y]) for y in years])
    put("DepreciationDepletionAndAmortization", [fy(y, 0.04 * rev[y]) for y in years])
    put("InterestExpense", [fy(y, 0.01 * rev[y]) for y in years])
    put("StockholdersEquity", [fy(y, 800, start=False) for y in years])
    put("LongTermDebtNoncurrent", [fy(y, 300, start=False) for y in years])
    put("CashAndCashEquivalentsAtCarryingValue", [fy(y, 100, start=False) for y in years])
    return f

def test_only_annual_10k_facts_used():
    f = synthetic()
    rows = f["facts"]["us-gaap"]["Revenues"]["units"]["USD"]
    rows.append({"end": "2024-06-30", "start": "2024-04-01", "val": 1, "fp": "Q2", "form": "10-Q", "filed": "2024-08-01"})
    rows.append({"end": "2024-12-31", "start": "2024-10-01", "val": 2, "fp": "FY", "form": "10-K", "filed": "2025-02-15"})  # quarter-length in a 10-K
    s, c = annual_series(f, "revenue", "2026-01-01")
    assert c == "Revenues" and "2024-06-30" not in s and s["2024-12-31"]["val"] > 100

def test_point_in_time_excludes_future_filings_and_honours_restatement():
    f = synthetic()
    rows = f["facts"]["us-gaap"]["Revenues"]["units"]["USD"]
    rows.append(fy(2023, 9999, filed="2025-03-01", form="10-K/A"))  # restated later
    s_before, _ = annual_series(f, "revenue", "2025-01-01")
    s_after, _ = annual_series(f, "revenue", "2026-01-01")
    assert s_before["2023-12-31"]["val"] != 9999 and s_after["2023-12-31"]["val"] == 9999
    s_cut, _ = annual_series(f, "revenue", "2024-01-01")
    assert "2024-12-31" not in s_cut

def test_concept_fallback_order():
    f = synthetic()
    g = f["facts"]["us-gaap"]; g["RevenueFromContractWithCustomerExcludingAssessedTax"] = g.pop("Revenues")
    _, c = annual_series(f, "revenue", "2026-01-01")
    assert c == "RevenueFromContractWithCustomerExcludingAssessedTax"

def test_roic_formula():
    out = extract(synthetic(), "2026-01-01", "tech")
    roic = out["log"]["ROIC_5Y"]["roic"]
    rev24 = 1000 * 1.05 ** 8
    tax_rate = 0.04 / 0.19
    expected = 0.2 * rev24 * (1 - tax_rate) / (800 + 300 - 100)
    assert roic[-1] == pytest.approx(expected)
    spread = sum(roic) / len(roic) - ASSUMPTIONS["wacc"]
    assert out["ev"]["ROIC_5Y"]["score"] == pytest.approx(round(max(0, min(100, 50 + 250 * spread)), 1))

def test_fcf_durability():
    out = extract(synthetic(), "2026-01-01", "tech")
    # FCF = 0.20 rev, op income 0.20 rev -> conversion 1.0 (capped), all years positive -> 100
    assert out["ev"]["FCF_DUR"]["score"] == 100.0

def test_revenue_durability_constant_growth_is_max_stability():
    out = extract(synthetic(), "2026-01-01", "tech")
    assert out["ev"]["REV_DUR"]["score"] == 100.0  # constant 5% growth and constant margin

def test_fin_frag_and_utility_scale():
    t = extract(synthetic(), "2026-01-01", "tech")["ev"]["FIN_FRAG"]["score"]
    u = extract(synthetic(), "2026-01-01", "utility")["ev"]["FIN_FRAG"]["score"]
    assert u <= t  # same leverage is less severe for a utility

def test_op_res_drawdown():
    f = synthetic()
    rows = f["facts"]["us-gaap"]["Revenues"]["units"]["USD"]
    for r in rows:
        if r["end"] == "2020-12-31": r["val"] *= 0.7
    out = extract(f, "2026-01-01", "tech")
    assert out["log"]["OP_RES"]["drawdown"] == pytest.approx(1 - 0.7 * 1.05)
    assert out["ev"]["OP_RES"]["score"] == pytest.approx(100 - 250 * out["log"]["OP_RES"]["drawdown"], abs=0.06)

def test_financial_path_uses_roe_and_marks_bank_items():
    out = extract(synthetic(), "2026-01-01", "financial")
    assert "ROE" in out["ev"]["ROIC_5Y"]["raw"]
    assert out["ev"]["FCF_DUR"]["state"] == "not_applicable"
    assert out["ev"]["FIN_FRAG"]["state"] == "unavailable"

def test_missing_data_is_unavailable_never_guessed():
    f = synthetic(); del f["facts"]["us-gaap"]["NetCashProvidedByUsedInOperatingActivities"]
    out = extract(f, "2026-01-01", "tech")
    assert out["ev"]["FCF_DUR"]["state"] == "unavailable" and out["ev"]["FCF_DUR"]["score"] is None
    for ind in ("REV_DIV", "REINVEST", "ENV_OUT"):
        assert out["ev"][ind]["state"] == "unavailable"

def test_every_score_is_bounded_and_cited():
    out = extract(synthetic(), "2026-01-01", "industrial")
    for ind, e in out["ev"].items():
        if e["state"] == "disclosed":
            assert 0 <= e["score"] <= 100
            assert e["tag"].startswith("us-gaap:") and e["latest_accession"] and e["filed"]

def test_extraction_is_deterministic():
    a = extract(synthetic(), "2026-01-01", "tech"); b = extract(copy.deepcopy(synthetic()), "2026-01-01", "tech")
    assert a == b

def test_layer_a_alone_cannot_produce_a_definitive_score():
    """Honest pipeline property: XBRL alone leaves judgement indicators unscored, so coverage < 80%."""
    ev = extract(synthetic(), "2026-01-01", "tech")["ev"]
    r = v3_0.compute({"archetype": "tech", "cutoff": "2026-01-01", "ev": ev, "events": []})
    assert r["status"] == "insufficient" and any("coverage" in x for x in r["reasons"])
