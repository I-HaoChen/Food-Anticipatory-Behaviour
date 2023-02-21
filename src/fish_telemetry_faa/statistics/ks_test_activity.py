# import pandas
import plotly.graph_objects as go
# from kats.consts import TimeSeriesData
# from kats.tsfeatures.tsfeatures import TsFeatures
from scipy.stats import ks_2samp
from statsmodels.tsa.seasonal import seasonal_decompose

from src.fish_telemetry_faa.utils.data_loader import init_standard_data, init_unconstrained_tag_data


def ks_test_act_with_unconstrained_act_tags(minutes=20):
    df = init_standard_data()
    df_2 = init_unconstrained_tag_data()
    df = df.loc[df["is_activity"]]
    df_2 = df_2.loc[df_2["is_activity"]]

    df = df.resample(f'{minutes}min', label='left', closed='left',
                     offset=f"{0}min",
                     on="Time (corrected)").mean()
    df_2 = df_2.resample(f'{minutes}min', label='left', closed='left',
                         offset=f"{0}min",
                         on="Time (corrected)").mean()
    df["time_resampled"] = df.index
    df_2["time_resampled"] = df_2.index
    ks_result = ks_2samp(df["activity"], df_2["activity"])
    print(ks_result)


# Uncomment this method and the needed imports when the OS is ubuntu. The kats package does not work on Windows.

# def activity_features(minutes):
#     df = init_standard_data()
#     df = df.loc[df["is_activity"]]
#     df = df.resample(f'{minutes}min', label='left', closed='left',
#                      offset=f"{0}min",
#                      on="Time (corrected)").mean()
#     df["time"] = df.index
#     df["time"] = pandas.to_datetime(df["time"])
#     ts = TimeSeriesData(df[["activity", "time"]])
#     features = TsFeatures().transform(ts)
#     print(features)


def seasonal_decomposition_of_activity(minutes):
    df = init_standard_data()
    df = df.loc[df["is_activity"]]
    df = df.resample(f'{minutes}min', label='left', closed='left',
                     offset=f"{0}min",
                     on="Time (corrected)").mean()
    # seasonal decomposition of observed data
    # 24*3 for daily pattern
    result = seasonal_decompose(df["activity"], model="additive", period=24 * 3)
    fig = go.Figure()
    fig.add_trace(go.Line(x=result.trend.index, y=result.trend, mode='lines', name="Trend", line=dict(color='blue')))
    fig.add_trace(
        go.Line(x=result.seasonal.index, y=result.seasonal, mode='lines', name="Seasonal", line=dict(color='orange')))
    fig.add_trace(
        go.Line(x=result.resid.index, y=result.resid, mode='lines', name="Residual", line=dict(color='green')))
    fig.add_trace(
        go.Line(x=result.observed.index, y=result.observed, mode='lines', name="Observed", line=dict(color='red')))
    fig.update_annotations(font_size=30)
    fig.update_layout(font_size=30)
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    ))
    fig.update_layout(
        yaxis_title='Activity in m/s²',
    )
    fig.show()


if __name__ == "__main__":
    minutes = 20
    activity_features(minutes)  # stat 7
    ks_test_act_with_unconstrained_act_tags(minutes)  # stat 3, different distribution
    seasonal_decomposition_of_activity(minutes)  # stat 7
