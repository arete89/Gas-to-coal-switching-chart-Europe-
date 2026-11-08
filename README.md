# Gas-to-coal switching chart (Europe)

Plots the TTF gas price against gas-to-coal switching thresholds: for each of
several coal plant efficiencies, the gas price at which a gas plant is
cost-indifferent to that coal plant. When the gas line is below a threshold,
gas is cheaper to run than coal at that efficiency; above it, coal wins.

## How it works

For a gas plant of efficiency `eta_gas` and a coal plant of efficiency
`eta_coal`, variable cost per MWh of electricity is fuel cost plus carbon cost,
divided by efficiency. Setting the two equal and solving for the gas price:

```
gas_switch = eta_gas * (coal/eta_coal + carbon * (EF_coal/eta_coal - EF_gas/eta_gas))
```

- Gas efficiency is fixed at **49.13%**, the S&P Global Platts European
  spark-spread benchmark (HHV basis, consistent with how TTF is quoted).
- Coal efficiency is swept from 36% to 44% in `N_COAL_SUBBANDS` steps, giving
  one threshold line per step. Higher coal efficiency always gives a lower
  threshold, so the lines never cross.
- Emission factors are IPCC 2006 defaults (gas 0.202, coal 0.341 tCO2/MWh thermal).

See `switching.py` for the derivation.

## Setup

```
pip install -r requirements.txt
python3 main.py
```

This writes `gas_coal_switching_chart.png`. Choose the data source with
`DATA_SOURCE` in `config.py`.

### `DATA_SOURCE = "refinitiv"` (LSEG Workspace)

| Input | RIC | Notes |
|---|---|---|
| Gas | `TFMBMc1` | ICE Dutch TTF, EUR/MWh |
| Coal | `ATWMc1` | ICE Rotterdam Coal (API2), USD/tonne, converted with `EUR=` and a calorific value |
| Carbon | `CFI2c1` | ICE EUA front-month, EUR/tonne CO2 |

Requires an LSEG Workspace subscription with the desktop app open and logged in.

1. In Workspace, search "App Key Generator", register an app with only
   **Eikon Data API** ticked, and copy the key.
2. Copy `lseg-data.config.example.json` to `lseg-data.config.json` and paste
   the key in. That file is gitignored; never commit it.

Entitlements vary by account. If a RIC returns "no permission", it's a
licensing gap rather than a wrong RIC. Use `ld.discovery.search()` to find
an equivalent instrument you are entitled to. For example, the Argus API2
assessment (`ARGCAATMc1`) is a separate add-on, which is why this project
uses the ICE exchange future instead.

### `DATA_SOURCE = "free"` (no account)

| Input | Source | Quality |
|---|---|---|
| Gas | `yfinance` `TTF=F` | Real daily TTF |
| Coal | FRED `PCOALAUUSDM` (Newcastle), monthly, forward-filled | Proxy, not API2 |
| Carbon | Flat `CARBON_PRICE_EUR_PER_T` in `config.py` | Manual assumption; no free daily EUA feed exists |

## Configuration

Everything adjustable lives in `config.py`: efficiencies, number of coal
levels, emission factors, coal calorific value, lookback window, RIC codes.

To add another data source, implement the `PriceProvider` interface in
`providers/base.py` and register it in `main.py`.

## Data licensing

Market data from LSEG/ICE is licensed. This repository contains no market
data and the generated chart is gitignored. Check your LSEG agreement before
publishing charts or data derived from it.

## Disclaimer

For analysis and education only, not investment advice. Efficiency and
emission assumptions are simplifications; real dispatch also depends on plant
availability, start-up costs, grid constraints and contracts.

