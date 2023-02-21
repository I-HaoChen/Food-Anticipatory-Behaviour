import datetime

from pandas import DataFrame, Timestamp

from src.fish_telemetry_faa.utils.transmitter_datasheets import TransmitterDataSheet


def filter_by_hdop(df: DataFrame, lower_bound_inclusive=1, upper_bound_exclusive=3):
    filtered_df = df[(df['HDOP'] >= lower_bound_inclusive) & (df['HDOP'] < upper_bound_exclusive)]
    print(
        f"Length of input df: {len(df)}\nAfter filtering by HDOP ({lower_bound_inclusive}, {upper_bound_exclusive}): {len(filtered_df)}")
    return filtered_df


def filter_by_snr(df: DataFrame, lower_bound_inclusive=25, upper_bound_exclusive=35):
    filtered_df = df[(df['SNR [dB]'] >= lower_bound_inclusive) & (df['SNR [dB]'] < upper_bound_exclusive)]
    print(
        f"Length of input df: {len(df)}\nAfter filtering by SNR [dB] ({lower_bound_inclusive}, {upper_bound_exclusive}): {len(filtered_df)}")
    return filtered_df


def cut_by_start_date(df: DataFrame, start_date: str, add_days=0):
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    if add_days > 0:
        start_date = start_date - datetime.timedelta(days=add_days)
    filtered_df = df[df["datum"] > Timestamp(start_date)]
    return filtered_df


def cut_by_end_date(df: DataFrame, end_date: str, include_end=True, add_days=0):
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    if include_end:
        end_date = end_date + datetime.timedelta(days=1)
    if add_days:
        end_date = end_date + datetime.timedelta(days=add_days)
    filtered_df = df[df["datum"] < Timestamp(end_date)]
    return filtered_df


def get_data_between_hour_times(df: DataFrame, time_first: float, time_last: float) -> DataFrame:
    if df.index.nlevels == 2:
        df['hour'] = df["datum"].dt.hour
        df['minute'] = df["datum"].dt.minute
        df['second'] = df["datum"].dt.second
    else:  # 3
        df['hour'] = df["Time (corrected)"].dt.hour
        df['minute'] = df["Time (corrected)"].dt.minute
        df['second'] = df["Time (corrected)"].dt.second
    df['time'] = df['hour'] + df['minute'] / 60 + df['second'] / 3600
    df = df.drop(columns=["hour", "minute", "second"])
    df = df[df["time"] <= time_last]
    df = df[df["time"] > time_first]
    return df


if __name__ == "__main__":
    data_sheet = TransmitterDataSheet(empty=False)
    data_frame = data_sheet.get_all_current_csv_files_as_one_df()
    data_frame = cut_by_start_date(data_frame, str(datetime.date(2021, 5, 26)))
    data_frame = cut_by_end_date(data_frame, str(datetime.date(2021, 6, 3)))
    data_frame = get_data_between_hour_times(data_frame, time_first=8.5,
                                             time_last=10)
    print(data_frame)
