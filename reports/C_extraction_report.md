# C. Financial-data extraction report

Assessment date 2026-11-13 · generated 2026-11-13T12:25:44Z · source: SEC EDGAR (data.sec.gov companyfacts + submissions)

Values are USD millions as filed. '—' means the item was not reported for that period (never zero-filled). Concept = the us-gaap tag actually used.


## MICROSOFT CORP (MSFT) · CIK 0000789019 · model: corporate

SIC 7372 Services-Prepackaged Software · fiscal year end 0630 · 33,058 XBRL facts · 336 filings registered (18 10-K, 56 10-Q, 19 DEF 14A, 1 10-K/10-Q amendments)

| Item | concept | 2021-06-30 | 2022-06-30 | 2023-06-30 | 2024-06-30 | 2025-06-30 | 2026-06-30 |
|---|---|---:|---:|---:|---:|---:|---:|
| revenue | RevenueFromContractWithCustomerExcludingAssessedTax | 168,088 | 198,270 | 211,915 | 245,122 | 281,724 | 331,839 |
| net_income | NetIncomeLoss | 61,271 | 72,738 | 72,361 | 88,136 | 101,832 | 133,749 |
| pretax_income | IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest | 71,102 | 83,716 | 89,311 | 107,787 | 123,627 | 165,934 |
| income_tax | IncomeTaxExpenseBenefit | 9,831 | 10,978 | 16,950 | 19,651 | 21,795 | 32,185 |
| cfo | NetCashProvidedByUsedInOperatingActivities | 76,740 | 89,035 | 87,582 | 118,548 | 136,162 | 182,935 |
| total_assets | Assets | 333,779 | 364,840 | 411,976 | 512,163 | 619,003 | 758,376 |
| total_liabilities | Liabilities | 191,791 | 198,298 | 205,753 | 243,686 | 275,524 | 315,989 |
| equity | StockholdersEquity | 141,988 | 166,542 | 206,223 | 268,477 | 343,479 | 442,387 |
| cash | CashAndCashEquivalentsAtCarryingValue | 14,224 | 13,931 | 34,704 | 18,315 | 30,242 | 20,935 |
| diluted_eps | EarningsPerShareDiluted | 8.05 | 9.65 | 9.68 | 11.80 | 13.64 | 17.95 |
| operating_income | OperatingIncomeLoss | 69,916 | 83,383 | 88,523 | 109,433 | 128,528 | 155,237 |
| cost_of_revenue | CostOfGoodsAndServicesSold | 52,232 | 62,650 | 65,863 | 74,114 | 87,831 | 106,374 |
| rnd | ResearchAndDevelopmentExpense | 20,716 | 24,512 | 27,195 | 29,510 | 32,488 | 35,562 |
| capex | PaymentsToAcquirePropertyPlantAndEquipment | 20,622 | 23,886 | 28,107 | 44,477 | 64,551 | 115,948 |
| dna | — | — | — | — | — | — | — |
| interest_expense | InterestExpense, InterestExpenseNonoperating | 2,346 | 2,063 | 1,968 | 2,935 | 2,385 | 3,051 |
| debt_noncurrent | LongTermDebtNoncurrent | 50,074 | 47,032 | 41,990 | 42,688 | 40,152 | 31,067 |
| debt_current | LongTermDebtCurrent | 8,072 | 2,749 | 5,247 | 2,249 | 2,999 | 9,227 |
| commercial_paper | CommercialPaper | — | — | 0.00 | 6,693 | 0.00 | — |
| short_term_borrowings | — | — | — | — | — | — | — |
| current_assets | AssetsCurrent | 184,406 | 169,684 | 184,257 | 159,734 | 191,131 | 207,710 |
| current_liabilities | LiabilitiesCurrent | 88,657 | 95,082 | 104,149 | 125,286 | 141,218 | 168,825 |

ᴿ = value differs from the first-filed figure (restated or reclassified); both are kept.

**Normalised metrics (latest fiscal year)**

