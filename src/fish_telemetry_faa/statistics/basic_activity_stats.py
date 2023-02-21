import itertools

import pandas as pd

from src.fish_telemetry_faa.utils.data_loader import init_standard_data, init_unconstrained_tag_data
from src.fish_telemetry_faa.utils.project_constants import ProjectConstants


def print_basic_activity_stats(unconstrained: bool = False):
    if unconstrained:
        df = init_unconstrained_tag_data()
    else:
        df = init_standard_data()
    mean_val = df.loc[df["is_activity"], "activity"].mean()
    std_val = df.loc[df["is_activity"], "activity"].std()
    print(f"Mean of activity (dataset): {mean_val}+/- {std_val}")
    max_value = df.loc[df["is_activity"], "activity"].max()
    min_value = df.loc[df["is_activity"], "activity"].min()
    print(f"Range from {min_value} to {max_value}")
    quantiles = [df.loc[df["is_activity"], "activity"].quantile(0.25),
                 df.loc[df["is_activity"], "activity"].quantile(0.75)]
    print(f"Quantile: {quantiles}")


def identify_lasting_peaks(unconstrained: bool = False, minutes=20):
    if unconstrained:
        df = init_unconstrained_tag_data()
    else:
        df = init_standard_data()
    df = df.loc[df["is_activity"]]
    df = df.resample(f'{minutes}min', label='left', closed='left',
                     offset=f"{0}min",
                     on="Time (corrected)").mean()
    df["time"] = df.index
    # choosing the quantile as threshold for FAA
    quantile = 0.5
    faa_duration = 6
    list_of_faa_df_lists = []
    list_of_faa_df_lists_start_time = []
    for datum, mini_df in df.groupby(df["time"].dt.date):
        faa_threshold = mini_df["activity"].quantile(quantile)
        # resample the data, since we only interested in the group behaviour
        # setting faa duration to 6 which equals 20 minutes * 6 = 120 minutes
        # This is how long a peak must persist to be considered true FAA (since 120 minutes is the feeding window)
        print(f"{faa_threshold=} and {faa_duration* minutes=}")

        # Number each value from the beginning starting with 1, but keep the number if over threshold
        grouper = mini_df.groupby(mini_df["activity"].ge(faa_threshold).diff().ne(0).cumsum())

        # The smallest in the group MUST be higher than the threshold
        # The diff between the first and last element in the group must exceed the set faa_duration
        # And the timespan starts before 8 for daily FAA (no food -> nothing interesting on the daily scale)
        condition = lambda group: (group["activity"].min() >= faa_threshold and
                                   len(group) >= faa_duration
                                   and group.iloc[0]["time"].hour < 8)

        # filter the grouper
        result = [g for _, g in grouper if condition(g)]
        print(f"Number of FAA windows detected for the f{datum}: {len(result)}")
        list_of_faa_df_lists.append(result)
        list_of_faa_df_lists_start_time.append([el.head(1) for el in result])
    faa_df = pd.concat(list(itertools.chain(*list_of_faa_df_lists_start_time)))
    print(f"{faa_df}")
    faa_df["faa_start"] = pd.to_datetime(faa_df.index)
    output_path = ProjectConstants.ROOT.joinpath("output")
    output_path.mkdir(parents=True, exist_ok=True)
    faa_df[["faa_start"]].to_csv(output_path.joinpath(f"faa_starting_times_{unconstrained}.csv"))
    faa_df["time_numeric"] = faa_df['faa_start'].dt.hour + faa_df['faa_start'].dt.minute / 60
    faa_mean = faa_df["time_numeric"].mean()
    # convert back to minutes and hours
    faa_mean_minutes = int(faa_mean % 1 * 60)
    faa_mean_hour = int(faa_mean)
    faa_std = faa_df["time_numeric"].std()
    faa_std_minutes = int(faa_std % 1 * 60)
    faa_std_hours = int(faa_std)
    print(
        f"Mean time for FAA to start: {faa_mean_hour:02}:{faa_mean_minutes:02} +/- {faa_std_hours:02}:{faa_std_minutes:02}")
    return list_of_faa_df_lists


def identify_lasting_peaks_all_dates(unconstrained: bool = False, minutes=5):
    if unconstrained:
        df = init_unconstrained_tag_data()
    else:
        df = init_standard_data()
    df = df.loc[df["is_activity"]]
    # Random Day chosen (not relevant)
    df["Time (corrected)"] = pd.to_datetime("2020-01-01" + " " + df["time"].astype(str))
    df = df.resample(f'{minutes}min', label='left', closed='left',
                     offset=f"{0}min",
                     on="Time (corrected)").mean()
    df["time"] = df.index
    # choosing the quantile as threshold for FAA
    quantile = 0.5
    faa_duration = 24
    list_of_faa_df_lists = []
    list_of_faa_df_lists_start_time = []
    for _, mini_df in df.groupby(df["time"].dt.date):
        faa_threshold = mini_df["activity"].quantile(quantile)
        # resample the data, since we only interested in the group behaviour
        # setting faa duration to 24 which equals 5 minutes = 120 minutes
        # This is how long a peak must persist to be considered true FAA
        print(f"{faa_threshold=} and {faa_duration* minutes=}")

        # Number each value from the beginning starting with 1, but keep the number if over threshold
        grouper = mini_df.groupby(mini_df["activity"].ge(faa_threshold).diff().ne(0).cumsum())

        # The smallest in the group MUST be higher than the threshold
        # The diff between the first and last element in the group must exceed the set faa_duration
        condition = lambda group: (group["activity"].min() >= faa_threshold and
                                   len(group) >= faa_duration)

        # filter the grouper
        result = [g for _, g in grouper if condition(g)]
        print(f"Number of FAA windows detected: {len(result)}")
        list_of_faa_df_lists.append(result)
        list_of_faa_df_lists_start_time.append([el.head(1) for el in result])
    faa_df = pd.concat(list(itertools.chain(*list_of_faa_df_lists_start_time)))
    print(f"{faa_df}")
    faa_df["faa_start"] = pd.to_datetime(faa_df.index)
    output_path = ProjectConstants.ROOT.joinpath("output")
    output_path.mkdir(parents=True, exist_ok=True)
    faa_df[["faa_start"]].to_csv(output_path.joinpath(f"faa_starting_times_all_dates_{unconstrained}.csv"))
    faa_df["time_numeric"] = faa_df['faa_start'].dt.hour + faa_df['faa_start'].dt.minute / 60
    faa_mean = faa_df["time_numeric"].mean()
    # convert back to minutes and hours
    faa_mean_minutes = int(faa_mean % 1 * 60)
    faa_mean_hour = int(faa_mean)
    print(
        f"Mean time for FAA to start: {faa_mean_hour:02}:{faa_mean_minutes:02}")
    return list_of_faa_df_lists


if __name__ == "__main__":
    print_basic_activity_stats(unconstrained=False)
    print_basic_activity_stats(unconstrained=True)
    identify_lasting_peaks(unconstrained=False, minutes=20)
    identify_lasting_peaks_all_dates(unconstrained=False, minutes=5)
