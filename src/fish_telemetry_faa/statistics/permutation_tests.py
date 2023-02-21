import numpy as np
from numpy.random import lognormal
from scipy.stats._resampling import permutation_test

from src.fish_telemetry_faa.utils.data_loader import init_standard_data, init_unconstrained_tag_data


def statistic_mean_diff(x, y, axis=0):
    return np.mean(x, axis=axis) - np.mean(y, axis=axis)


def run_permutation_test_water_columns(unconstrained=False):
    if unconstrained:
        df = init_unconstrained_tag_data()
    else:
        df = init_standard_data()
    df["water_column"] = "ERROR"
    df.loc[df["Depth [m] (est. or from tag)"] < 3, "water_column"] = "0-3m"
    df.loc[(3 <= df["Depth [m] (est. or from tag)"]) & (
            df["Depth [m] (est. or from tag)"] < 6), "water_column"] = "3-6m"
    df.loc[6 <= df["Depth [m] (est. or from tag)"], "water_column"] = "6-9m"
    # only look at day values
    df = df.loc[df["time_of_day"] == "Day"]
    data_03 = df.loc[df["water_column"] == "0-3m", "time_numeric"]
    data_36 = df.loc[df["water_column"] == "3-6m", "time_numeric"]
    data_69 = df.loc[df["water_column"] == "6-9m", "time_numeric"]

    rng = np.random.default_rng(0)
    print(f"From underlying truth: {statistic_mean_diff(data_03, data_36)}")
    res_1 = permutation_test((data_03,
                              data_36),
                             statistic_mean_diff,
                             n_resamples=10000,
                             vectorized=True,
                             alternative='less', random_state=rng)
    print("03 vs 36")
    print(res_1.statistic)
    print(res_1.pvalue)
    print(f"From underlying truth: {statistic_mean_diff(data_03, data_69)}")
    rng = np.random.default_rng(1)
    res_2 = permutation_test((data_03,
                              data_69),
                             statistic_mean_diff,
                             n_resamples=10000,
                             vectorized=True,
                             alternative='less', random_state=rng)
    print("03 vs 69")
    print(res_2.statistic)
    print(res_2.pvalue)
    print(f"From underlying truth: {statistic_mean_diff(data_36, data_69)}")
    rng = np.random.default_rng(2)
    res_3 = permutation_test((data_36,
                              data_69),
                             statistic_mean_diff,
                             n_resamples=10000,
                             vectorized=True,
                             alternative='two-sided', random_state=rng)
    print("36 vs 69")
    print(res_3.statistic)
    print(res_3.pvalue)


if __name__ == "__main__":
    unconstrained = False
    run_permutation_test_water_columns(unconstrained)  # stat 1
