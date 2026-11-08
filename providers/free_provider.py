"""Free, keyless data provider.

Data quality notes (see README before trusting absolute levels):
  - Gas (TTF=F via yfinance): real daily TTF front-month, already EUR/MWh. Good.
  - Coal (FRED PCOALAUUSDM): monthly Newcastle/Australia benchmark, forward-filled
    to daily and converted from USD/tonne to EUR/MWh(th). This is NOT API2/ARA —
    it's the closest legitimate free daily-usable proxy. Replace with a real
    API2 feed via Refinitiv when available.
  - Carbon: no reliable free daily EUA series exists. Held flat at
    config.CARBON_PRICE_EUR_PER_T (update by hand until Refinitiv is wired in).
"""

import io
import urllib.request

import pandas as pd
import yfinance as yf

import config
from providers.base import PriceProvider

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"


def _fetch_fred_series(series_id: str) -> pd.Series:
    url = FRED_CSV_URL.format(series_id=series_id)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read()
    df = pd.read_csv(io.BytesIO(raw))
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")["value"]
    return pd.to_numeric(df, errors="coerce").dropna()


class FreeProvider(PriceProvider):
    def get_gas_price(self, lookback: str) -> pd.Series:
        hist = yf.Ticker(config.TICKER_GAS_TTF).history(period=lookback, interval="1d")
        if hist.empty:
            raise RuntimeError(f"No data returned for {config.TICKER_GAS_TTF}")
        s = hist["Close"]
        s.index = s.index.tz_localize(None)
        return s.rename("gas_eur_mwh")

    def get_coal_price(self, lookback: str) -> pd.Series:
        gas_index = self.get_gas_price(lookback).index

        coal_usd_t = _fetch_fred_series(config.FRED_COAL_SERIES)

        fx_hist = yf.Ticker(config.TICKER_FX_EURUSD).history(period=lookback, interval="1d")
        fx = fx_hist["Close"]
        fx.index = fx.index.tz_localize(None)

        daily_index = pd.date_range(coal_usd_t.index.min(), gas_index.max(), freq="D")
        coal_usd_t_daily = coal_usd_t.reindex(daily_index).ffill()
        fx_daily = fx.reindex(daily_index).ffill().bfill()

        coal_eur_t = coal_usd_t_daily / fx_daily
        coal_eur_mwh = coal_eur_t / config.COAL_MWH_PER_TONNE
        return coal_eur_mwh.reindex(gas_index).ffill().rename("coal_eur_mwh")

    def get_carbon_price(self, lookback: str) -> pd.Series:
        gas_index = self.get_gas_price(lookback).index
        return pd.Series(config.CARBON_PRICE_EUR_PER_T, index=gas_index, name="carbon_eur_t")