| Metric | value | status | formula |
|---|---:|---|---|
| revenue_growth | 17.8% | computed | `revenue[t] / revenue[t-1] - 1` |
| operating_margin | 46.8% | computed | `operating_income / revenue` |
| net_margin | 40.3% | computed | `net_income / revenue` |
| rnd_to_revenue | 10.7% | computed | `rnd / revenue` |
| capex_to_revenue | 34.9% | computed | `capex / revenue` |
| effective_tax_rate | 19.4% | computed | `income_tax / pretax_income` |
| liabilities_to_assets | 41.7% | computed | `total_liabilities / total_assets` |
| current_ratio | 1.23x | computed | `current_assets / current_liabilities` |
| return_on_equity | 30.2% | computed | `net_income / equity (period-end)` |
| interest_cover | 50.88x | computed | `operating_income / interest_expense` |
| free_cash_flow | 66,987 | computed | `cfo - capex` |
| fcf_to_operating_income | 43.2% | computed | `(cfo - capex) / operating_income` |
| ebitda | — | missing_input (dna) | `operating_income + dna` |
| total_debt | 40,294 | computed_partial (commercial_paper, short_term_borrowings) | `debt_noncurrent + debt_current + commercial_paper + short_term_borrowings` |
| net_debt | 19,359 | computed_partial (commercial_paper, short_term_borrowings) | `total_debt - cash` |
| net_debt_to_ebitda | — | missing_input (ebitda) | `net_debt / ebitda` |
| return_on_invested_capital | 27.1% | computed_partial (commercial_paper, short_term_borrowings) | `operating_income * (1 - income_tax/pretax_income) / (equity + total_debt - cash)` |

**Five-year summary (descriptive, unscored):** years_in_window 6; revenue_growth_sd 4.1%; revenue_growth_mean 14.6%; worst_revenue_drawdown 0.0%; operating_margin_sd 2.0%; fcf_positive_share 100.0%; roic_mean 31.0%

**CELI-100 engine:** status `insufficient` · reasons: Constructive Capability scored coverage 0% below 80%; Systemic Risk scored coverage 0% below 80%; Adaptability scored coverage 0% below 80%; Data Confidence 25.0 below 50


## NVIDIA CORP (NVDA) · CIK 0001045810 · model: corporate

SIC 3674 Semiconductors & Related Devices · fiscal year end 0131 · 27,281 XBRL facts · 416 filings registered (27 10-K, 85 10-Q, 29 DEF 14A, 4 10-K/10-Q amendments)

