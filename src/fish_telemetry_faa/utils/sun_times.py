from pathlib import Path

import pandas
import pandas as pd
import plotly.graph_objects as go
from pandas import DataFrame

from src.fish_telemetry_faa.utils.filter_util import get_data_between_hour_times
from src.fish_telemetry_faa.utils.project_constants import ProjectConstants
from src.fish_telemetry_faa.utils.transmitter_datasheets import TransmitterDataSheet


class SunTimer(object):

    def __init__(self):
        self._official = self.parse_and_read(ProjectConstants.SUN_TIMES_OFFICIAL)
        self._civil = self.parse_and_read(ProjectConstants.SUN_TIMES_CIVIL)
        self._nautical = self.parse_and_read(ProjectConstants.SUN_TIMES_NAUTICAL)
        self._astronomic = self.parse_and_read(ProjectConstants.SUN_TIMES_ASTRONOMICAL)
        self._csv_files = {}
        self._add_all_scientific_csv_files()
        self._all_sun_times = pd.concat(self._csv_files.values(), keys=self._csv_files.keys(), names=["type", "dates"])
        self._all_sun_times_unified = {}

    def _add_all_scientific_csv_files(self):
        for file in ProjectConstants.SUN_TIMES.glob('*.csv'):
            df_indexed_datetime = self.parse_and_read(file)
            self._csv_files[file.stem] = df_indexed_datetime

    def get_all_sun_times_variations(self):
        return self._all_sun_times

    def parse_and_read(self, file: Path):
        df = pd.read_csv(file, header=0, skipinitialspace=True)
        # create date
        df.loc[:, "type"] = file.stem.rstrip("sun_times_2021")
        df.loc[:, "year"] = 2021
        df.loc[:, "Datum"] = pd.DatetimeIndex(
            pd.to_datetime(df[['year', 'month', 'day']], format='%d.%m.%Y'))
        df = df.set_index(df["Datum"])

        # Getting sunrise and sunset
        df["sunrise"] = df["rise"].map('{:0>4}'.format)
        df["sunrise"] = [f"{x[:2]}:{x[-2:]}:00" for x in df["sunrise"]]
        df["sunset"] = df["set"].map('{:0>4}'.format)
        df["sunset"] = [f"{x[:2]}:{x[-2:]}:00" for x in df["sunset"]]
        dawn_time = pd.DatetimeIndex(pd.to_datetime(df["sunrise"]))
        df.loc[df.index, "dawn"] = dawn_time.hour + dawn_time.minute / 60 + dawn_time.second / 3600
        dusk_time = pd.DatetimeIndex(pd.to_datetime(df["sunset"]))
        df.loc[df.index, "dusk"] = dusk_time.hour + dusk_time.minute / 60 + dusk_time.second / 3600
        df = df.drop(columns=["month", "day", "year", "rise", "set"])
        df_indexed_datetime = df[
                              ProjectConstants.START_OF_EXPERIMENT:ProjectConstants.END_OF_EXPERIMENT_INCLUSIVE]
        return df_indexed_datetime

    def load_unified_sun_time_sheet_with_id(self):
        for file in ProjectConstants.SUN_TIMES.glob('*.csv'):
            df = pd.read_csv(file, header=0, skipinitialspace=True)
            file_stem = file.stem.rstrip("sun_times_2021")
            df.loc[:, "type"] = file_stem
            df.loc[:, "year"] = 2021
            df.loc[:, "Datum"] = pd.DatetimeIndex(
                pd.to_datetime(df[['year', 'month', 'day']], format='%d.%m.%Y'))
            df = df.set_index(df["Datum"])

            # Getting sunrise and sunset
            df[f"sunrise_{file_stem}"] = df["rise"].map('{:0>4}'.format)
            df[f"sunrise_{file_stem}"] = [f"{x[:2]}:{x[-2:]}:00" for x in df[f"sunrise_{file_stem}"]]
            df[f"sunrise_{file_stem}"] = pd.to_datetime(df.loc[:, f"sunrise_{file_stem}"]).dt.time
            df[f"sunset_{file_stem}"] = df["set"].map('{:0>4}'.format)
            df[f"sunset_{file_stem}"] = [f"{x[:2]}:{x[-2:]}:00" for x in df[f"sunset_{file_stem}"]]
            df[f"sunset_{file_stem}"] = pd.to_datetime(df.loc[:, f"sunset_{file_stem}"]).dt.time

            df = df.drop(columns=["month", "day", "year", "rise", "set"])
            df = df[ProjectConstants.START_OF_EXPERIMENT:ProjectConstants.END_OF_EXPERIMENT_INCLUSIVE]
            df = df.drop(columns=["type", "Datum"])
            self._all_sun_times_unified[file_stem] = df

        all_df = pd.concat(self._all_sun_times_unified.values(), axis=1)
        all_df["temp_id"] = all_df.index.date
        return all_df


