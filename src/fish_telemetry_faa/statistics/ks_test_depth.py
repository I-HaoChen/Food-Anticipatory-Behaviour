from scipy.stats import ks_2samp

from src.fish_telemetry_faa.utils.data_loader import init_standard_data, init_unconstrained_tag_data


def ks_test_depth_with_unconstrained_depth(minutes=20):
    df = init_standard_data()
    df_2 = init_unconstrained_tag_data()
    df = df.resample(f'{minutes}min', label='left', closed='left',
                     offset=f"{0}min",
                     on="Time (corrected)").mean()
    df_2 = df_2.resample(f'{minutes}min', label='left', closed='left',
                         offset=f"{0}min",
                         on="Time (corrected)").mean()
    df["time_resampled"] = df.index
    df_2["time_resampled"] = df_2.index
    ks_result = ks_2samp(df["Depth [m] (est. or from tag)"], df_2["Depth [m] (est. or from tag)"])
    print(ks_result)


if __name__ == "__main__":
    minutes = 20
    ks_test_depth_with_unconstrained_depth(minutes)  # stat 5, different distribution
