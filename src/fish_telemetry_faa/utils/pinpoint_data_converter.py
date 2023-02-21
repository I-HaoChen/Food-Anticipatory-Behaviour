import numpy as np
import pandas

from src.fish_telemetry_faa.utils.filter_util import filter_by_snr
from src.fish_telemetry_faa.utils.transmitter_datasheets import TransmitterDataSheet
from src.fish_telemetry_faa.utils.transmitter_datasheets import UnconstrainedTransmitterDataSheet
from src.fish_telemetry_faa.utils.sun_times import correlate_sun_timer_with_fish_positions


# For each tag you have "ID" and "ID+1". The first one, "ID", is depth+temperature, and the 2nd ID, "ID+1", is
# depth+activity. For example, if you have a tag with ID 1001, ID 1001 would be depth+temperature,
# and ID 1002 would be depth+activity.

def convert_data2(df: pandas.DataFrame, unconstrained: bool = False) -> pandas.DataFrame:
    df = append_data2_is_activity_as_column(df, unconstrained=unconstrained)
    df = append_data2_is_temperature_as_column(df, unconstrained=unconstrained)
    df = calculate_activity_from_data2(df)
    df = calculate_temperature_from_data2(df)
    return df


def append_data2_is_activity_as_column(df: pandas.DataFrame, unconstrained=False) -> pandas.DataFrame:
    """For all even number IDs, the second part of data is carrying acceleration data"""
    if unconstrained:
        df["is_activity"] = df["ID"] % 2 == 0
    else:
        df["is_activity"] = df["Name"].str[-1:].astype(int) % 2 == 0
    return df


def append_data2_is_temperature_as_column(df: pandas.DataFrame, unconstrained=False) -> pandas.DataFrame:
    """For all odd number IDs, the second part of data is carrying temperature data"""
    if unconstrained:
        df["is_temperature"] = df["ID"] % 2 == 1
    else:
        df["is_temperature"] = df["Name"].str[-1:].astype(int) % 2 == 1
    return df


def calculate_activity_from_data2(df: pandas.DataFrame) -> pandas.DataFrame:
    df["activity"] = -1
    df.loc[df["is_activity"], "activity"] = 0.013588 * df.loc[df["is_activity"], "Data2 (DS256 only)"]
    return df


def calculate_temperature_from_data2(df: pandas.DataFrame) -> pandas.DataFrame:
    df["temperature"] = -1
    # t_min = 10, t_max = 35.5
    df.loc[df["is_temperature"], "temperature"] = 0.1 * df.loc[df["is_temperature"], "Data2 (DS256 only)"] + 10
    return df


def exclude_all_outliers(df: pandas.DataFrame, unconstrained: bool = False) -> pandas.DataFrame:
    for name in ["temperature"]:
        # Should exclude eleven points for temperature
        df = exclude_data2_or_depth_outliers(df, name, unconstrained=unconstrained)

    df = df.loc[df["Depth [m] (est. or from tag)"] <= 9]
    df = df.loc[0 <= df["Depth [m] (est. or from tag)"]]
    print(f"After final exclusion: {len(df)}")
    return df


def exclude_data2_or_depth_outliers(df: pandas.DataFrame, column_name: str, unconstrained=False) -> pandas.DataFrame:
    df["z_score_temp"] = 0
    if column_name == "temperature":
        df_small = df.loc[df["is_temperature"]]
    elif column_name == "activity":
        df_small = df.loc[df["is_activity"]]
    elif column_name == "Depth [m] (est. or from tag)":
        df_small = df
    else:
        raise AttributeError("No boolean given!")
    if unconstrained:
        for name, group in df_small.groupby(df_small.index.get_level_values(1)):
            df.loc[group.index, "z_score_temp"] = np.divide(group[column_name] - group[column_name].mean(),
                                                            group[column_name].std(ddof=0))
        df_lefties = df.loc[df["z_score_temp"] < 3]
        df_lefties = df_lefties.loc[-3 < df_lefties["z_score_temp"]]
        print(f"{len(df) - len(df_lefties)} outliers with (z_score > 3) excluded for column {column_name}")
        df_lefties = df_lefties.drop(columns=["z_score_temp"])
    else:
        for name, group in df_small.groupby("Name"):
            df.loc[group.index, "z_score_temp"] = np.divide(group[column_name] - group[column_name].mean(),
                                                            group[column_name].std(ddof=0))
        df_lefties = df.loc[df["z_score_temp"] < 3]
        df_lefties = df_lefties.loc[-3 < df_lefties["z_score_temp"]]
        print(f"{len(df) - len(df_lefties)} outliers with (z_score > 3) excluded for column {column_name}")
        df_lefties = df_lefties.drop(columns=["z_score_temp"])
    return df_lefties


if __name__ == "__main__":
    data_sheet = TransmitterDataSheet(empty=False)
    data_frame = data_sheet.get_all_current_csv_files_as_one_df()
    data_frame = convert_data2(data_frame)
    data_frame = exclude_all_outliers(data_frame)
    print(data_frame[["activity", "temperature"]])

    data_sheet = UnconstrainedTransmitterDataSheet()
    df = data_sheet.get_unconstrained_transmitter_data()
    df = filter_by_snr(df, 20, 50)
    df = correlate_sun_timer_with_fish_positions(df)
    df = convert_data2(df, unconstrained=True)
    df = exclude_all_outliers(df, unconstrained=True)
    print(data_frame[["activity", "temperature"]])
