import pandas
from scipy.stats import ks_2samp

from src.fish_telemetry_faa.utils.data_loader import init_standard_data, init_unconstrained_tag_data, \
    init_receiver_sensor_data


def general_ks_test_temperature(df_1: pandas.DataFrame, df_2: pandas.DataFrame):
    df_1 = df_1.resample(f'{minutes}min', label='left', closed='left',
                         offset=f"{0}min",
                         on="Time (corrected)").mean()
    df_2 = df_2.resample(f'{minutes}min', label='left', closed='left',
                         offset=f"{0}min",
                         on="Time (corrected)").mean()
    df_1["time_resampled"] = df_1.index
    df_2["time_resampled"] = df_2.index
    ks_result = ks_2samp(df_1["temperature"], df_2["temperature"])
    print(ks_result)


def ks_test_temp_with_unconstrained_temp():
    df = init_standard_data()
    df_2 = init_unconstrained_tag_data()
    df = df.loc[df["is_temperature"]]
    df_2 = df_2.loc[df_2["is_temperature"]]
    general_ks_test_temperature(df_1=df, df_2=df_2)


def ks_test_temp_with_receiver():
    df = init_standard_data()
    df_2 = init_receiver_sensor_data()
    df = df.loc[df["is_temperature"]]
    general_ks_test_temperature(df_1=df, df_2=df_2)


def ks_test_unconstrained_temp_with_receiver():
    df = init_unconstrained_tag_data()
    df_2 = init_receiver_sensor_data()
    df = df.loc[df["is_temperature"]]
    general_ks_test_temperature(df_1=df, df_2=df_2)


if __name__ == "__main__":
    minutes = 20
    ks_test_temp_with_unconstrained_temp()  # stat 2, same distribution
    ks_test_temp_with_receiver()  # stat 2, different distribution
    ks_test_unconstrained_temp_with_receiver()  # stat 2, different distribution
