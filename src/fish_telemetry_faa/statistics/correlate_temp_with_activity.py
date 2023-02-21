import pandas
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import pearsonr

from src.fish_telemetry_faa.utils.data_loader import init_unconstrained_tag_data, init_standard_data, \
    init_receiver_sensor_data


def correlate_temperature_with_activity_generic(df_act: pandas.DataFrame, df_temp: pandas.DataFrame):
    df_act_resampled = df_act.resample(f'{minutes}min', label='left', closed='left',
                                       offset=f"{0}min",
                                       on="Time (corrected)").mean()
    df_act_resampled["time_resampled"] = df_act_resampled.index
    df_temp_resampled = df_temp.resample(f'{minutes}min', label='left', closed='left',
                                         offset=f"{0}min",
                                         on="Time (corrected)").mean()
    df_temp_resampled["time_resampled"] = df_temp_resampled.index
    # Testing for positive or negative correlation
    res = pearsonr(df_act_resampled["activity"], df_temp_resampled["temperature"],
                   alternative="two-sided")
    print(res)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Line(x=df_act_resampled["time_resampled"], y=df_act_resampled["activity"], name="Activity"),
        secondary_y=False)
    fig.add_trace(
        go.Line(x=df_temp_resampled["time_resampled"], y=df_temp_resampled["temperature"],
                name="Temperature"),
        secondary_y=True)
    fig.update_layout(
        title="2D histogram of positional data: Depth against Daytime",
        xaxis_title="date and time")
    fig.update_yaxes(title_text="<b>Activity</b> in m/s²", secondary_y=False)
    fig.update_yaxes(title_text="<b>Temperature</b> in degC", secondary_y=True)
    fig.show()


def correlate_temp_with_activity():
    df = init_standard_data()
    df_act = df.loc[df["is_activity"]]
    df_temp = df.loc[df["is_temperature"]]
    correlate_temperature_with_activity_generic(df_act=df_act, df_temp=df_temp)


def correlate_temp_with_activity_both_unconstrained():
    df = init_unconstrained_tag_data()
    df_act = df.loc[df["is_activity"]]
    df_temp = df.loc[df["is_temperature"]]
    correlate_temperature_with_activity_generic(df_act=df_act, df_temp=df_temp)


def correlate_receiver_temp_with_activity():
    df = init_standard_data()
    df_temp_rec = init_receiver_sensor_data()
    df_act = df.loc[df["is_activity"]]
    correlate_temperature_with_activity_generic(df_act=df_act, df_temp=df_temp_rec)


def correlate_receiver_temp_with_activity_unconstrained():
    df = init_unconstrained_tag_data()
    df_temp_rec = init_receiver_sensor_data()
    df_act = df.loc[df["is_activity"]]
    correlate_temperature_with_activity_generic(df_act=df_act, df_temp=df_temp_rec)


if __name__ == "__main__":
    minutes = 20
    correlate_temp_with_activity()  # stat 6, no correlation
    correlate_temp_with_activity_both_unconstrained()  # stat 6, no correlation
    correlate_receiver_temp_with_activity()  # stat 6, no correlation
    correlate_receiver_temp_with_activity_unconstrained()  # stat 6, no correlation