def set_correct_time_of_day(df: DataFrame, lower_col_bound: str, upper_col_bound: str, value_for_column) -> DataFrame:
    stuff = df.query(f"{lower_col_bound} <= time < {upper_col_bound}")
    df.loc[stuff.index, "time_of_day"] = value_for_column
    return df


def set_correct_night(df: DataFrame, lower_col_bound: str, upper_col_bound: str, value_for_column) -> DataFrame:
    stuff = df.query(f"{lower_col_bound} <= time | time < {upper_col_bound}")
    df.loc[stuff.index, "time_of_day"] = value_for_column
    return df


def correlate_sun_timer_with_fish_positions(df: DataFrame):
    sun_times = SunTimer()
    st_df = sun_times.load_unified_sun_time_sheet_with_id()
    if df.index.nlevels == 2:
        df['temp_id'] = df.index.get_level_values(1).date
        df = df.merge(st_df, how="left", on='temp_id').set_axis(df.index)
        df["time"] = df.index.get_level_values(1).time
    elif df.index.nlevels == 3:
        df['temp_id'] = df.index.get_level_values(2).date
        df = df.merge(st_df, how="left", on='temp_id').set_axis(df.index)
        df["time"] = df.index.get_level_values(2).time
    else:
        df['temp_id'] = df.index.date
        df = df.merge(st_df, how="left", on='temp_id').set_axis(df.index)
        df["time"] = df.index.time
    df["time_of_day"] = "INVALID"
    # Change all the names

    df_temp = df[[
        "time", "time_of_day", ProjectConstants.SUNRISE_OFFICIAL, ProjectConstants.SUNRISE_CIVIL,
        ProjectConstants.SUNRISE_NAUTICAL, ProjectConstants.SUNRISE_ASTRONOMICAL,
        ProjectConstants.SUNSET_ASTRONOMICAL, ProjectConstants.SUNSET_NAUTICAL,
        ProjectConstants.SUNSET_CIVIL, ProjectConstants.SUNSET_OFFICIAL]].copy()

    df_temp = set_correct_time_of_day(df_temp, ProjectConstants.SUNRISE_OFFICIAL,
                                      ProjectConstants.SUNSET_OFFICIAL,
                                      value_for_column="Day")
    df_temp = set_correct_time_of_day(df_temp, ProjectConstants.SUNSET_OFFICIAL, ProjectConstants.SUNSET_CIVIL,
                                      value_for_column="Civil Twilight")
    df_temp = set_correct_time_of_day(df_temp, ProjectConstants.SUNSET_CIVIL, ProjectConstants.SUNSET_NAUTICAL,
                                      value_for_column="Nautical Twilight")
    df_temp = set_correct_time_of_day(df_temp, ProjectConstants.SUNSET_NAUTICAL,
                                      ProjectConstants.SUNSET_ASTRONOMICAL,
                                      value_for_column="Astronomical Twilight")
    df_temp = set_correct_night(df_temp, ProjectConstants.SUNSET_ASTRONOMICAL,
                                ProjectConstants.SUNRISE_ASTRONOMICAL,
                                value_for_column="Night")
    df_temp = set_correct_time_of_day(df_temp, ProjectConstants.SUNRISE_ASTRONOMICAL,
                                      ProjectConstants.SUNRISE_NAUTICAL,
                                      value_for_column="Astronomical Twilight")
    df_temp = set_correct_time_of_day(df_temp, ProjectConstants.SUNRISE_NAUTICAL, ProjectConstants.SUNRISE_CIVIL,
                                      value_for_column="Nautical Twilight")
    df_temp = set_correct_time_of_day(df_temp, ProjectConstants.SUNRISE_CIVIL, ProjectConstants.SUNRISE_OFFICIAL,
                                      value_for_column="Civil Twilight")
    df["time_of_day"] = df_temp["time_of_day"]
    assert df.equals(df.mask(df_temp["time_of_day"] == "INVALID", "FAIL"))
    return df


