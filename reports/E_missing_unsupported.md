# E. Missing and unsupported indicators

Assessment date 2026-11-13. No WACC, cost of equity, sector threshold or scoring scale is assumed, so no CELI indicator is scored yet.


## MICROSOFT CORP (MSFT) · corporate model

| Indicator | status | reason | evidence available |
|---|---|---|---|
| ROIC_5Y | evidence_available_not_scored | No calibrated cost-of-capital benchmark; WACC is not assumed | return_on_invested_capital, return_on_equity |
| FCF_DUR | evidence_available_not_scored | No calibrated scale for cash-flow conversion | free_cash_flow, fcf_to_operating_income |
| REINVEST | evidence_available_not_scored | Reinvestment quality is an analyst judgement | capex_to_revenue, rnd_to_revenue |
| REV_DUR | evidence_available_not_scored | No calibrated volatility scale; the pilot found growth was penalised as volatility | revenue_growth, operating_margin |
| WORKFORCE | unsupported_by_sec_xbrl | Human-capital disclosures are narrative (10-K Item 1); needs analyst extraction | — |
| ENV_OUT | unsupported_by_sec_xbrl | Emissions and environmental outcomes are in sustainability reports / EPA data, not SEC XBRL | — |
| FIN_FRAG | evidence_available_not_scored | No sector leverage thresholds calibrated | interest_cover, liabilities_to_assets, current_ratio |
| GOV_CONC | unsupported_by_sec_xbrl | Board and control concentration need DEF 14A proxy extraction | — |
| AUDIT_INT | unsupported_by_sec_xbrl | Needs auditor's report, Item 9A controls and restatement review; amendment/restatement flags below are an input, not a score | — |
| REG_LEGAL | unsupported_by_sec_xbrl | Needs enforcement databases (SEC litigation, DOJ, CFPB, EPA) and contingency notes | — |
| OP_HARM | unsupported_by_sec_xbrl | Needs verified incident sources (OSHA, EPA ECHO, recalls) | — |
| OP_RES | evidence_available_not_scored | Needs a longer window (10y) and a calibrated drawdown scale | revenue_growth |
| BM_ADAPT | unsupported_by_sec_xbrl | Business-model adaptability is an analyst judgement | — |
| REV_DIV | unsupported_by_sec_xbrl | Segment and product revenue are dimensional XBRL, not in companyfacts; needs filing-level XBRL parsing | — |
| GEO_SUPPLY | unsupported_by_sec_xbrl | Geographic revenue is dimensional XBRL; supply-chain risk needs risk-factor extraction | — |
| INNOV | evidence_available_not_scored | R&D intensity alone does not measure innovation capability; analyst review needed | rnd_to_revenue |

**Metrics not fully computable (any year in window):**

- ebitda: missing_input (dna)
- net_debt: computed_partial (commercial_paper, short_term_borrowings)
- net_debt: computed_partial (short_term_borrowings)
- net_debt_to_ebitda: missing_input (ebitda)
- return_on_invested_capital: computed_partial (commercial_paper, short_term_borrowings)
- return_on_invested_capital: computed_partial (short_term_borrowings)
- total_debt: computed_partial (commercial_paper, short_term_borrowings)
- total_debt: computed_partial (short_term_borrowings)

**Statement items not reported for at least one year:** commercial_paper, dna, short_term_borrowings

## NVIDIA CORP (NVDA) · corporate model

| Indicator | status | reason | evidence available |
|---|---|---|---|
| ROIC_5Y | evidence_available_not_scored | No calibrated cost-of-capital benchmark; WACC is not assumed | return_on_invested_capital, return_on_equity |
| FCF_DUR | evidence_available_not_scored | No calibrated scale for cash-flow conversion | free_cash_flow, fcf_to_operating_income |
| REINVEST | evidence_available_not_scored | Reinvestment quality is an analyst judgement | capex_to_revenue, rnd_to_revenue |
| REV_DUR | evidence_available_not_scored | No calibrated volatility scale; the pilot found growth was penalised as volatility | revenue_growth, operating_margin |
| WORKFORCE | unsupported_by_sec_xbrl | Human-capital disclosures are narrative (10-K Item 1); needs analyst extraction | — |
| ENV_OUT | unsupported_by_sec_xbrl | Emissions and environmental outcomes are in sustainability reports / EPA data, not SEC XBRL | — |
| FIN_FRAG | evidence_available_not_scored | No sector leverage thresholds calibrated | net_debt_to_ebitda, interest_cover, liabilities_to_assets, current_ratio |
| GOV_CONC | unsupported_by_sec_xbrl | Board and control concentration need DEF 14A proxy extraction | — |
| AUDIT_INT | unsupported_by_sec_xbrl | Needs auditor's report, Item 9A controls and restatement review; amendment/restatement flags below are an input, not a score | — |
| REG_LEGAL | unsupported_by_sec_xbrl | Needs enforcement databases (SEC litigation, DOJ, CFPB, EPA) and contingency notes | — |
| OP_HARM | unsupported_by_sec_xbrl | Needs verified incident sources (OSHA, EPA ECHO, recalls) | — |
| OP_RES | evidence_available_not_scored | Needs a longer window (10y) and a calibrated drawdown scale | revenue_growth |
| BM_ADAPT | unsupported_by_sec_xbrl | Business-model adaptability is an analyst judgement | — |
| REV_DIV | unsupported_by_sec_xbrl | Segment and product revenue are dimensional XBRL, not in companyfacts; needs filing-level XBRL parsing | — |
| GEO_SUPPLY | unsupported_by_sec_xbrl | Geographic revenue is dimensional XBRL; supply-chain risk needs risk-factor extraction | — |
| INNOV | evidence_available_not_scored | R&D intensity alone does not measure innovation capability; analyst review needed | rnd_to_revenue |

