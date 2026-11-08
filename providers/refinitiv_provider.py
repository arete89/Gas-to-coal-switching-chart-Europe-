"""LSEG (Refinitiv) Workspace data provider.

Setup:
  1. In LSEG Workspace, open "App Key Generator" (search bar), register an
     app, copy the App Key.
  2. Copy lseg-data.config.example.json (project root) to
     lseg-data.config.json and paste the key under
     sessions.desktop.workspace.app-key. The real file is gitignored.
  3. Keep Workspace open and logged in — the library talks to it over
     localhost, no separate credentials needed beyond the app key.
  4. Set config.DATA_SOURCE = "refinitiv".

RIC codes (config.py) are the standard Reuters front-month continuation
("c1") contracts:
  - TFMBMc1: ICE Dutch TTF Natural Gas, EUR/MWh
  - ATWMc1:  ICE Rotterdam Coal future (API2), USD/tonne
  - CFI2c1:  ICE EUA carbon futures, EUR/tonne CO2
  - EUR=:    EUR/USD spot

Note: the Argus/McCloskey API2 assessment (e.g. ARGCAATMc1) is the
"official" API2 benchmark and is what config.py's comments used to
reference, but it's a separately-licensed dataset — this account's
entitlement returned "User has no permission" for it. ATWMc1 is the ICE
*exchange* future for the same Rotterdam coal market and is entitled here;
it's a very close proxy for API2 (ICE's contract effectively tracks the
same delivery point) but not numerically identical to the Argus index.

If a RIC comes back "not found", it's been renamed/delisted — search
Workspace and update config.py. If it comes back "no permission", it's a
licensing gap, not a wrong RIC — use `ld.discovery.search()` to find an
alternate instrument for the same underlying that your account is entitled
to (see how ATWMc1 was found, above).
"""

import pandas as pd
import lseg.data as ld

import config
from providers.base import PriceProvider

_session_open = False


def _ensure_session():
    global _session_open
    if not _session_open:
        ld.open_session()
        _session_open = True


def _lookback_to_start(lookback: str) -> str:
    if lookback.endswith("mo"):
        delta = pd.DateOffset(months=int(lookback[:-2]))
    elif lookback.endswith("y"):
        delta = pd.DateOffset(years=int(lookback[:-1]))
    elif lookback.endswith("d"):
        delta = pd.DateOffset(days=int(lookback[:-1]))
    else:
        raise ValueError(f"Unrecognized lookback format: {lookback!r}")
    return (pd.Timestamp.today() - delta).strftime("%Y-%m-%d")


def _fetch_close(ric: str, lookback: str) -> pd.Series:
    _ensure_session()
    start = _lookback_to_start(lookback)
    end = pd.Timestamp.today().strftime("%Y-%m-%d")
    df = ld.get_history(universe=ric, start=start, end=end, interval="daily")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(-1)
    # Prefer the daily settlement price — it's published every trading day
    # even when a contract doesn't trade, unlike last-trade (TRDPRC_1/CLOSE),
    # which is important for a lower-volume series like API2 coal.
    col = next((c for c in df.columns if str(c).upper() in ("SETTLE", "CLOSE", "TRDPRC_1")), df.columns[0])

    s = pd.to_numeric(df[col], errors="coerce").dropna()
    s.index = pd.to_datetime(s.index).tz_localize(None)
    return s.rename(ric)


class RefinitivProvider(PriceProvider):
    def get_gas_price(self, lookback: str) -> pd.Series:
        return _fetch_close(config.RIC_GAS_TTF, lookback).rename("gas_eur_mwh")

    def get_coal_price(self, lookback: str) -> pd.Series:
        gas_index = self.get_gas_price(lookback).index
        coal_usd_t = _fetch_close(config.RIC_COAL_API2, lookback)
        fx = _fetch_close(config.RIC_FX_EURUSD, lookback)

        daily_index = pd.date_range(coal_usd_t.index.min(), gas_index.max(), freq="D")
        coal_usd_t_daily = coal_usd_t.reindex(daily_index).ffill()
        fx_daily = fx.reindex(daily_index).ffill().bfill()

        coal_eur_t = coal_usd_t_daily / fx_daily
        coal_eur_mwh = coal_eur_t / config.COAL_MWH_PER_TONNE
        return coal_eur_mwh.reindex(gas_index).ffill().rename("coal_eur_mwh")

    def get_carbon_price(self, lookback: str) -> pd.Series:
        gas_index = self.get_gas_price(lookback).index
        eua = _fetch_close(config.RIC_CARBON_EUA, lookback)
        return eua.reindex(gas_index).ffill().rename("carbon_eur_t")
