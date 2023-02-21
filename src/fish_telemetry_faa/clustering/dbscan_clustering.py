from itertools import cycle

import numpy as np
import pandas as pd
import plotly
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
from _plotly_utils.colors import n_colors
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import DBSCAN

from src.fish_telemetry_faa.statistics.basic_activity_stats import identify_lasting_peaks_all_dates
from src.fish_telemetry_faa.utils.data_loader import init_standard_data, init_unconstrained_tag_data
from src.fish_telemetry_faa.utils.sun_times import SunTimer


def convert_hour2angle(hour):
    return (hour * 15) % 360


def normalize_hour_suffix(hour):
    # Normalize hour to be between 1 and 12
    hour_as_str = str(((hour - 1) % 12) + 1)
    suffix = ' AM' if (hour % 24) < 12 else ' PM'
    return hour_as_str + suffix


def create_distplot(cluster_df, color_discrete_sequence, label_set,
                    column_name: str = "Depth [m] (est. or from tag)", ):
    # Getting each labels data points out, then extract depth
    distplot_data = [
        list(cluster_df.loc[cluster_df["cluster"] == str(x)][column_name].to_numpy())
        for x in reversed(label_set)]
    colors = list(reversed(color_discrete_sequence))
    fig = ff.create_distplot(distplot_data,
                             ["Cluster " + str(x) if x != -1 else "Noise points" for x in reversed(label_set)],
                             bin_size=.05,
                             show_rug=False,
                             colors=colors[len(colors) - len(label_set):])
    fig.update_layout(
        font=dict(size=30)
    )
    fig.update_layout(
        yaxis_title='Probability',
        xaxis_title='Depth in m',
    )
    fig.update_annotations(font_size=30)
    fig.update_layout(font_size=30)
    fig.show()


def create_polarplot(cluster_df, color_discrete_sequence, column_name: str = "Depth [m] (est. or from tag)",
                     reverse_axis: bool = True):
    colors = cycle(color_discrete_sequence)
    data = []
    cluster_df["cluster_numeric"] = cluster_df["cluster"].astype(int)
    for name, group in cluster_df.groupby('cluster_numeric'):
        if name == -1:
            name = "Noise points"
        else:
            name = f"Cluster {name}"
        data.append(
            go.Scatterpolar(
                r=group[column_name],
                theta=[convert_hour2angle(x) for x in group["time_numeric"]],
                mode='markers',
                marker=dict(
                    color=next(colors)
                ),
                name=name,
            ))

    # Make font bold and bigger, add angle to th text in the radial axis
    layout = go.Layout()

    layout.polar.angularaxis.direction = 'clockwise'
    layout.polar.angularaxis.tickvals = [convert_hour2angle(hr) for hr in range(24)]
    layout.polar.angularaxis.ticktext = [normalize_hour_suffix(hr) for hr in range(24)]
    # Make the axes bold and big
    layout.polar.angularaxis.tickfont = dict(family='Arial Black', size=30)
    layout.polar.angularaxis.ticksuffix = "m <b>"
    layout.polar.angularaxis.tickprefix = "<b>"

    layout.polar.radialaxis.tickfont = dict(family='Arial Black', size=30)
    layout.polar.radialaxis.ticksuffix = "m <b>"
    layout.polar.radialaxis.tickprefix = "<b>"
    layout.polar.radialaxis.tickangle = +45
    if column_name == "Depth [m] (est. or from tag)":
        layout.polar.radialaxis.range = [0, 9]
    elif column_name == "activity":
        layout.polar.radialaxis.range = [0, 3.5]
        layout.polar.radialaxis.tickangle = -225
        layout.polar.radialaxis.angle = 180
        layout.polar.radialaxis.ticksuffix = "m/s² <b>"

    fig = go.FigureWidget(data=data, layout=layout)
    if reverse_axis:
        fig.update_polars(radialaxis=dict(autorange="reversed"))  # Inverting depth

    fig.update_annotations(font_size=30)
    fig.update_layout(font_size=30)
    fig.show()


