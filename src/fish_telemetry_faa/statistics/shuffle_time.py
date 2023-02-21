import numpy as np
import pandas
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from _plotly_utils.colors import n_colors
from numpy.random import lognormal
from scipy.stats import combine_pvalues
from statsmodels.stats.proportion import proportions_chisquare

from src.fish_telemetry_faa.utils.data_loader import init_standard_data, init_unconstrained_tag_data


def get_water_column_counts(df, water_column: str, interval_minutes: int):
    df_resampled = df.loc[df["water_column"] == water_column].resample(f'{interval_minutes}min', label='left',
                                                                       closed='left',
                                                                       offset=f"{0}min",
                                                                       on="Time (corrected)", ).count()
    df_shuffle = df_resampled.copy()
    df_shuffle[:] = df_shuffle.sample(frac=1).values
    counts = df_shuffle.pivot_table(index=df_shuffle.index.hour,
                                    values="water_column",
                                    aggfunc='sum')
    counts[water_column] = counts["water_column"]
    counts = counts.drop(columns="water_column")
    return counts


def get_all_water_column_counts(df, interval_minutes: int = 120):
    all_water_cols = []
    for col in ["0-3m", "3-6m", "6-9m"]:
        all_water_cols.append(get_water_column_counts(df, col, interval_minutes))
    data_frame = pd.DataFrame(pd.concat(all_water_cols, axis=1), columns=["0-3m", "3-6m", "6-9m"])
    return data_frame


def run_proportions_chisquare_on_water_column(index, water_column: str, base_counts, shuffled_counts, verbose=True):
    if verbose:
        print(f"The proportions Stats number {index} for the intervals of the day for {water_column}:")
    stat, p, expected = proportions_chisquare(
        np.array([np.array(base_counts[water_column]), np.array(shuffled_counts[water_column])]),
        nobs=pandas.DataFrame(
            np.array([np.array(base_counts[water_column]), np.array(shuffled_counts[water_column])])).sum(
            axis=0))
    if verbose:
        print(f"{stat=}, {p=}")
    return p


def run_shuffle_test(df, repetitions, interval_minutes, verbose=True):
    base_counts = get_all_water_column_counts(df, interval_minutes=interval_minutes)
    p_value_dict = {"03": [], "36": [], "69": []}
    for i in range(repetitions):
        np.random.seed(i)
        # First sample, THEN permute the data values
        shuffled_counts = get_all_water_column_counts(df, interval_minutes=interval_minutes)

        temp_p_value = run_proportions_chisquare_on_water_column(i, "0-3m", base_counts, shuffled_counts, verbose)
        p_value_dict["03"].append(temp_p_value)
        temp_p_value = run_proportions_chisquare_on_water_column(i, "3-6m", base_counts, shuffled_counts, verbose)
        p_value_dict["36"].append(temp_p_value)
        temp_p_value = run_proportions_chisquare_on_water_column(i, "6-9m", base_counts, shuffled_counts, verbose)
        p_value_dict["69"].append(temp_p_value)

    # Fisher method to combine p values
    stat, p = combine_pvalues(p_value_dict["03"])
    print(f"After fishers method for 03: {stat, p}")
    stat, p = combine_pvalues(p_value_dict["36"])
    print(f"After fishers method for 36: {stat, p}")
    stat, p = combine_pvalues(p_value_dict["69"])
    print(f"After fishers method for 69: {stat, p}")


def run_shuffle_test_time(repetitions, interval_minutes: int, individual_days=False, unconstrained=False, verbose=True):
    if unconstrained:
        df = init_unconstrained_tag_data()
    else:
        df = init_standard_data()
        df["water_column"] = "ERROR"
    df.loc[df["Depth [m] (est. or from tag)"] < 3, "water_column"] = "0-3m"
    df.loc[(3 <= df["Depth [m] (est. or from tag)"]) & (
            df["Depth [m] (est. or from tag)"] < 6), "water_column"] = "3-6m"
    df.loc[6 <= df["Depth [m] (est. or from tag)"], "water_column"] = "6-9m"
    if individual_days:
        for date in sorted(set(df["Time (corrected)"].dt.date)):
            print(f"Run shuffle test time for Day {date}")
            run_shuffle_test(df.loc[df["Time (corrected)"].dt.date == date], repetitions, interval_minutes,
                             verbose)
    else:
        run_shuffle_test(df, repetitions, interval_minutes)