| Item | concept | 2021-01-31 | 2022-01-30 | 2023-01-29 | 2024-01-28 | 2025-01-26 | 2026-01-25 |
|---|---|---:|---:|---:|---:|---:|---:|
| revenue | Revenues | 16,675 | 26,914 | 26,974 | 60,922 | 130,497 | 215,938 |
| net_income | NetIncomeLoss | 4,332 | 9,752 | 4,368 | 29,760 | 72,880 | 120,067 |
| pretax_income | IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest | 4,409 | 9,941 | 4,181 | 33,818 | 84,026 | 141,450 |
| income_tax | IncomeTaxExpenseBenefit | 77.00 | 189 | -187 | 4,058 | 11,146 | 21,383 |
| cfo | NetCashProvidedByUsedInOperatingActivities | 5,822 | 9,108 | 5,641 | 28,090 | 64,089 | 102,718 |
| total_assets | Assets | 28,791 | 44,187 | 41,182 | 65,728 | 111,601 | 206,803 |
| total_liabilities | Liabilities | 11,898 | 17,575 | 19,081 | 22,750 | 32,274 | 49,510 |
| equity | StockholdersEquity | 16,893 | 26,612 | 22,101 | 42,978 | 79,327 | 157,293 |
| cash | CashAndCashEquivalentsAtCarryingValue | 847 | 1,990 | 3,389 | 7,280 | 8,589 | 10,605 |
| diluted_eps | EarningsPerShareDiluted | 1.73 ᴿ | 3.85 | 0.17 ᴿ | 1.19 ᴿ | 2.94 | 4.90 |
| operating_income | OperatingIncomeLoss | 4,532 | 10,041 | 4,224 | 32,972 | 81,453 | 130,387 |
| cost_of_revenue | CostOfRevenue | 6,279 | 9,439 | 11,618 | 16,621 | 32,639 | 62,475 |
| rnd | ResearchAndDevelopmentExpense | 3,924 | 5,268 | 7,339 | 8,675 | 12,914 | 18,497 |
| capex | PaymentsToAcquireProductiveAssets | — | 976 | 1,833 | 1,069 | 3,236 | 6,042 |
| dna | DepreciationDepletionAndAmortization | 1,098 | 1,174 | 1,544 | 1,508 | 1,864 | 2,843 |
| interest_expense | InterestExpense, InterestExpenseNonoperating | 184 | 236 | 262 | 257 | 247 | 259 |
| debt_noncurrent | LongTermDebtNoncurrent | 5,964 | 10,946 | 9,703 | 8,459 | 8,463 | 7,469 |
| debt_current | LongTermDebtCurrent | 999 | 0.00 | 1,250 | 1,250 | 0.00 | 999 |
| commercial_paper | CommercialPaper | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | — |
| short_term_borrowings | — | — | — | — | — | — | — |
| current_assets | AssetsCurrent | 16,055 | 28,829 | 23,073 | 44,345 | 80,126 | 125,605 |
| current_liabilities | LiabilitiesCurrent | 3,925 | 4,335 | 6,563 | 10,631 | 18,047 | 32,163 |

ᴿ = value differs from the first-filed figure (restated or reclassified); both are kept.

**Normalised metrics (latest fiscal year)**

| Metric | value | status | formula |
|---|---:|---|---|
| revenue_growth | 65.5% | computed | `revenue[t] / revenue[t-1] - 1` |
| operating_margin | 60.4% | computed | `operating_income / revenue` |
| net_margin | 55.6% | computed | `net_income / revenue` |
| rnd_to_revenue | 8.6% | computed | `rnd / revenue` |
| capex_to_revenue | 2.8% | computed | `capex / revenue` |
| effective_tax_rate | 15.1% | computed | `income_tax / pretax_income` |
| liabilities_to_assets | 23.9% | computed | `total_liabilities / total_assets` |
| current_ratio | 3.91x | computed | `current_assets / current_liabilities` |
| return_on_equity | 76.3% | computed | `net_income / equity (period-end)` |
| interest_cover | 503.42x | computed | `operating_income / interest_expense` |
| free_cash_flow | 96,676 | computed | `cfo - capex` |
| fcf_to_operating_income | 74.1% | computed | `(cfo - capex) / operating_income` |
| ebitda | 133,230 | computed | `operating_income + dna` |
| total_debt | 8,468 | computed_partial (commercial_paper, short_term_borrowings) | `debt_noncurrent + debt_current + commercial_paper + short_term_borrowings` |
| net_debt | -2,137 | computed_partial (commercial_paper, short_term_borrowings) | `total_debt - cash` |
| net_debt_to_ebitda | -0.02x | computed_partial (commercial_paper, short_term_borrowings) | `net_debt / ebitda` |
| return_on_invested_capital | 71.3% | computed_partial (commercial_paper, short_term_borrowings) | `operating_income * (1 - income_tax/pretax_income) / (equity + total_debt - cash)` |

**Five-year summary (descriptive, unscored):** years_in_window 6; revenue_growth_sd 44.7%; revenue_growth_mean 73.4%; worst_revenue_drawdown 0.0%; operating_margin_sd 17.5%; fcf_positive_share 100.0%; roic_mean 53.4%

**CELI-100 engine:** status `insufficient` · reasons: Constructive Capability scored coverage 0% below 80%; Systemic Risk scored coverage 0% below 80%; Adaptability scored coverage 0% below 80%; Data Confidence 25.0 below 50