def add_time_of_day_intervals(df: pandas.DataFrame, drop_sun_times=False, short_nights=True) -> pandas.DataFrame:
    list_of_small_dfs = []
    df["time_of_day_interval"] = "Official Night Time"
    for date in sorted(set(df["temp_id"])):
        df_small_date = df.loc[df["temp_id"] == date]
        # The data already has the different sunrise/sunsets, "ID" == "date"
        if short_nights:
            sun_rise = df_small_date["sunrise_astronomical"].values[0]
            sun_rise_float = sun_rise.hour + (sun_rise.minute / 60) + (sun_rise.second / 3600)
            sun_set = df_small_date["sunset_astronomical"].values[0]
            sun_set_float = sun_set.hour + (sun_set.minute / 60) + (sun_set.second / 3600)
            df_start_8 = get_data_between_hour_times(df_small_date.copy(), time_first=sun_rise_float, time_last=8)
            df_start_8.loc[df_small_date["time_of_day"] != "Night", ["time_of_day_interval"]] = "Sunrise to 8:00"
            df_810 = get_data_between_hour_times(df_small_date.copy(), time_first=8, time_last=10)
            df_810.loc[df_small_date["time_of_day"] != "Night", ["time_of_day_interval"]] = "8:00 to 10:00"
            df_1012 = get_data_between_hour_times(df_small_date.copy(), time_first=10, time_last=12)
            df_1012.loc[df_small_date["time_of_day"] != "Night", ["time_of_day_interval"]] = "10:00 to 12:00"
            df_1214 = get_data_between_hour_times(df_small_date.copy(), time_first=12, time_last=14)
            df_1214.loc[df_small_date["time_of_day"] != "Night", ["time_of_day_interval"]] = "12:00 to 14:00"
            df_1416 = get_data_between_hour_times(df_small_date.copy(), time_first=14, time_last=16)
            df_1416.loc[df_small_date["time_of_day"] != "Night", ["time_of_day_interval"]] = "14:00 to 16:00"
            df_16_end = get_data_between_hour_times(df_small_date.copy(), time_first=16, time_last=sun_set_float)
            df_16_end.loc[df_small_date["time_of_day"] != "Night", ["time_of_day_interval"]] = "16:00 to Sunset"
            df_small_date = pd.concat([df_start_8, df_810, df_1012, df_1214, df_1416, df_16_end])
            list_of_small_dfs.append(df_small_date)
        else:
            sun_rise = df_small_date["sunrise_official"].values[0]
            sun_rise_float = sun_rise.hour + (sun_rise.minute / 60) + (sun_rise.second / 3600)
            sun_set = df_small_date["sunset_official"].values[0]
            sun_set_float = sun_set.hour + (sun_set.minute / 60) + (sun_set.second / 3600)
            df_start_8 = get_data_between_hour_times(df_small_date.copy(), time_first=sun_rise_float, time_last=8)
            df_start_8.loc[df_small_date["time_of_day"] == "Day", ["time_of_day_interval"]] = "Sunrise to 8:00"
            df_810 = get_data_between_hour_times(df_small_date.copy(), time_first=8, time_last=10)
            df_810.loc[df_small_date["time_of_day"] == "Day", ["time_of_day_interval"]] = "8:00 to 10:00"
            df_1012 = get_data_between_hour_times(df_small_date.copy(), time_first=10, time_last=12)
            df_1012.loc[df_small_date["time_of_day"] == "Day", ["time_of_day_interval"]] = "10:00 to 12:00"
            df_1214 = get_data_between_hour_times(df_small_date.copy(), time_first=12, time_last=14)
            df_1214.loc[df_small_date["time_of_day"] == "Day", ["time_of_day_interval"]] = "12:00 to 14:00"
            df_1416 = get_data_between_hour_times(df_small_date.copy(), time_first=14, time_last=16)
            df_1416.loc[df_small_date["time_of_day"] == "Day", ["time_of_day_interval"]] = "14:00 to 16:00"
            df_16_end = get_data_between_hour_times(df_small_date.copy(), time_first=16, time_last=sun_set_float)
            df_16_end.loc[df_small_date["time_of_day"] == "Day", ["time_of_day_interval"]] = "16:00 to Sunset"
            df_small_date = pd.concat([df_start_8, df_810, df_1012, df_1214, df_1416, df_16_end])
            list_of_small_dfs.append(df_small_date)
    df_update = pd.concat(list_of_small_dfs)
    if short_nights:
        df_update = df_update.loc[df_update["time_of_day"] != "Night"]
    else:
        df_update = df_update.loc[df_update["time_of_day"] == "Day"]
    assert len(df_update.loc[df_update[
                                 "time_of_day_interval"] == "Official Night Time"]) == 0, "Error when calculating the time of day intervals!"
    df.update(df_update["time_of_day_interval"])
    if drop_sun_times:
        df = df.drop(
            columns=["sunrise_astronomical", "sunset_astronomical", "sunrise_nautical", "sunset_nautical",
                     "sunrise_civil",
                     "sunset_civil", "sunrise_official", "sunset_official"])
    return df


