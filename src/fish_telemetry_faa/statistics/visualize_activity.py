import plotly.express as px
import plotly.graph_objects as go
from _plotly_utils.colors import n_colors
from plotly.subplots import make_subplots
import pandas as pd
from src.fish_telemetry_faa.statistics.basic_activity_stats import identify_lasting_peaks
from src.fish_telemetry_faa.utils.data_loader import init_unconstrained_tag_data, init_standard_data
from src.fish_telemetry_faa.utils.sun_times import SunTimer


def viualize_activity():
    df = init_standard_data(with_dates=False)
    df = df.loc[df["is_activity"]]
    fig = px.line(df, x="Time (corrected)", y="activity", color="Name")
    fig.show()


def viualize_binned_activity(minutes):
    df = init_standard_data(with_dates=False)
    df = df.loc[df["is_activity"]]
    df_resampled = df.resample(f'{minutes}min', label='left', closed='left',
                               offset=f"{0}min",
                               on="Time (corrected)").mean()
    df_resampled["time_resampled"] = df_resampled.index
    df_resampled["Fish ID"] = "all fish"
    fig = px.line(df_resampled, x="time_resampled", y="activity", color="Fish ID")
    fig.update_traces(line=dict(width=10))
    # Add the individual binnings in there too
    for name, df_partly in df.groupby("Name"):
        df_partly_resampled = df_partly.resample(f'{minutes}min', label='left', closed='left',
                                                 offset=f"{0}min",
                                                 on="Time (corrected)").mean()
        df_partly_resampled["time_resampled"] = df_partly_resampled.index
        df_partly_resampled = df_partly_resampled.dropna()
        fig.add_trace(go.Line(x=df_partly_resampled["time_resampled"], y=df_partly_resampled["activity"], name=name))
    fig.show()


def visualize_activity_binned_mean_std(minutes, unconstrained=False, with_faa_bars=True, with_day_night_bars=True):
    if unconstrained:
        df = init_unconstrained_tag_data()
    else:
        df = init_standard_data(with_dates=False)
    df_temp = df.loc[df["is_temperature"]]
    df = df.loc[df["is_activity"]]
    df_temp_mean = df_temp.resample(f'{minutes}min', label='left', closed='left',
                                    offset=f"{0}min",
                                    on="Time (corrected)").mean()
    df_temp_mean["time_resampled"] = df_temp_mean.index
    df_resampled_mean = df.resample(f'{minutes}min', label='left', closed='left',
                                    offset=f"{0}min",
                                    on="Time (corrected)").mean()
    std = df.resample(f'{minutes}min', label='left', closed='left',
                      offset=f"{0}min",
                      on="Time (corrected)").std()
    df_resampled_mean["std"] = std["activity"]
    df_resampled_mean["time_resampled"] = df_resampled_mean.index

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(name="Activity", x=df_resampled_mean["time_resampled"], y=df_resampled_mean["activity"],
                             mode="lines", marker=dict(color="blue")), secondary_y=False)

    fig.add_trace(go.Scatter(
        name='Upper Bound',
        x=df_resampled_mean["time_resampled"],
        y=df_resampled_mean["activity"] + df_resampled_mean["std"],
        mode='lines',
        marker=dict(color="#444"),
        line=dict(width=0),
        showlegend=False
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        name='Lower Bound',
        x=df_resampled_mean["time_resampled"],
        y=df_resampled_mean["activity"] - df_resampled_mean["std"],
        marker=dict(color="#444"),
        line=dict(width=0),
        mode='lines',
        fillcolor='rgba(68, 68, 68, 0.3)',
        fill='tonexty',
        showlegend=False
    ), secondary_y=False)
    fig.add_trace(go.Scatter(name="Temperature", x=df_temp_mean["time_resampled"], y=df_temp_mean["temperature"],
                             mode="lines", marker=dict(color="red"), opacity=0.5), secondary_y=True)

    fig.update_layout(
        yaxis_title='Acceleration activity (m/s²)',
        hovermode="x",
        font=dict(
            size=24,
        ),
    )
    fig.update_layout(showlegend=False)
    fig.update_yaxes(title_text="<b>Activity</b> in m/s²", secondary_y=False)
    fig.update_yaxes(title_text="<b>Temperature</b> in degC", secondary_y=True)
    if with_faa_bars:
        faa_list = identify_lasting_peaks(unconstrained=unconstrained, minutes=minutes)
        for dff in faa_list:
            unpacked_df = dff[0]
            # Always cut off at 8:00
            unpacked_df = unpacked_df.loc[(unpacked_df["time"].dt.hour <= 7) | (
                    (unpacked_df["time"].dt.hour <= 8) & (unpacked_df["time"].dt.minute == 0))]
            fig.add_vrect(x0=unpacked_df["time"].dt.strftime('%Y-%m-%d %X')[0],
                          x1=unpacked_df["time"].dt.strftime('%Y-%m-%d %X')[-1],
                          annotation_text="FAA", annotation_position="top left",
                          annotation=dict(font_size=20, font_family="Times New Roman"),
                          fillcolor="darkgreen", opacity=0.75, line_width=0)
    if with_day_night_bars:
        greys_dark = n_colors('rgb(0, 0, 0)', 'rgb(255, 255, 255)',  5, colortype='rgb')
        sun_timer = SunTimer()
        sun_times_df = sun_timer.get_all_sun_times_variations()
        fig.add_shape(type="rect",
                      x0='2021-05-26 00:00:00', y0=-0.1,
                      x1='2021-06-06 23:59:00', y1=0.1,
                      fillcolor=greys_dark[0],
                      line=dict(width=0)
                      )
        for date in sorted(set(df_resampled_mean["time_resampled"].dt.date)):
            for tw_type, colour in zip(["astronomical", "nautical", "civil", "official"],
                                       greys_dark[1:6]):
                correct_twilight = sun_times_df.loc[sun_times_df["Datum"].dt.date == date].loc[
                    sun_times_df["type"] == tw_type]
                sunrise_of_that_day = pd.to_datetime(
                    correct_twilight["Datum"].astype(str) + " " + correct_twilight["sunrise"])
                sunset_of_that_day = pd.to_datetime(
                    correct_twilight["Datum"].astype(str) + " " + correct_twilight["sunset"])
                fig.add_shape(type="rect",
                              x0=sunrise_of_that_day.dt.strftime('%Y-%m-%d %X')[0], y0=-0.1,
                              x1=sunset_of_that_day.dt.strftime('%Y-%m-%d %X')[0], y1=0.1,
                              fillcolor=colour,
                              line=dict(width=0)
                              )
    fig.show()


if __name__ == "__main__":
    minutes_cfg = 20
    viualize_activity()
    viualize_binned_activity(minutes=minutes_cfg)
    visualize_activity_binned_mean_std(minutes=minutes_cfg, unconstrained=False, with_faa_bars=True)
    visualize_activity_binned_mean_std(minutes=minutes_cfg, unconstrained=True, with_faa_bars=True)
