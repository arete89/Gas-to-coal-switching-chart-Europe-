"""Assumptions for the gas-to-coal switching model. Edit freely."""

# Which provider to use: "free" (yfinance/FRED proxies) or "refinitiv"
# (LSEG Workspace, real TTF/API2/EUA series).
DATA_SOURCE = "refinitiv"

LOOKBACK = "2y"

# Gas plant efficiency: fixed at the standard European market-benchmark
# efficiency (S&P Global Platts' European spark spread convention), on HHV —
# matches how TTF itself is quoted, so no LHV/HHV mismatch in the formula.
GAS_EFF = 0.4913

# Coal plant efficiency range (also HHV-consistent)
COAL_EFF_LOW = 0.36   # older subcritical coal plant
COAL_EFF_HIGH = 0.44  # modern supercritical/ultra-supercritical coal plant

# Number of discrete coal-efficiency layers to break the switching band into,
# evenly spaced across COAL_EFF_LOW..HIGH (e.g. 4 -> 36%, 38.7%, 41.3%, 44%)
N_COAL_SUBBANDS = 4

# CO2 emission factors, tCO2 per MWh of fuel thermal input (IPCC 2006 defaults,
# Vol.2 Ch.2 Table 2.2: natural gas 56.1 kgCO2/GJ, other bituminous coal 94.6 kgCO2/GJ)
EF_GAS_T_PER_MWH_TH = 0.202
EF_COAL_T_PER_MWH_TH = 0.341

# Coal calorific value used to convert $/tonne -> $/MWh(thermal).
# 6,000 kcal/kg NAR (the standard API2/Newcastle contract spec) = 25.12 GJ/t = 6.98 MWh/t
COAL_MWH_PER_TONNE = 6.98

# Carbon price fallback for the free provider only (no free, reliable daily
# EUA series exists — see README). Unused when DATA_SOURCE = "refinitiv",
# which pulls the real EUA series instead.
CARBON_PRICE_EUR_PER_T = 80.0
CARBON_PRICE_AS_OF = "2026-09-06"

# yfinance tickers used by the free provider
TICKER_GAS_TTF = "TTF=F"
TICKER_FX_EURUSD = "EURUSD=X"

# FRED series id used by the free provider (free, keyless CSV endpoint)
FRED_COAL_SERIES = "PCOALAUUSDM"  # Global price of Coal, Australia, monthly, USD/tonne

# RIC codes used by the refinitiv (LSEG Workspace) provider — standard
# Reuters front-month continuation ("c1") contracts. If Workspace returns no
# data for one of these, search the instrument in Workspace and correct it
# here rather than guessing a replacement.
RIC_GAS_TTF = "TFMBMc1"     # ICE Dutch TTF Natural Gas, EUR/MWh
RIC_COAL_API2 = "ATWMc1"     # ICE Rotterdam Coal future (API2), monthly continuation, USD/tonne
RIC_CARBON_EUA = "CFI2c1"   # ICE EUA carbon futures, EUR/tonne CO2
RIC_FX_EURUSD = "EUR="      # EUR/USD spot