**Metrics not fully computable (any year in window):**

- net_debt: computed_partial (commercial_paper, short_term_borrowings)
- net_debt: computed_partial (short_term_borrowings)
- net_debt_to_ebitda: computed_partial (commercial_paper, short_term_borrowings)
- net_debt_to_ebitda: computed_partial (short_term_borrowings)
- return_on_invested_capital: computed_partial (commercial_paper, short_term_borrowings)
- return_on_invested_capital: computed_partial (short_term_borrowings)
- total_debt: computed_partial (commercial_paper, short_term_borrowings)
- total_debt: computed_partial (short_term_borrowings)

**Statement items not reported for at least one year:** capex, commercial_paper, short_term_borrowings

## JPMORGAN CHASE & CO (JPM) · bank model

| Indicator | status | reason | evidence available |
|---|---|---|---|
| ROIC_5Y | evidence_available_not_scored | No calibrated cost-of-equity benchmark; not assumed | return_on_equity, return_on_assets |
| FCF_DUR | not_applicable | Free-cash-flow conversion is not meaningful for a bank | — |
| REINVEST | unsupported_by_sec_xbrl | Not derivable from SEC XBRL | — |
| REV_DUR | evidence_available_not_scored | No calibrated volatility scale | revenue_growth, efficiency_ratio |
| WORKFORCE | unsupported_by_sec_xbrl | Human-capital disclosures are narrative (10-K Item 1); needs analyst extraction | — |
| ENV_OUT | unsupported_by_sec_xbrl | Emissions and environmental outcomes are in sustainability reports / EPA data, not SEC XBRL | — |
| FIN_FRAG | evidence_available_not_scored | Bank fragility needs CET1, LCR and NSFR from regulatory reports (FR Y-9C / Pillar 3), not in XBRL companyfacts | equity_to_assets, loans_to_deposits, deposits_to_assets |
| GOV_CONC | unsupported_by_sec_xbrl | Board and control concentration need DEF 14A proxy extraction | — |
| AUDIT_INT | unsupported_by_sec_xbrl | Needs auditor's report, Item 9A controls and restatement review; amendment/restatement flags below are an input, not a score | — |
| REG_LEGAL | unsupported_by_sec_xbrl | Needs enforcement databases (SEC litigation, DOJ, CFPB, EPA) and contingency notes | — |
| OP_HARM | unsupported_by_sec_xbrl | Needs verified incident sources (OSHA, EPA ECHO, recalls) | — |
| OP_RES | evidence_available_not_scored | Needs a longer window and a calibrated scale | revenue_growth, provision_to_loans |
| BM_ADAPT | unsupported_by_sec_xbrl | Business-model adaptability is an analyst judgement | — |
| REV_DIV | unsupported_by_sec_xbrl | Segment and product revenue are dimensional XBRL, not in companyfacts; needs filing-level XBRL parsing | — |
| GEO_SUPPLY | unsupported_by_sec_xbrl | Geographic revenue is dimensional XBRL; supply-chain risk needs risk-factor extraction | — |
| INNOV | unsupported_by_sec_xbrl | Not derivable from SEC XBRL | — |

## Apple Inc. (AAPL) · corporate model