def plot_no_shuffled_data_time_of_days(df):
    fig = px.histogram(df, y="Depth [m] (est. or from tag)",
                       color="time_of_day",
                       barmode="relative",
                       barnorm="percent",
                       histnorm="density",
                       labels={"time_of_day": "Time of day", "water_column": "Water col.",
                               "Depth [m] (est. or from tag)": "Depth in m"},
                       category_orders={"water_column": ["0-3m", "3-6m", "6-9m"],
                                        "time_of_day": ['Night', 'Astronomical Twilight', 'Nautical Twilight',
                                                        'Civil Twilight', 'Day']},
                       color_discrete_sequence=n_colors('rgb(0, 0, 0)', 'rgb(240, 240, 240)', 5, colortype='rgb')
                       )
    fig.update_traces(ybins_size=3)
    fig.update_layout(
        yaxis=dict(autorange="reversed")
    )
    fig.add_shape(
        go.layout.Shape(type='line', xref='x', yref='paper',
                        x0=0, y0=0.66666666, x1=100, y1=0.66666666, line=dict(color='grey', width=4)),
    )
    fig.add_shape(
        go.layout.Shape(type='line', xref='x', yref='paper',
                        x0=0, y0=0.33333333, x1=100, y1=0.33333333, line=dict(color='grey', width=4)),
    )
    fig.update_layout(legend=dict(bgcolor=px.colors.qualitative.Pastel1[1]))
    fig.update_annotations(font_size=30)
    fig.update_layout(font_size=30)

    fig.update_layout(xaxis_title="Density (normalized as percent)")
    fig.show()


def visualize_no_shuffled_data_time_of_days(unconstrained=False, individual_days=False):
    if unconstrained:
        df = init_unconstrained_tag_data()
    else:
        df = init_standard_data()
    df["water_column"] = "ERROR"
    df.loc[df["Depth [m] (est. or from tag)"] < 3, "water_column"] = "0-3m"
    df.loc[(3 <= df["Depth [m] (est. or from tag)"]) & (
            df["Depth [m] (est. or from tag)"] < 6), "water_column"] = "3-6m"
    df.loc[6 <= df["Depth [m] (est. or from tag)"], "water_column"] = "6-9m"
    if individual_days:
        for date in sorted(set(df["Time (corrected)"].dt.date)):
            plot_no_shuffled_data_time_of_days(df.loc[df["Time (corrected)"].dt.date == date])
    else:
        plot_no_shuffled_data_time_of_days(df)


def plot_no_shuffled_data(df):
    fig = px.histogram(df, y="Depth [m] (est. or from tag)",
                       color="time_of_day_interval",
                       barmode="relative",
                       barnorm="percent",
                       histnorm="density",
                       labels={"time_of_day_interval": "Time interval", "water_column": "Water col.",
                               "Depth [m] (est. or from tag)": "Depth in m"},
                       category_orders={"water_column": ["0-3m", "3-6m", "6-9m"]},
                       color_discrete_sequence=n_colors('rgb(50, 50, 50)', 'rgb(240, 240, 240)', 3,
                                                        colortype='rgb') + n_colors('rgb(270,270,270)',
                                                                                    'rgb(75, 75, 75)', 3,
                                                                                    colortype='rgb')
                       )
    fig.add_shape(
        go.layout.Shape(type='line', xref='x', yref='paper',
                        x0=0, y0=0.66666666, x1=100, y1=0.66666666, line=dict(color='grey', width=4)),
    )
    fig.add_shape(
        go.layout.Shape(type='line', xref='x', yref='paper',
                        x0=0, y0=0.33333333, x1=100, y1=0.33333333, line=dict(color='grey', width=4)),
    )
    fig.update_traces(ybins_size=3)
    fig.update_layout(
        yaxis=dict(autorange="reversed")
    )
    fig.update_layout(legend=dict(bgcolor=px.colors.qualitative.Pastel1[1]))
    fig.update_layout(legend=dict(
        xanchor="right",  # changed
        x=-0.1
    ))
    fig.update_annotations(font_size=30)
    fig.update_layout(font_size=30)
    fig.update_layout(xaxis_title="Density (normalized as percent)")
    fig.update_layout(showlegend=False)
    fig.show()


def visualize_no_shuffled_data(with_night, short_nights, unconstrained=False, individual_days=False):
    if unconstrained:
        df = init_unconstrained_tag_data(short_nights=short_nights)
    else:
        df = init_standard_data(short_nights=short_nights)
    df["water_column"] = "ERROR"
    df.loc[df["Depth [m] (est. or from tag)"] < 3, "water_column"] = "0-3m"
    df.loc[(3 <= df["Depth [m] (est. or from tag)"]) & (
            df["Depth [m] (est. or from tag)"] < 6), "water_column"] = "3-6m"
    df.loc[6 <= df["Depth [m] (est. or from tag)"], "water_column"] = "6-9m"
    if not with_night:
        df = df.loc[df["time_of_day_interval"] != "Official Night Time"]
    if individual_days:
        for date in sorted(set(df["Time (corrected)"].dt.date)):
            plot_no_shuffled_data(df.loc[df["Time (corrected)"].dt.date == date])
    else:
        plot_no_shuffled_data(df)


