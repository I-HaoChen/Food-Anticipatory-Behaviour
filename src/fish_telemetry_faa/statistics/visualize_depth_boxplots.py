import plotly.express as px

from src.fish_telemetry_faa.utils.data_loader import init_standard_data


def visualize_boxplots_day_night():
    df = init_standard_data()
    df['fish_number'] = df['fish_number'].rank(method='dense')
    df["Time of day"] = "PLACEHOLDER"
    df.loc[df["time_of_day"] == "Day", "Time of day"] = "Day"
    df.loc[df["time_of_day"] != "Day", "Time of day"] = "Night"
    fig = px.box(data_frame=df, x="fish_number", y="Depth [m] (est. or from tag)", color="Time of day",
                 labels={"fish_number": "Fish number",
                         "Depth [m] (est. or from tag)": "Depth in m"})
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_annotations(font_size=30)
    fig.update_layout(font_size=30)
    fig.update_yaxes(autorange="reversed")
    fig.show()


if __name__ == "__main__":
    visualize_boxplots_day_night()