| Indicator | status | reason | evidence available |
|---|---|---|---|
| ROIC_5Y | evidence_available_not_scored | No calibrated cost-of-capital benchmark; WACC is not assumed | return_on_invested_capital, return_on_equity |
| FCF_DUR | evidence_available_not_scored | No calibrated scale for cash-flow conversion | free_cash_flow, fcf_to_operating_income |
| REINVEST | evidence_available_not_scored | Reinvestment quality is an analyst judgement | capex_to_revenue, rnd_to_revenue |
| REV_DUR | evidence_available_not_scored | No calibrated volatility scale; the pilot found growth was penalised as volatility | revenue_growth, operating_margin |
| WORKFORCE | unsupported_by_sec_xbrl | Human-capital disclosures are narrative (10-K Item 1); needs analyst extraction | — |
| ENV_OUT | unsupported_by_sec_xbrl | Emissions and environmental outcomes are in sustainability reports / EPA data, not SEC XBRL | — |
| FIN_FRAG | evidence_available_not_scored | No sector leverage thresholds calibrated | net_debt_to_ebitda, interest_cover, liabilities_to_assets, current_ratio |
| GOV_CONC | unsupported_by_sec_xbrl | Board and control concentration need DEF 14A proxy extraction | — |
| AUDIT_INT | unsupported_by_sec_xbrl | Needs auditor's report, Item 9A controls and restatement review; amendment/restatement flags below are an input, not a score | — |
| REG_LEGAL | unsupported_by_sec_xbrl | Needs enforcement databases (SEC litigation, DOJ, CFPB, EPA) and contingency notes | — |
| OP_HARM | unsupported_by_sec_xbrl | Needs verified incident sources (OSHA, EPA ECHO, recalls) | — |
| OP_RES | evidence_available_not_scored | Needs a longer window (10y) and a calibrated drawdown scale | revenue_growth |
| BM_ADAPT | unsupported_by_sec_xbrl | Business-model adaptability is an analyst judgement | — |
| REV_DIV | unsupported_by_sec_xbrl | Segment and product revenue are dimensional XBRL, not in companyfacts; needs filing-level XBRL parsing | — |
| GEO_SUPPLY | unsupported_by_sec_xbrl | Geographic revenue is dimensional XBRL; supply-chain risk needs risk-factor extraction | — |
| INNOV | evidence_available_not_scored | R&D intensity alone does not measure innovation capability; analyst review needed | rnd_to_revenue |

**Metrics not fully computable (any year in window):**

- interest_cover: missing_input (interest_expense)
- net_debt: computed_partial (short_term_borrowings)
- net_debt_to_ebitda: computed_partial (short_term_borrowings)
- return_on_invested_capital: computed_partial (short_term_borrowings)
- total_debt: computed_partial (short_term_borrowings)

**Statement items not reported for at least one year:** interest_expense, short_term_borrowings

## AMAZON COM INC (AMZN) · corporate model

| Indicator | status | reason | evidence available |
|---|---|---|---|
| ROIC_5Y | evidence_available_not_scored | No calibrated cost-of-capital benchmark; WACC is not assumed | return_on_invested_capital, return_on_equity |
| FCF_DUR | evidence_available_not_scored | No calibrated scale for cash-flow conversion | free_cash_flow, fcf_to_operating_income |
| REINVEST | evidence_available_not_scored | Reinvestment quality is an analyst judgement | capex_to_revenue |
| REV_DUR | evidence_available_not_scored | No calibrated volatility scale; the pilot found growth was penalised as volatility | revenue_growth, operating_margin |
| WORKFORCE | unsupported_by_sec_xbrl | Human-capital disclosures are narrative (10-K Item 1); needs analyst extraction | — |
| ENV_OUT | unsupported_by_sec_xbrl | Emissions and environmental outcomes are in sustainability reports / EPA data, not SEC XBRL | — |
| FIN_FRAG | evidence_available_not_scored | No sector leverage thresholds calibrated | net_debt_to_ebitda, interest_cover, current_ratio |
| GOV_CONC | unsupported_by_sec_xbrl | Board and control concentration need DEF 14A proxy extraction | — |
| AUDIT_INT | unsupported_by_sec_xbrl | Needs auditor's report, Item 9A controls and restatement review; amendment/restatement flags below are an input, not a score | — |
| REG_LEGAL | unsupported_by_sec_xbrl | Needs enforcement databases (SEC litigation, DOJ, CFPB, EPA) and contingency notes | — |
| OP_HARM | unsupported_by_sec_xbrl | Needs verified incident sources (OSHA, EPA ECHO, recalls) | — |
| OP_RES | evidence_available_not_scored | Needs a longer window (10y) and a calibrated drawdown scale | revenue_growth |
| BM_ADAPT | unsupported_by_sec_xbrl | Business-model adaptability is an analyst judgement | — |
| REV_DIV | unsupported_by_sec_xbrl | Segment and product revenue are dimensional XBRL, not in companyfacts; needs filing-level XBRL parsing | — |
| GEO_SUPPLY | unsupported_by_sec_xbrl | Geographic revenue is dimensional XBRL; supply-chain risk needs risk-factor extraction | — |
| INNOV | evidence_missing | Required filed figures not reported | — |

**Metrics not fully computable (any year in window):**

- effective_tax_rate: undefined (pretax_income is -5936000000)
- liabilities_to_assets: missing_input (total_liabilities)
- net_debt: computed_partial (commercial_paper)
- net_debt: computed_partial (commercial_paper, short_term_borrowings)
- net_debt_to_ebitda: computed_partial (commercial_paper)
- net_debt_to_ebitda: computed_partial (commercial_paper, short_term_borrowings)
- return_on_invested_capital: computed_partial (commercial_paper)
- return_on_invested_capital: computed_partial (commercial_paper, short_term_borrowings)
- return_on_invested_capital: undefined (pretax income or invested capital not positive)
- rnd_to_revenue: missing_input (rnd)
- total_debt: computed_partial (commercial_paper)
- total_debt: computed_partial (commercial_paper, short_term_borrowings)

**Statement items not reported for at least one year:** commercial_paper, rnd, short_term_borrowings, total_liabilities