## JPMORGAN CHASE & CO (JPM) · CIK 0000019617 · model: bank

SIC 6021 National Commercial Banks · fiscal year end 1231 · 55,228 XBRL facts · 487 filings registered (12 10-K, 38 10-Q, 12 DEF 14A, 0 10-K/10-Q amendments)

| Item | concept | 2020-12-31 | 2021-12-31 | 2022-12-31 | 2023-12-31 | 2024-12-31 | 2025-12-31 |
|---|---|---:|---:|---:|---:|---:|---:|
| revenue | Revenues | 119,951 ᴿ | 121,649 | 128,695 | 158,104 | 177,556 | 182,447 |
| net_income | NetIncomeLoss | 29,131 | 48,334 | 37,676 | 49,552 | 58,471 | 57,048 |
| pretax_income | IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest | 35,815 ᴿ | 59,562 | 46,166 | 61,612 | 75,081 | 72,595 |
| income_tax | IncomeTaxExpenseBenefit | 6,684 ᴿ | 11,228 | 8,490 | 12,060 | 16,610 | 15,547 |
| cfo | NetCashProvidedByUsedInOperatingActivities | -79,910 | 78,084 | 107,119 | 12,974 | -42,012 | -147,782 |
| total_assets | Assets | 3,384,757 ᴿ | 3,743,567 | 3,665,743 | 3,875,393 | 4,002,814 | 4,424,900 |
| total_liabilities | Liabilities | 3,105,403 ᴿ | 3,449,440 | 3,373,411 | 3,547,515 | 3,658,056 | 4,062,462 |
| equity | StockholdersEquity | 279,354 | 294,127 | 292,332 | 327,878 | 344,758 | 362,438 |
| cash | CashAndDueFromBanks | 24,874 | 26,438 | 27,697 | 29,066 | 23,372 | 21,742 |
| diluted_eps | EarningsPerShareDiluted | 8.88 | 15.36 | 12.09 | 16.23 | 19.75 | 20.02 |
| net_interest_income | InterestIncomeExpenseNet | 54,563 | 52,311 | 66,710 | 89,267 | 92,583 | 95,443 |
| noninterest_expense | NoninterestExpense | 66,656 | 71,343 | 76,140 | 87,172 | 91,797 | 95,640 |
| provision_credit_losses | ProvisionForLoanLeaseAndOtherLosses | 17,480 | -9,256 | 6,389 | 9,320 | 10,678 | 14,212 |
| deposits | Deposits | 2,144,257 | 2,462,303 | 2,340,179 | 2,400,688 | 2,406,032 | 2,559,320 |
| loans_net | FinancingReceivableExcludingAccruedInterestAfterAllowanceForCreditLoss | 984,525 | 1,061,328 | 1,115,921 | 1,301,286 | 1,323,643 | 1,467,664 |
| long_term_debt | LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities | 281,685 | 301,005 | 295,865 | 391,825 | 401,418 | 435,206 |

ᴿ = value differs from the first-filed figure (restated or reclassified); both are kept.

**Normalised metrics (latest fiscal year)**

| Metric | value | status | formula |
|---|---:|---|---|
| revenue_growth | 2.8% | computed | `revenue[t] / revenue[t-1] - 1` |
| return_on_equity | 15.7% | computed | `net_income / equity (period-end)` |
| return_on_assets | 1.3% | computed | `net_income / total_assets (period-end)` |
| equity_to_assets | 8.2% | computed | `equity / total_assets` |
| deposits_to_assets | 57.8% | computed | `deposits / total_assets` |
| loans_to_deposits | 57.3% | computed | `loans_net / deposits` |
| efficiency_ratio | 52.4% | computed | `noninterest_expense / revenue` |
| provision_to_loans | 1.0% | computed | `provision_credit_losses / loans_net` |
| net_interest_income_share | 52.3% | computed | `net_interest_income / revenue` |