def plot_all_sun_times():
    df = sun_timer.get_all_sun_times_variations()
    # df.sort_values(by=['Datum'])
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=df.loc[df["type"] == "official"].Datum, y=df.loc[df["type"] == "official"].dawn,
                   mode="lines+markers", showlegend=True, name="dawn", legendgroup="official",
                   legendgrouptitle_text="Official", marker=dict(color="orange")))
    fig.add_trace(
        go.Scatter(x=df.loc[df["type"] == "official"].Datum, y=df.loc[df["type"] == "official"].dusk,
                   mode="lines+markers", showlegend=True, name="dusk", legendgroup="official",
                   marker=dict(color="orange")))
    fig.add_trace(
        go.Scatter(x=df.loc[df["type"] == "civil"].Datum, y=df.loc[df["type"] == "civil"].dawn, mode="lines+markers",
                   showlegend=True, name="dawn", legendgroup="civil", legendgrouptitle_text="Civil",
                   marker=dict(color="lightblue")))
    fig.add_trace(
        go.Scatter(x=df.loc[df["type"] == "civil"].Datum, y=df.loc[df["type"] == "civil"].dusk, mode="lines+markers",
                   showlegend=True, name="dusk", legendgroup="civil", marker=dict(color="lightblue")))
    fig.add_trace(go.Scatter(x=df.loc[df["type"] == "nautical"].Datum, y=df.loc[df["type"] == "nautical"].dawn,
                             mode="lines+markers", showlegend=True, name="dawn", legendgroup="nautical",
                             legendgrouptitle_text="Nautical", marker=dict(color="steelblue")))
    fig.add_trace(go.Scatter(x=df.loc[df["type"] == "nautical"].Datum, y=df.loc[df["type"] == "nautical"].dusk,
                             mode="lines+markers",
                             showlegend=True, name="dusk", legendgroup="nautical", marker=dict(color="steelblue")))
    fig.add_trace(
        go.Scatter(x=df.loc[df["type"] == "astronomical"].Datum, y=df.loc[df["type"] == "astronomical"].dawn,
                   mode="lines+markers", showlegend=True, name="dawn", legendgroup="astronomical",
                   legendgrouptitle_text="Astronomical", marker=dict(color="midnightblue")))
    fig.add_trace(
        go.Scatter(x=df.loc[df["type"] == "astronomical"].Datum, y=df.loc[df["type"] == "astronomical"].dusk,
                   mode="lines+markers", showlegend=True, name="dusk", legendgroup="astronomical",
                   marker=dict(color="midnightblue")))
    fig.update_layout(
        title=f"Different dawn and dusk times for Latitude: {ProjectConstants.RECEIVER_MIDDLE['Latitude']}, "
              f"Longitude: {ProjectConstants.RECEIVER_MIDDLE['Longitude']}")
    fig.update_xaxes(title_text="Dates")
    fig.update_yaxes(title_text='Hour of the day')
    fig.show()
    print(df)


if __name__ == "__main__":
    sun_timer = SunTimer()
    data_sheet = TransmitterDataSheet(empty=False)
    df = data_sheet.get_all_current_csv_files_as_one_df()
    df = correlate_sun_timer_with_fish_positions(df)
    plot_all_sun_times()
