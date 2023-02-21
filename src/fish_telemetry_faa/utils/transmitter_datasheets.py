import pandas as pd

from src.fish_telemetry_faa.utils.project_constants import ProjectConstants


class TransmitterDataSheet:
    def __init__(self, empty=False):
        self._csv_files = {}
        if not empty:
            self._add_all_csv_files()

    def _add_all_csv_files(self):
        iterator = ProjectConstants.CONSTRAINED_TRANSMITTER_DATA.glob('*.csv')
        for file in iterator:
            self.add_one_csv_file(file)

    def get_csv_files(self):
        return self._csv_files

    def add_one_csv_file(self, file):
        df_indexed = pd.read_csv(file, header=0, skipinitialspace=True)
        df_indexed["time_index"] = pd.to_datetime(df_indexed["Time (UTC)"]) + pd.DateOffset(
            hours=3)  # Crete is +3 towards UTC!
        df_indexed["Time (corrected)"] = pd.to_datetime(df_indexed["Time (UTC)"]) + pd.DateOffset(
            hours=3)  # Crete is +3 towards UTC!
        df_indexed = df_indexed.set_index(df_indexed["time_index"])
        datetime_series = pd.to_datetime(df_indexed.index)
        datetime_index = pd.DatetimeIndex(datetime_series.values)
        df_indexed["datum"] = datetime_index
        df_indexed_datetime = df_indexed.set_index(datetime_index)
        df_indexed_datetime = df_indexed_datetime[
                              ProjectConstants.START_OF_EXPERIMENT:ProjectConstants.END_OF_EXPERIMENT_INCLUSIVE]
        self._csv_files[file.stem] = df_indexed_datetime

    def get_all_current_csv_files_as_one_df(self):
        df = pd.concat(self._csv_files.values(), keys=self._csv_files.keys(), names=["fish_name", "dates"])
        df = self.add_fish_numbers(df)
        return df

    def add_fish_numbers(self, df):
        df["fish_number"] = -1
        for name in sorted(set(df["Name"])):
            identifier = int(name.split("-")[1])
            other_name = name.split("-")[0] + "-" + str(identifier + 1)
            if (df.loc[df["Name"] == name, "fish_number"] == -1).all():
                try:
                    df.loc[df["Name"] == name, "fish_number"] = identifier + 1
                    df.loc[df["Name"] == other_name, "fish_number"] = identifier + 1
                except ValueError:
                    pass
        return df

class UnconstrainedTransmitterDataSheet:
    def __init__(self):
        self.excel_data_df = pd.read_csv(ProjectConstants.UNCONSTRAINED_RECEIVER_DATA, header=0, encoding="utf-8",
                                         skipinitialspace=True, delimiter=";")
        self.add_fish_numbers(self.excel_data_df)
        self.add_3_hours()  # Crete is UTC +3
        self.change_names()

    def get_unconstrained_transmitter_data(self):

        return self.excel_data_df

    def add_fish_numbers(self, df):
        df["fish_number"] = -1
        for idx, df_partly in df.groupby("ID"):
            if idx % 2 == 0:
                df.loc[df["ID"] == idx, "fish_number"] = idx - 1
            else:
                df.loc[df["ID"] == idx, "fish_number"] = idx
        return df

    def add_3_hours(self):

        self.excel_data_df["Time (corrected)"] = pd.to_datetime(
            self.excel_data_df["Date and Time (UTC)"]) + pd.DateOffset(hours=3)
        self.excel_data_df = self.excel_data_df.set_index(["Protocol", "ID", "Time (corrected)"], drop=False)
        self.excel_data_df = self.excel_data_df.drop(columns="Date and Time (UTC)")

    def change_names(self):
        self.excel_data_df['SNR [dB]'] = self.excel_data_df["SNR"]
        self.excel_data_df['Data2 (DS256 only)'] = self.excel_data_df["Data2"]
        self.excel_data_df["datum"] = self.excel_data_df["Time (corrected)"]
        # Fx depth
        self.excel_data_df["Depth [m] (est. or from tag)"] = self.excel_data_df[
            "Depth [m] (est. or from tag)"].str.replace(",", ".")
        self.excel_data_df['Depth [m] (est. or from tag)'] = self.excel_data_df["Depth [m] (est. or from tag)"].astype(
            float)



if __name__ == "__main__":
    data_sheet = TransmitterDataSheet(empty=False)
    df = data_sheet.get_all_current_csv_files_as_one_df()
    df = df.sort_index(level=1)
    print(df)
    data_sheet = UnconstrainedTransmitterDataSheet()
    df = data_sheet.get_unconstrained_transmitter_data()
    df = df.sort_index(level=1)
    print(df)
