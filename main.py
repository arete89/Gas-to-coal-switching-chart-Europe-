import config
from providers.free_provider import FreeProvider
from providers.refinitiv_provider import RefinitivProvider
from switching import compute_thresholds
from plot import plot_switching_chart

PROVIDERS = {
    "free": FreeProvider,
    "refinitiv": RefinitivProvider,
}


def main():
    provider = PROVIDERS[config.DATA_SOURCE]()
    df = provider.get_all(config.LOOKBACK)
    df = compute_thresholds(df)

    out_path = "gas_coal_switching_chart.png"
    plot_switching_chart(df, out_path)
    print(f"Chart saved to {out_path}")
    print(df.tail())


if __name__ == "__main__":
    main()