def create_2d_scatterplot_fab(cluster_df, color_discrete_sequence, label_set,
                              column_name: str = "Depth [m] (est. or from tag)", reverse_axis: bool = True,
                              with_faa_bars=True, with_fap_rectangles=True, with_day_night_bars=True):
    fig = px.scatter(cluster_df.loc[cluster_df["cluster"] != "-1"], x="time_numeric", y=column_name, color="cluster",
                     category_orders={"cluster": [str(x) for x in label_set]},
                     color_discrete_sequence=color_discrete_sequence,
                     labels={"time_numeric": "Hours of the day", "water_column": "Water col.",
                             "Depth [m] (est. or from tag)": "Depth in m"},
                     )
    fig.add_trace(
        go.Scatter(x=cluster_df.loc[cluster_df["cluster"] == "-1"]["time_numeric"],
                   y=cluster_df.loc[cluster_df["cluster"] == "-1"][column_name],
                   opacity=0.3,
                   mode='markers',
                   marker=dict(color=color_discrete_sequence[0])
                   ))
    if with_fap_rectangles:
        sun_rise = 6.15  # mean during the experiment
        feeding_start = 8
        fig.add_trace(go.Scatter(x=[sun_rise, sun_rise, feeding_start, feeding_start, sun_rise],
                                 y=[0, 3, 3, 0, 0], mode='lines+text',
                                 # opacity=0.5,
                                 text=["", "P-FAP", "", "", ""],
                                 textposition="bottom center",
                                 fill="toself",
                                 textfont=dict(
                                     family="Times New Roman",
                                     size=30,
                                 ), fillcolor=plotly.colors.qualitative.Set3[5],
                                 line=dict(color=plotly.colors.qualitative.Set3[6])
                                 ))
        fig.update_layout(uniformtext_minsize=30, uniformtext_mode='hide')
        for cluster_number in ["0", "1"]:
            cluster_with_number = cluster_df.loc[cluster_df["cluster"] == cluster_number]
            min_depth = cluster_with_number["Depth [m] (est. or from tag)"].min()
            max_depth = cluster_with_number["Depth [m] (est. or from tag)"].max()
            min_time = cluster_with_number["time_numeric"].min()
            max_time = cluster_with_number["time_numeric"].max()
            fig.add_trace(go.Scatter(x=[min_time, min_time, max_time, max_time, min_time],
                                     y=[min_depth, max_depth, max_depth, min_depth, min_depth], mode='lines+text',
                                     text=["", "", "", "D-FAP", ""],
                                     textposition="top center",
                                     fill="toself",
                                     textfont=dict(
                                         family="Times New Roman",
                                         size=30,
                                     ), fillcolor=plotly.colors.qualitative.Set3[1],
                                     line=dict(color=plotly.colors.qualitative.Set3[0])
                                     ))
            fig.update_layout(uniformtext_minsize=30, uniformtext_mode='hide')
    if reverse_axis:
        fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        font=dict(size=24)
    )
    if with_faa_bars:
        faa_list = identify_lasting_peaks_all_dates(unconstrained=False, minutes=5)
        for dff in faa_list:
            unpacked_df = dff[0]
            # Always cut off at 8:00
            unpacked_df = unpacked_df.loc[(unpacked_df["time"].dt.hour <= 7) | (
                    (unpacked_df["time"].dt.hour <= 8) & (unpacked_df["time"].dt.minute == 0))]
            fig.add_vrect(x0=unpacked_df["time"].dt.hour[0] + unpacked_df["time"].dt.minute[0] / 60,
                          x1=unpacked_df["time"].dt.hour[-1] + unpacked_df["time"].dt.minute[-1] / 60,
                          annotation_text="FAA", annotation_position="top left",
                          annotation=dict(font_size=30, font_family="Times New Roman"),
                          fillcolor="darkgreen", opacity=0.25, line_width=0)
    if with_day_night_bars:
        greys_dark = n_colors('rgb(0, 0, 0)', 'rgb(255, 255, 255)', 5, colortype='rgb')
        sun_timer = SunTimer()
        sun_times_df = sun_timer.get_all_sun_times_variations()
        fig.add_shape(type="rect",
                      x0='0', y0=7,
                      x1='24', y1=7.8,
                      fillcolor=greys_dark[0],
                      line=dict(width=0)
                      )
        for date in [pd.to_datetime("2021-06-01")]:
            for tw_type, colour in zip(["astronomical", "nautical", "civil", "official"],
                                       greys_dark[1:6]):
                correct_twilight = sun_times_df.loc[sun_times_df["Datum"].dt.date == date].loc[
                    sun_times_df["type"] == tw_type]
                sunrise_of_that_day = pd.to_datetime(
                    correct_twilight["Datum"].astype(str) + " " + correct_twilight["sunrise"])
                sunset_of_that_day = pd.to_datetime(
                    correct_twilight["Datum"].astype(str) + " " + correct_twilight["sunset"])
                sunrise_of_that_day = sunrise_of_that_day.dt.hour + sunrise_of_that_day.dt.minute / 60
                sunset_of_that_day = sunset_of_that_day.dt.hour + sunset_of_that_day.dt.minute / 60
                fig.add_shape(type="rect",
                              x0=sunrise_of_that_day.astype(str).values[0], y0=7,
                              x1=sunset_of_that_day.astype(str).values[0], y1=7.8,
                              fillcolor=colour,
                              line=dict(width=0)
                              )
    fig.update_annotations(font_size=30)
    fig.update_layout(font_size=30)
    fig.update_layout(showlegend=False)
    fig.update_xaxes(range=(0, 24))
    fig.show()


