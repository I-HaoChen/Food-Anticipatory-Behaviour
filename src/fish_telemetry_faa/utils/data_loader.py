import pandas
import pandas as pd

from src.fish_telemetry_faa.utils.filter_util import cut_by_start_date, filter_by_snr, cut_by_end_date, filter_by_hdop
from src.fish_telemetry_faa.utils.pinpoint_data_converter import convert_data2, exclude_all_outliers
from src.fish_telemetry_faa.utils.transmitter_datasheets import TransmitterDataSheet, \
    UnconstrainedTransmitterDataSheet
from src.fish_telemetry_faa.utils.project_constants import ProjectConstants
from src.fish_telemetry_faa.utils.sun_times import correlate_sun_timer_with_fish_positions, add_time_of_day_intervals


def add_water_columns(df):
    df["water_column"] = "ERROR"
    df.loc[df["Depth [m] (est. or from tag)"] < 3, "water_column"] = "0-3m"
    df.loc[(3 <= df["Depth [m] (est. or from tag)"]) & (
            df["Depth [m] (est. or from tag)"] < 6), "water_column"] = "3-6m"
    df.loc[6 <= df["Depth [m] (est. or from tag)"], "water_column"] = "6-9m"
    return df


def init_data(files, all_fish, start_date, end_date, hdop_slider_values, snr_slider_values,
              with_dates=True, short_nights=True) -> pandas.DataFrame:
    if all_fish:
        data_sheet = TransmitterDataSheet(empty=False)
    else:
        data_sheet = TransmitterDataSheet(empty=True)
        try:
            print(len(files))
            print(files)
            print(type(files))
            if len(files) == 1:
                # One file
                for file in ProjectConstants.CONSTRAINED_TRANSMITTER_DATA.glob(files[0] + "*.csv"):
                    print(file)
                    data_sheet.add_one_csv_file(
                        ProjectConstants.CONSTRAINED_TRANSMITTER_DATA.joinpath(file).with_suffix(".csv"))
            else:
                for file in files:
                    print(f"Loading {file}")
                    for real_file in ProjectConstants.CONSTRAINED_TRANSMITTER_DATA.glob(file + "*.csv"):
                        print(real_file)
                        data_sheet.add_one_csv_file(
                            ProjectConstants.CONSTRAINED_TRANSMITTER_DATA.joinpath(real_file).with_suffix(".csv"))
        except (FileNotFoundError, TypeError):
            return pd.DataFrame()
    df = data_sheet.get_all_current_csv_files_as_one_df()
    if with_dates:
        df = cut_by_start_date(df, start_date)
        df = cut_by_end_date(df, end_date)
        print(f"Number of signals in the experiment window: {len(df)}")
    df = filter_by_snr(df, snr_slider_values[0], snr_slider_values[1])
    df = filter_by_hdop(df, hdop_slider_values[0], hdop_slider_values[1])
    df = correlate_sun_timer_with_fish_positions(df)
    df = convert_data2(df)
    df = exclude_all_outliers(df)
    df = add_time_of_day_intervals(df, short_nights=short_nights)
    df = add_water_columns(df)
    return df


def init_standard_data(short_nights=True, with_dates=True):
    df = init_data([], all_fish=True, start_date="2021-05-26", end_date="2021-06-06", hdop_slider_values=[0, 1.2],
                   snr_slider_values=[20, 50], with_dates=with_dates, short_nights=short_nights)
    df['hour'] = df.index.get_level_values(1).hour
    df['minute'] = df.index.get_level_values(1).minute
    df['second'] = df.index.get_level_values(1).second
    df['time_numeric'] = df['hour'] + df['minute'] / 60 + df['second'] / 3600
    return df


def init_unconstrained_data(snr_slider_values, short_nights=True) -> pandas.DataFrame:
    data_sheet = UnconstrainedTransmitterDataSheet()
    df = data_sheet.get_unconstrained_transmitter_data()
    df = filter_by_snr(df, snr_slider_values[0], snr_slider_values[1])
    # No HDOP filter because no positioning
    df = correlate_sun_timer_with_fish_positions(df)
    df = convert_data2(df, unconstrained=True)
    df = exclude_all_outliers(df, unconstrained=True)
    df = add_time_of_day_intervals(df, drop_sun_times=True, short_nights=short_nights)
    df = add_water_columns(df)
    return df


def init_unconstrained_tag_data(short_nights=True):
    df = init_unconstrained_data(snr_slider_values=[20, 50], short_nights=short_nights)
    df['hour'] = df.index.get_level_values(2).hour
    df['minute'] = df.index.get_level_values(2).minute
    df['second'] = df.index.get_level_values(2).second
    df['time_numeric'] = df['hour'] + df['minute'] / 60 + df['second'] / 3600
    return df


def init_receiver_sensor_data():
    df = pd.read_csv(ProjectConstants.RECEIVERS_SENSOR_DATA, header=0, encoding="utf-8",
                     skipinitialspace=True, delimiter=";")
    df["Time (corrected)"] = pd.to_datetime(df["Date and Time (UTC)"]) + pd.DateOffset(hours=3)
    df = df.drop(columns="Date and Time (UTC)")
    df = df.set_index(["Time (corrected)", "Receiver"], drop=False)
    df["temperature"] = df["Temperature [degC]"].str.replace(",", ".").astype(float)
    return df


if __name__ == "__main__":
    df = init_standard_data()
    print(f"Standard data ({len(df)}) loaded")
    df_unconstrained = init_unconstrained_tag_data()
    print(f"unconstrained transmitter data ({len(df_unconstrained)}) loaded")
    df_receiver_unconstrained = init_receiver_sensor_data()
    print(f"Receiver data ({len(df_receiver_unconstrained)}) loaded")
