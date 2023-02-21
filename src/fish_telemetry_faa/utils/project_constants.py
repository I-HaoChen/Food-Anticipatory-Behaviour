from pathlib import Path
from typing import Final

import pandas as pd

ROOT_PATH = Path(__file__).parent.parent.parent.parent


class ProjectConstants():
    ROOT: Final = ROOT_PATH
    DATASETS: Final = ROOT_PATH.joinpath("data")
    SUN_TIMES = DATASETS.joinpath("Sun Times")
    SUN_TIMES_OFFICIAL = SUN_TIMES.joinpath("official_sun_times_2021.csv")
    SUN_TIMES_CIVIL = SUN_TIMES.joinpath("civil_sun_times_2021.csv")
    SUN_TIMES_NAUTICAL = SUN_TIMES.joinpath("nautical_sun_times_2021.csv")
    SUN_TIMES_ASTRONOMICAL = SUN_TIMES.joinpath("astronomical_sun_times_2021.csv")

    CONSTRAINED_TRANSMITTER_DATA = DATASETS.joinpath('Acoustic Transmitters Constrained')
    UNCONSTRAINED_TRANSMITTER_DATA = DATASETS.joinpath('Acoustic Transmitters Unconstrained')
    UNCONSTRAINED_RECEIVER_DATA = UNCONSTRAINED_TRANSMITTER_DATA.joinpath('TagDetections.csv')
    RECEIVER_DATA = DATASETS.joinpath('Receivers')
    RECEIVERS_SENSOR_DATA = RECEIVER_DATA.joinpath('TBRSensorData.csv')

    START_OF_EXPERIMENT = pd.Timestamp(2021, 5, 26)
    END_OF_EXPERIMENT_INCLUSIVE = pd.Timestamp(2021, 6, 7)
    RECEIVER_1425 = {'Latitude': 35.48011, 'Longitude': 24.112, "Depth": 2.5}
    RECEIVER_1426 = {'Latitude': 35.48006, 'Longitude': 24.11209, "Depth": 2.5}
    RECEIVER_1427 = {'Latitude': 35.48, 'Longitude': 24.11196, "Depth": 2.5}
    RECEIVER_MIDDLE = {'Latitude': 35.4800403781513, 'Longitude': 24.112020210084, "Depth": 2.5,
                       "radius_sqr": 0.0000000052556}
    SUNRISE_OFFICIAL = 'sunrise_official'
    SUNRISE_CIVIL = 'sunrise_civil'
    SUNRISE_NAUTICAL = 'sunrise_nautical'
    SUNRISE_ASTRONOMICAL = 'sunrise_astronomical'
    SUNSET_OFFICIAL = 'sunset_official'
    SUNSET_CIVIL = 'sunset_civil'
    SUNSET_NAUTICAL = 'sunset_nautical'
    SUNSET_ASTRONOMICAL = 'sunset_astronomical'

    @classmethod
    def all_key_value_items(cls):
        return {k.upper(): v for k, v in vars(cls).items() if k.isupper()}.items()


if __name__ == "__main__":
    for k, v in ProjectConstants.all_key_value_items():
        print(f"{k}:{v}")