def create_2d_histogram(cluster_df, column_name: str = "Depth [m] (est. or from tag)",
                        reverse_axis: bool = True):
    fig = go.Figure()
    fig.add_trace(go.Histogram2dContour(
        x=cluster_df["time_numeric"],
        y=cluster_df[column_name],
        colorscale='Blues',
        reversescale=True,
        nbinsx=64,
        nbinsy=48,
        xaxis='x',
        yaxis='y',
        colorbar={"title": 'Counts'}
    ))
    fig.add_hline(y=2, line_dash='dash', line_color='Red', line_width=4)
    if reverse_axis:
        fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        showlegend=True
    )
    fig.update_layout(
        xaxis_title="Hours of the day",
        yaxis_title="Depth in m")
    fig.update_annotations(font_size=30)
    fig.update_layout(font_size=30)
    fig.show()


def visualize_clustering_with_labels(cluster_df, color_discrete_sequence, label_set,
                                     column_name: str = "Depth [m] (est. or from tag)",
                                     reverse_axis: bool = True,
                                     with_faa_bars=True, with_fap_rectangles=True, with_day_night_bars=True,
                                     day_by_day=False):
    if not day_by_day:
        create_distplot(cluster_df, color_discrete_sequence, label_set, column_name)

    create_polarplot(cluster_df, color_discrete_sequence, column_name, reverse_axis)

    if not day_by_day:
        create_2d_scatterplot_fab(cluster_df, color_discrete_sequence, label_set, column_name, reverse_axis,
                                  with_faa_bars, with_fap_rectangles, with_day_night_bars)

    if not day_by_day:
        create_2d_histogram(cluster_df, column_name, reverse_axis)


def run_clustering(df, clustering_weights, n_clusters=10,
                   visualize=True, day_by_day=False):
    cluster_df = df[["Depth [m] (est. or from tag)", "time_numeric"]]
    print(len(cluster_df))
    depth_array = cluster_df["Depth [m] (est. or from tag)"].values.reshape(
        cluster_df["Depth [m] (est. or from tag)"].shape[0], 1)
    time_array = cluster_df["time_numeric"].values.reshape(cluster_df["time_numeric"].shape[0], 1)
    pd_1 = pdist(depth_array)
    pd_2 = pdist(time_array)
    # Apply boundary condition to the time component
    pd_2[pd_2 > 24 * 0.5] -= 24
    norm_values = np.linalg.norm(np.stack((pd_1, pd_2)), axis=0)
    square = squareform(norm_values)
    clustering = DBSCAN(eps=clustering_weights[0], min_samples=clustering_weights[1], metric='precomputed').fit(square)

    labels = clustering.labels_
    color_discrete_sequence = px.colors.qualitative.Alphabet if n_clusters > 10 else px.colors.qualitative.Plotly
    cluster_df = cluster_df.assign(cluster=[str(x) for x in labels])
    label_set = sorted(set(labels))
    if visualize:
        visualize_clustering_with_labels(cluster_df=cluster_df, color_discrete_sequence=color_discrete_sequence,
                                         label_set=label_set, day_by_day=day_by_day)


def run_dbscan_clustering_time_depth(df, weights, n_clusters=10,
                                     visualize=True, day_by_day: bool = False):
    if day_by_day:
        for date, group in df.groupby(df["Time (corrected)"].dt.date):
            print(f"Clustering for date {date}")
            small_df = group
            run_clustering(small_df, weights, n_clusters, visualize, day_by_day)
    else:
        print(f"Clustering for all dates")
        run_clustering(df, weights, n_clusters, visualize)


if __name__ == "__main__":
    # cluster 1
    unconstrained = False
    by_day = False
    parameters = [0.5, 300]
    clusters = 10
    if unconstrained:
        data = init_unconstrained_tag_data()
    else:
        data = init_standard_data()
    run_dbscan_clustering_time_depth(df=data,
                                     weights=parameters,
                                     n_clusters=clusters,
                                     visualize=True, day_by_day=by_day)