**Five-year summary (descriptive, unscored):** years_in_window 6; revenue_growth_sd 7.9%; revenue_growth_mean 9.0%; worst_revenue_drawdown 0.0%; roe_mean 15.4%; efficiency_ratio_mean 55.4%

**CELI-100 engine:** status `insufficient` · reasons: Constructive Capability scored coverage 0% below 80%; Systemic Risk scored coverage 0% below 80%; Adaptability scored coverage 0% below 80%; Data Confidence 25.0 below 50


## Apple Inc. (AAPL) · CIK 0000320193 · model: corporate

SIC 3571 Electronic Computers · fiscal year end 0926 · 25,604 XBRL facts · 425 filings registered (33 10-K, 100 10-Q, 32 DEF 14A, 4 10-K/10-Q amendments)

| Item | concept | 2021-09-25 | 2022-09-24 | 2023-09-30 | 2024-09-28 | 2025-09-27 | 2026-09-26 |
|---|---|---:|---:|---:|---:|---:|---:|
| revenue | RevenueFromContractWithCustomerExcludingAssessedTax | 365,817 | 394,328 | 383,285 | 391,035 | 416,161 | 478,834 |
| net_income | NetIncomeLoss | 94,680 | 99,803 | 96,995 | 93,736 | 112,010 | 132,175 |
| pretax_income | IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest | 109,207 | 119,103 | 113,736 | 123,485 | 132,729 | 159,237 |
| income_tax | IncomeTaxExpenseBenefit | 14,527 | 19,300 | 16,741 | 29,749 | 20,719 | 27,062 |
| cfo | NetCashProvidedByUsedInOperatingActivities | 104,038 | 122,151 | 110,543 | 118,254 | 111,482 | 145,097 |
| total_assets | Assets | 351,002 | 352,755 | 352,583 | 364,980 | 359,241 | 404,548 |
| total_liabilities | Liabilities | 287,912 | 302,083 | 290,437 | 308,030 | 285,508 | 292,455 |
| equity | StockholdersEquity | 63,090 | 50,672 | 62,146 | 56,950 | 73,733 | 112,093 |
| cash | CashAndCashEquivalentsAtCarryingValue | 34,940 | 23,646 | 29,965 | 29,943 | 35,934 | 36,305 |
| diluted_eps | EarningsPerShareDiluted | 5.61 | 6.11 | 6.13 | 6.08 | 7.46 | 8.98 |
| operating_income | OperatingIncomeLoss | 108,949 | 119,437 | 114,301 | 123,216 | 133,050 | 158,063 |
| cost_of_revenue | CostOfGoodsAndServicesSold | 212,981 | 223,546 | 214,137 | 210,352 | 220,960 | 245,232 |
| rnd | ResearchAndDevelopmentExpense | 21,914 | 26,251 | 29,915 | 31,370 | 34,550 | 45,765 |
| capex | PaymentsToAcquirePropertyPlantAndEquipment | 11,085 | 10,708 | 10,959 | 9,447 | 12,715 | 9,041 |
| dna | DepreciationDepletionAndAmortization | 11,284 | 11,104 | 11,519 | 11,445 | 11,698 | 13,423 |
| interest_expense | InterestExpense | 2,645 | 2,931 | 3,933 | — | — | — |
| debt_noncurrent | LongTermDebtNoncurrent | 109,106 | 98,959 | 95,281 | 85,750 | 78,328 | 68,208 |
| debt_current | LongTermDebtCurrent | 9,613 | 11,128 | 9,822 | 10,912 | 12,350 | 9,906 |
| commercial_paper | CommercialPaper | 6,000 | 9,982 | 5,985 | 9,967 | 7,979 | 1,997 |
| short_term_borrowings | — | — | — | — | — | — | — |
| current_assets | AssetsCurrent | 134,836 | 135,405 | 143,566 | 152,987 | 147,957 | 173,857 |
| current_liabilities | LiabilitiesCurrent | 125,481 | 153,982 | 145,308 | 176,392 | 165,631 | 169,915 |

ᴿ = value differs from the first-filed figure (restated or reclassified); both are kept.

