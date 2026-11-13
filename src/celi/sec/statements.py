"""Financial statement extraction: XBRL tag mapping and the five-year annual history.

Each line item lists candidate us-gaap concepts in priority order. The choice is made per
fiscal year (companies switch tags over time) and the concept actually used is recorded.
Debt components are kept separate and never netted against each other here.
"""
from __future__ import annotations

from .facts import FactIndex, Selection, fiscal_year_ends

# item: (flow?, unit kind, [concepts in priority order])
COMMON = {
    "revenue": (True, "monetary", ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet"]),
    "net_income": (True, "monetary", ["NetIncomeLoss"]),
    "pretax_income": (True, "monetary", ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
                                         "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"]),
    "income_tax": (True, "monetary", ["IncomeTaxExpenseBenefit"]),
    "cfo": (True, "monetary", ["NetCashProvidedByUsedInOperatingActivities"]),
    "total_assets": (False, "monetary", ["Assets"]),
    "total_liabilities": (False, "monetary", ["Liabilities"]),
    "equity": (False, "monetary", ["StockholdersEquity"]),
    "cash": (False, "monetary", ["CashAndCashEquivalentsAtCarryingValue"]),
    "diluted_eps": (True, "per_share", ["EarningsPerShareDiluted"]),
}
CORPORATE = {
    "operating_income": (True, "monetary", ["OperatingIncomeLoss"]),
    "cost_of_revenue": (True, "monetary", ["CostOfRevenue", "CostOfGoodsAndServicesSold"]),
    "rnd": (True, "monetary", ["ResearchAndDevelopmentExpense"]),
    "capex": (True, "monetary", ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"]),
    "dna": (True, "monetary", ["DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet", "DepreciationAndAmortization",
                               "DepreciationAmortizationAndOther"]),
    "interest_expense": (True, "monetary", ["InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt"]),
    "debt_noncurrent": (False, "monetary", ["LongTermDebtNoncurrent"]),
    "debt_current": (False, "monetary", ["LongTermDebtCurrent"]),
    "commercial_paper": (False, "monetary", ["CommercialPaper"]),
    "short_term_borrowings": (False, "monetary", ["ShortTermBorrowings"]),
    "current_assets": (False, "monetary", ["AssetsCurrent"]),
    "current_liabilities": (False, "monetary", ["LiabilitiesCurrent"]),
}
BANK = {
    "net_interest_income": (True, "monetary", ["InterestIncomeExpenseNet"]),
    "noninterest_expense": (True, "monetary", ["NoninterestExpense"]),
    "provision_credit_losses": (True, "monetary", ["ProvisionForLoanLeaseAndOtherLosses", "ProvisionForLoanAndLeaseLosses", "ProvisionForCreditLossesExcludingAccruedInterest"]),
    "deposits": (False, "monetary", ["Deposits"]),
    "loans_net": (False, "monetary", ["LoansAndLeasesReceivableNetReportedAmount", "FinancingReceivableExcludingAccruedInterestAfterAllowanceForCreditLoss"]),
    "long_term_debt": (False, "monetary", ["LongTermDebt"]),
}
ANCHORS = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "NetIncomeLoss", "NetCashProvidedByUsedInOperatingActivities"]


def item_map(model: str) -> dict:
    if model == "bank":
        return {**COMMON, **BANK}
    if model == "corporate":
        return {**COMMON, **CORPORATE}
    raise ValueError(f"No statement model for {model!r}")


def select_item(index: FactIndex, item: tuple, end: str, asof: str) -> Selection | None:
    flow, kind, concepts = item
    for c in concepts:
        s = index.select(c, end, asof, flow=flow, kind=kind)
        if s is not None:
            return s
    return None


def annual_history(index: FactIndex, model: str, asof: str, years: int = 5) -> dict:
    """{'periods': [...], 'items': {item: {end: Selection|None}}} for the last `years` fiscal years (+1 for growth)."""
    ends = fiscal_year_ends(index, asof, ANCHORS)[-(years + 1):]
    items = item_map(model)
    table = {name: {e: select_item(index, spec, e, asof) for e in ends} for name, spec in items.items()}
    return {"model": model, "asof": asof, "periods": ends, "items": table}
