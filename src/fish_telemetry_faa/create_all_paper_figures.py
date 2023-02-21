from src.fish_telemetry_faa.clustering.dbscan_clustering import run_dbscan_clustering_time_depth
from src.fish_telemetry_faa.statistics.ks_test_activity import seasonal_decomposition_of_activity
from src.fish_telemetry_faa.statistics.shuffle_time import visualize_no_shuffled_data_time_of_days, \
    visualize_no_shuffled_data, visualize_time_shuffled_data
from src.fish_telemetry_faa.statistics.visualize_activity import visualize_activity_binned_mean_std
from src.fish_telemetry_faa.statistics.visualize_depth_boxplots import visualize_boxplots_day_night
from src.fish_telemetry_faa.utils.data_loader import init_unconstrained_tag_data, init_standard_data


def create_figure_2():
    visualize_no_shuffled_data_time_of_days(unconstrained=False, individual_days=False)


def create_figure_3ab():
    visualize_no_shuffled_data(with_night=False, short_nights=False, unconstrained=False, individual_days=False)
    visualize_time_shuffled_data(with_night=False, short_nights=False, unconstrained=False, individual_days=False)


def create_figure_4():
    visualize_boxplots_day_night()


def create_figure_5_8_9_10():
    unconstrained = False
    by_day = False
    weights = [0.5, 300]
    clusters = 10
    if unconstrained:
        data = init_unconstrained_tag_data()
    else:
        data = init_standard_data()
    run_dbscan_clustering_time_depth(df=data,
                                     weights=weights,
                                     n_clusters=clusters,
                                     visualize=True, day_by_day=by_day)


def create_figure_6():
    visualize_activity_binned_mean_std(minutes=20, unconstrained=False, with_faa_bars=True)


def create_figure_7():
    seasonal_decomposition_of_activity(minutes=20)  # stat 7


def create_figure_S1():
    visualize_activity_binned_mean_std(minutes=20, unconstrained=True, with_faa_bars=True)


def create_figure_S2():
    visualize_no_shuffled_data_time_of_days(unconstrained=True, individual_days=False)


def create_figure_S3ab():
    visualize_no_shuffled_data(with_night=False, short_nights=False, unconstrained=True, individual_days=False)
    visualize_time_shuffled_data(with_night=False, short_nights=False, unconstrained=True, individual_days=False)


def create_figure_S4_12():
    run_dbscan_clustering_time_depth(df=init_standard_data(),
                                     weights=[0.5, 25],
                                     n_clusters=10,
                                     visualize=True, day_by_day=True)


if __name__ == "__main__":
    print("Coded Figures for paper are being created")
    create_figure_2()
    create_figure_3ab()
    create_figure_4()
    create_figure_5_8_9_10()
    create_figure_6()
    create_figure_7()
    print("Coded Supplementary Figures for paper are being created")
    create_figure_S1()
    create_figure_S2()
    create_figure_S3ab()
    create_figure_S4_12()