**Normalised metrics (latest fiscal year)**

| Metric | value | status | formula |
|---|---:|---|---|
| revenue_growth | 15.1% | computed | `revenue[t] / revenue[t-1] - 1` |
| operating_margin | 33.0% | computed | `operating_income / revenue` |
| net_margin | 27.6% | computed | `net_income / revenue` |
| rnd_to_revenue | 9.6% | computed | `rnd / revenue` |
| capex_to_revenue | 1.9% | computed | `capex / revenue` |
| effective_tax_rate | 17.0% | computed | `income_tax / pretax_income` |
| liabilities_to_assets | 72.3% | computed | `total_liabilities / total_assets` |
| current_ratio | 1.02x | computed | `current_assets / current_liabilities` |
| return_on_equity | 117.9% | computed | `net_income / equity (period-end)` |
| interest_cover | — | missing_input (interest_expense) | `operating_income / interest_expense` |
| free_cash_flow | 136,056 | computed | `cfo - capex` |
| fcf_to_operating_income | 86.1% | computed | `(cfo - capex) / operating_income` |
| ebitda | 171,486 | computed | `operating_income + dna` |
| total_debt | 80,111 | computed_partial (short_term_borrowings) | `debt_noncurrent + debt_current + commercial_paper + short_term_borrowings` |
| net_debt | 43,806 | computed_partial (short_term_borrowings) | `total_debt - cash` |
| net_debt_to_ebitda | 0.26x | computed_partial (short_term_borrowings) | `net_debt / ebitda` |
| return_on_invested_capital | 84.2% | computed_partial (short_term_borrowings) | `operating_income * (1 - income_tax/pretax_income) / (equity + total_debt - cash)` |

**Five-year summary (descriptive, unscored):** years_in_window 6; revenue_growth_sd 6.0%; revenue_growth_mean 5.7%; worst_revenue_drawdown 2.8%; operating_margin_sd 1.2%; fcf_positive_share 100.0%; roic_mean 74.5%

**CELI-100 engine:** status `insufficient` · reasons: Constructive Capability scored coverage 0% below 80%; Systemic Risk scored coverage 0% below 80%; Adaptability scored coverage 0% below 80%; Data Confidence 25.0 below 50


## AMAZON COM INC (AMZN) · CIK 0001018724 · model: corporate

SIC 5961 Retail-Catalog & Mail-Order Houses · fiscal year end 1231 · 30,289 XBRL facts · 411 filings registered (27 10-K, 81 10-Q, 27 DEF 14A, 2 10-K/10-Q amendments)

