"""SYNTHETIC TEST DATA — NOT A REAL COMPANY. Shaped like SEC companyfacts / submissions JSON.
Every payload carries "_synthetic": true so the pipeline refuses it in real assessments."""

CIK = 9999999
SYN_NAME = "SYNTHETIC TEST CORP"


def row(val, end, filed, accn, form="10-K", start=None, fy=None, fp="FY"):
    r = {"val": val, "end": end, "filed": filed, "accn": accn, "form": form, "fy": fy or int(filed[:4]), "fp": fp}
    if start:
        r["start"] = start
    return r


def companyfacts():
    # FY t is reported in its own 10-K, K[t], filed t+1-02-10, and again as a comparative in K[t+1].
    K = {yr: f"0009999999-{(yr + 1) % 100:02d}-000001" for yr in range(2021, 2026)}
    KF = {yr: f"{yr + 1}-02-10" for yr in range(2021, 2026)}
    AMD = "0009999999-24-000077"  # 10-K/A filed 2024-06-15 restating FY2023 revenue 1200 -> 1150
    Q = "0009999999-25-000050"    # a 10-Q: must never be used for annual values
    y = {yr: (f"{yr}-01-01", f"{yr}-12-31") for yr in range(2020, 2026)}

    rev = [
        row(800, y[2020][1], KF[2021], K[2021], start=y[2020][0]),             # comparative only
        row(1000, y[2021][1], KF[2021], K[2021], start=y[2021][0]), row(1000, y[2021][1], KF[2022], K[2022], start=y[2021][0]),
        row(1100, y[2022][1], KF[2022], K[2022], start=y[2022][0]), row(1100, y[2022][1], KF[2023], K[2023], start=y[2022][0]),
        row(1200, y[2023][1], KF[2023], K[2023], start=y[2023][0]),
        row(1150, y[2023][1], "2024-06-15", AMD, "10-K/A", start=y[2023][0]),
        row(1150, y[2023][1], KF[2024], K[2024], start=y[2023][0]),
        row(1300, y[2024][1], KF[2024], K[2024], start=y[2024][0]), row(1300, y[2024][1], KF[2025], K[2025], start=y[2024][0]),
        row(1500, y[2025][1], KF[2025], K[2025], start=y[2025][0]),
    ]
    old_rev = [r for r in rev if r["end"] <= "2021-12-31"]  # the synthetic company used an older revenue tag until FY2021
    new_rev = [r for r in rev if r["end"] > "2021-12-31"] + [row(350, "2025-03-31", "2025-05-01", Q, "10-Q", start="2025-01-01", fp="Q1")]

    def own(vals):
        out = []
        for yr, v in vals.items():
            out.append(row(v, y[yr][1], KF[yr], K[yr], start=y[yr][0]))
            if yr + 1 in K:
                out.append(row(v, y[yr][1], KF[yr + 1], K[yr + 1], start=y[yr][0]))
        return out

    def inst(vals):
        return [row(v, y[yr][1], KF[yr], K[yr]) for yr, v in vals.items()]

    years = [2021, 2022, 2023, 2024, 2025]
    g = {
        "SalesRevenueNet": {"units": {"USD": old_rev}},
        "Revenues": {"units": {"USD": new_rev}},
        "OperatingIncomeLoss": {"units": {"USD": own(dict(zip(years, [200, 220, 240, 260, 300])))}},
        "NetIncomeLoss": {"units": {"USD": own(dict(zip(years, [150, 160, 0, 190, 220])))}},  # FY2023 net income is a true zero
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest": {"units": {"USD": own(dict(zip(years, [190, 200, 210, 240, 280])))}},
        "IncomeTaxExpenseBenefit": {"units": {"USD": own(dict(zip(years, [40, 40, 42, 48, 56])))}},
        "NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": own(dict(zip(years, [250, 260, 270, 300, 330])))}},
        "PaymentsToAcquirePropertyPlantAndEquipment": {"units": {"USD": own(dict(zip(years, [50, 60, 70, 80, 90])))}},
        "DepreciationDepletionAndAmortization": {"units": {"USD": own(dict(zip(years, [30, 30, 35, 35, 40])))}},
        # interest expense deliberately not reported for FY2024 (missing, not zero)
        "InterestExpense": {"units": {"USD": [r for r in own(dict(zip(years, [10, 10, 12, 12, 15]))) if r["end"] != "2024-12-31"]}},
        "StockholdersEquity": {"units": {"USD": inst(dict(zip(years, [900, 950, 1000, 1100, 1200])))}},
        "LongTermDebtNoncurrent": {"units": {"USD": inst(dict(zip(years, [400, 400, 380, 360, 340])))}},
        "LongTermDebtCurrent": {"units": {"USD": inst(dict(zip(years, [20, 20, 20, 20, 20])))}},
        "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": inst(dict(zip(years, [100, 120, 140, 160, 180])))}},
        "Assets": {"units": {"USD": inst(dict(zip(years, [2000, 2100, 2200, 2300, 2400])))}},
        "Liabilities": {"units": {"USD": inst(dict(zip(years, [1100, 1150, 1200, 1200, 1200])))}},
        "ResearchAndDevelopmentExpense": {"units": {"EUR": own(dict(zip(years, [5, 5, 5, 5, 5])))}},  # must be rejected, never converted
        "EarningsPerShareDiluted": {"units": {"USD/shares": own(dict(zip(years, [1.5, 1.6, 0.0, 1.9, 2.2])))}},
    }
    return {"_synthetic": True, "cik": CIK, "entityName": SYN_NAME, "facts": {"us-gaap": g}}


def submissions():
    return {"_synthetic": True, "cik": str(CIK), "name": SYN_NAME, "tickers": ["SYNT"], "exchanges": ["TEST"], "sic": "7372",
            "sicDescription": "Services-Prepackaged Software", "fiscalYearEnd": "1231", "entityType": "operating",
            "filings": {"recent": {
                "accessionNumber": ["0009999999-25-000050", "0009999999-25-000001", "0009999999-24-000077", "0009999999-24-000001", "0009999999-24-000099"],
                "filingDate": ["2025-05-01", "2025-02-10", "2024-06-15", "2024-02-10", "2024-04-01"],
                "reportDate": ["2025-03-31", "2024-12-31", "2023-12-31", "2023-12-31", ""],
                "acceptanceDateTime": ["", "", "", "", ""],
                "form": ["10-Q", "10-K", "10-K/A", "10-K", "DEF 14A"],
                "primaryDocument": ["q1.htm", "k2024.htm", "ka2023.htm", "k2023.htm", "proxy.htm"],
                "isXBRL": [1, 1, 1, 1, 0]},
                "files": [{"name": "CIK0009999999-submissions-001.json", "filingFrom": "2010-01-01", "filingTo": "2014-12-31"},
                          {"name": "CIK0009999999-submissions-002.json", "filingFrom": "2015-01-01", "filingTo": "2019-12-31"}]}}