def plot_shuffled_data(df, with_night=False):
    df["time_of_day_interval"] = np.random.permutation(df["time_of_day_interval"])
    category_orders_time_of_day_intervals = ["Official Night Time",
                                             "Sunrise to 8:00", "8:00 to 10:00",
                                             "10:00 to 12:00", "12:00 to 14:00", "14:00 to 16:00",
                                             "16:00 to Sunset"]
    if not with_night:
        df = df.loc[df["time_of_day_interval"] != "Official Night Time"]
        category_orders_time_of_day_intervals = ["Sunrise to 8:00", "8:00 to 10:00",
                                                 "10:00 to 12:00", "12:00 to 14:00", "14:00 to 16:00",
                                                 "16:00 to Sunset"]

    fig = px.histogram(df, y="Depth [m] (est. or from tag)",
                       color="time_of_day_interval",
                       barmode="relative",
                       barnorm="percent",
                       histnorm="density",
                       labels={"time_of_day_interval": "Time interval", "water_column": "Water col.",
                               "Depth [m] (est. or from tag)": "Depth in m"},
                       category_orders={"water_column": ["0-3m", "3-6m", "6-9m"],
                                        "time_of_day_interval": category_orders_time_of_day_intervals},
                       color_discrete_sequence=n_colors('rgb(50, 50, 50)', 'rgb(240, 240, 240)', 3,
                                                        colortype='rgb') + n_colors('rgb(270,270,270)',
                                                                                    'rgb(75, 75, 75)', 3,
                                                                                    colortype='rgb')
                       )
    fig.add_shape(
        go.layout.Shape(type='line', xref='x', yref='paper',
                        x0=0, y0=0.66666666, x1=100, y1=0.66666666, line=dict(color='grey', width=4)),
    )
    fig.add_shape(
        go.layout.Shape(type='line', xref='x', yref='paper',
                        x0=0, y0=0.33333333, x1=100, y1=0.33333333, line=dict(color='grey', width=4)),
    )
    fig.update_traces(ybins_size=3)
    fig.update_layout(legend=dict(bgcolor=px.colors.qualitative.Pastel1[1]))
    fig.update_layout(
        yaxis=dict(autorange="reversed")
    )
    fig.update_annotations(font_size=30)
    fig.update_layout(font_size=30)
    fig.update_layout(xaxis_title="Density (normalized as percent)")
    fig.show()


def visualize_time_shuffled_data(with_night, short_nights, unconstrained=False, individual_days=False):
    if unconstrained:
        df = init_unconstrained_tag_data(short_nights=short_nights)
    else:
        df = init_standard_data(short_nights=short_nights)
    df["water_column"] = "ERROR"
    df.loc[df["Depth [m] (est. or from tag)"] < 3, "water_column"] = "0-3m"
    df.loc[(3 <= df["Depth [m] (est. or from tag)"]) & (
            df["Depth [m] (est. or from tag)"] < 6), "water_column"] = "3-6m"
    df.loc[6 <= df["Depth [m] (est. or from tag)"], "water_column"] = "6-9m"
    if not with_night:
        df = df.loc[df["time_of_day_interval"] != "Official Night Time"]
    # df[:] = df.sample(frac=1).values
    if individual_days:
        for date in sorted(set(df["Time (corrected)"].dt.date)):
            plot_shuffled_data(df.loc[df["Time (corrected)"].dt.date == date])
    else:
        plot_shuffled_data(df)


if __name__ == "__main__":
    interval_minutes_cfg = 20
    unconstrained = False
    individual_days = False
    run_shuffle_test_time(repetitions=10000, interval_minutes=interval_minutes_cfg, individual_days=individual_days,
                          unconstrained=False, verbose=False)  # stat 4
    run_shuffle_test_time(repetitions=10000, interval_minutes=interval_minutes_cfg, individual_days=individual_days,
                          unconstrained=True, verbose=False)  # stat 4
    visualize_no_shuffled_data_time_of_days(unconstrained=unconstrained, individual_days=individual_days)
    with_night = False
    visualize_no_shuffled_data(with_night, short_nights=False, unconstrained=unconstrained, individual_days=individual_days)
    visualize_time_shuffled_data(with_night, unconstrained=unconstrained, individual_days=individual_days, short_nights=False)
