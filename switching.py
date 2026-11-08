"""Gas-to-coal switching price calculation.

At the switching price, a gas plant's variable cost per MWh(e) equals a coal
plant's variable cost per MWh(e):

    gas_price/eta_gas + carbon*EF_gas/eta_gas = coal_price/eta_coal + carbon*EF_coal/eta_coal

Solving for gas_price gives the TTF-equivalent price at which gas and coal
dispatch are indifferent, for a given pair of plant efficiencies:

    gas_switch = eta_gas * (coal_price/eta_coal + carbon*(EF_coal/eta_coal - EF_gas/eta_gas))

Below gas_switch, gas is cheaper to run than coal (for that efficiency pair);
above it, coal is cheaper. Gas efficiency is held fixed at the European
market-benchmark value (config.GAS_EFF), so sweeping only the coal
efficiency range gives one threshold price per coal plant efficiency —
higher coal efficiency always yields a strictly lower threshold (harder for
gas to beat), so the thresholds never cross.
"""

import pandas as pd

import config


def switching_price(coal_price, carbon_price, eta_gas, eta_coal):
    coal_term = coal_price / eta_coal
    carbon_term = carbon_price * (config.EF_COAL_T_PER_MWH_TH / eta_coal
                                   - config.EF_GAS_T_PER_MWH_TH / eta_gas)
    return eta_gas * (coal_term + carbon_term)


def coal_efficiency_levels():
    """N evenly spaced coal-plant efficiencies spanning config.COAL_EFF_LOW..HIGH."""
    n = config.N_COAL_SUBBANDS
    lo, hi = config.COAL_EFF_LOW, config.COAL_EFF_HIGH
    if n == 1:
        return [lo]
    step = (hi - lo) / (n - 1)
    return [lo + i * step for i in range(n)]


def compute_thresholds(df: pd.DataFrame) -> pd.DataFrame:
    """df must have columns: gas, coal, carbon.

    Adds one switching-price column per discrete coal efficiency level in
    coal_efficiency_levels(): the TTF-equivalent gas price at which a
    European-average-efficiency gas plant (config.GAS_EFF) is indifferent
    to a coal plant at that efficiency. Below the column's value, gas beats
    that coal plant; above it, coal wins.
    """
    out = df.copy()
    for level in coal_efficiency_levels():
        out[f"coal_eff_{level:.3f}"] = switching_price(df["coal"], df["carbon"], config.GAS_EFF, level)
    return out
