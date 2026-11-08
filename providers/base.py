from abc import ABC, abstractmethod

import pandas as pd


class PriceProvider(ABC):
    """Daily price series needed for the gas-to-coal switching calc.

    All three series must share a common daily DatetimeIndex and units:
      - gas price:    EUR / MWh (thermal, HHV as quoted at TTF)
      - coal price:   EUR / MWh (thermal)
      - carbon price: EUR / tonne CO2
    """

    @abstractmethod
    def get_gas_price(self, lookback: str) -> pd.Series:
        ...

    @abstractmethod
    def get_coal_price(self, lookback: str) -> pd.Series:
        ...

    @abstractmethod
    def get_carbon_price(self, lookback: str) -> pd.Series:
        ...

    def get_all(self, lookback: str) -> pd.DataFrame:
        gas = self.get_gas_price(lookback)
        coal = self.get_coal_price(lookback)
        carbon = self.get_carbon_price(lookback)
        df = pd.concat({"gas": gas, "coal": coal, "carbon": carbon}, axis=1)
        return df.reindex(gas.index).ffill().dropna()