| Item | concept | 2020-12-31 | 2021-12-31 | 2022-12-31 | 2023-12-31 | 2024-12-31 | 2025-12-31 |
|---|---|---:|---:|---:|---:|---:|---:|
| revenue | RevenueFromContractWithCustomerExcludingAssessedTax | 386,064 | 469,822 | 513,983 | 574,785 | 637,959 | 716,924 |
| net_income | NetIncomeLoss | 21,331 | 33,364 | -2,722 | 30,425 | 59,248 | 77,670 |
| pretax_income | IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments | 24,178 | 38,151 | -5,936 | 37,557 | 68,614 | 97,311 |
| income_tax | IncomeTaxExpenseBenefit | 2,863 | 4,791 | -3,217 | 7,120 | 9,265 | 19,087 |
| cfo | NetCashProvidedByUsedInOperatingActivities | 66,064 | 46,327 | 46,752 | 84,946 | 115,877 | 139,514 |
| total_assets | Assets | 321,195 | 420,549 | 462,675 | 527,854 | 624,894 | 818,042 |
| total_liabilities | — | — | — | — | — | — | — |
| equity | StockholdersEquity | 93,404 | 138,245 | 146,043 | 201,875 | 285,970 | 411,065 |
| cash | CashAndCashEquivalentsAtCarryingValue | 42,122 | 36,220 | 53,888 | 73,387 | 78,779 | 86,810 |
| diluted_eps | EarningsPerShareDiluted | 2.09 ᴿ | 3.24 ᴿ | -0.27 | 2.90 | 5.53 | 7.17 |
| operating_income | OperatingIncomeLoss | 22,899 | 24,879 | 12,248 | 36,852 | 68,593 | 79,975 |
| cost_of_revenue | CostOfGoodsAndServicesSold | 233,307 | 272,344 | 288,831 | 304,739 | 326,288 | 356,414 |
| rnd | — | — | — | — | — | — | — |
| capex | PaymentsToAcquireProductiveAssets | 40,140 | 61,053 | 63,645 | 52,729 | 82,999 | 131,819 |
| dna | DepreciationDepletionAndAmortization | 25,180 ᴿ | 34,433 ᴿ | 41,921 | 48,663 | 52,795 | 65,756 |
| interest_expense | InterestExpense, InterestExpenseNonoperating | 1,647 | 1,809 | 2,367 | 3,182 | 2,406 | 2,274 |
| debt_noncurrent | LongTermDebtNoncurrent | 31,816 | 48,744 | 67,150 | 58,314 | 52,623 | 65,648 |
| debt_current | LongTermDebtCurrent | 1,155 | 1,491 | 2,999 | 8,494 | 5,017 | 2,748 |
| commercial_paper | — | — | — | — | — | — | — |
| short_term_borrowings | ShortTermBorrowings | — | — | — | 147 | 151 | 455 |
| current_assets | AssetsCurrent | 132,733 | 161,580 | 146,791 | 172,351 | 190,867 | 229,083 |
| current_liabilities | LiabilitiesCurrent | 126,385 | 142,266 | 155,393 | 164,917 | 179,431 | 218,005 |

ᴿ = value differs from the first-filed figure (restated or reclassified); both are kept.

**Normalised metrics (latest fiscal year)**

| Metric | value | status | formula |
|---|---:|---|---|
| revenue_growth | 12.4% | computed | `revenue[t] / revenue[t-1] - 1` |
| operating_margin | 11.2% | computed | `operating_income / revenue` |
| net_margin | 10.8% | computed | `net_income / revenue` |
| rnd_to_revenue | — | missing_input (rnd) | `rnd / revenue` |
| capex_to_revenue | 18.4% | computed | `capex / revenue` |
| effective_tax_rate | 19.6% | computed | `income_tax / pretax_income` |
| liabilities_to_assets | — | missing_input (total_liabilities) | `total_liabilities / total_assets` |
| current_ratio | 1.05x | computed | `current_assets / current_liabilities` |
| return_on_equity | 18.9% | computed | `net_income / equity (period-end)` |
| interest_cover | 35.17x | computed | `operating_income / interest_expense` |
| free_cash_flow | 7,695 | computed | `cfo - capex` |
| fcf_to_operating_income | 9.6% | computed | `(cfo - capex) / operating_income` |
| ebitda | 145,731 | computed | `operating_income + dna` |
| total_debt | 68,851 | computed_partial (commercial_paper) | `debt_noncurrent + debt_current + commercial_paper + short_term_borrowings` |
| net_debt | -17,959 | computed_partial (commercial_paper) | `total_debt - cash` |
| net_debt_to_ebitda | -0.12x | computed_partial (commercial_paper) | `net_debt / ebitda` |
| return_on_invested_capital | 16.4% | computed_partial (commercial_paper) | `operating_income * (1 - income_tax/pretax_income) / (equity + total_debt - cash)` |

**Five-year summary (descriptive, unscored):** years_in_window 6; revenue_growth_sd 4.3%; revenue_growth_mean 13.3%; worst_revenue_drawdown 0.0%; operating_margin_sd 3.3%; fcf_positive_share 60.0%; roic_mean 17.1%

**CELI-100 engine:** status `insufficient` · reasons: Constructive Capability scored coverage 0% below 80%; Systemic Risk scored coverage 0% below 80%; Adaptability scored coverage 0% below 80%; Data Confidence 25.0 below 50

