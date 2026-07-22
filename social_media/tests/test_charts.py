import pandas as pd
import pytest
from matplotlib.figure import Figure

from social_media.src.charts.captions import plot_caption_word_count_vs_engagement
from social_media.src.charts.overview import (
    plot_likes_comments_timeline,
    plot_posts_by_type,
    plot_top_posts_engagement,
)
from social_media.src.charts.timing import (
    plot_avg_likes_comments_by_weekday,
    plot_engagement_heatmap_hour_weekday,
)


def _sample_posts() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                ["2024-01-15 10:00:00", "2024-01-16 14:00:00", "2024-01-17 20:00:00"]
            ),
            "num_likes": [10, 20, 30],
            "num_comentarios": [1, 2, 3],
            "short_code": ["A", "B", "C"],
            "engagement_rate": [0.1, 0.2, None],
            "comments_per_like": [0.1, 0.1, 0.1],
            "caption_word_count": [5, 10, 15],
            "post_hour": [10, 14, 20],
            "post_weekday": [0, 1, 2],
            "type": ["Image", "Video", "Sidecar"],
        }
    )


def _sample_timing_weekday() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "post_weekday": [0, 1, 2],
            "avg_likes": [10.0, 20.0, 30.0],
            "avg_comments": [1.0, 2.0, 3.0],
        }
    )


@pytest.mark.parametrize(
    "plot_func, df_fixture",
    [
        (plot_likes_comments_timeline, _sample_posts()),
        (plot_top_posts_engagement, _sample_posts()),
        (plot_posts_by_type, _sample_posts()),
        (plot_caption_word_count_vs_engagement, _sample_posts()),
        (plot_engagement_heatmap_hour_weekday, _sample_posts()),
        (plot_avg_likes_comments_by_weekday, _sample_timing_weekday()),
    ],
)
def test_chart_functions_return_figure(plot_func, df_fixture) -> None:
    fig = plot_func(df_fixture)
    assert isinstance(fig, Figure)


@pytest.mark.parametrize(
    "plot_func, df_fixture",
    [
        (plot_likes_comments_timeline, _sample_posts().iloc[:0]),
        (plot_top_posts_engagement, _sample_posts().iloc[:0]),
        (plot_posts_by_type, _sample_posts().iloc[:0]),
        (plot_caption_word_count_vs_engagement, _sample_posts().iloc[:0]),
        (plot_engagement_heatmap_hour_weekday, _sample_posts().iloc[:0]),
        (plot_avg_likes_comments_by_weekday, _sample_timing_weekday().iloc[:0]),
    ],
)
def test_chart_functions_handle_empty_data(plot_func, df_fixture) -> None:
    fig = plot_func(df_fixture)
    assert isinstance(fig, Figure)


def test_avg_likes_comments_by_weekday_fills_all_weekdays() -> None:
    df = pd.DataFrame(
        {
            "post_weekday": [1],
            "avg_likes": [20.0],
            "avg_comments": [2.0],
        }
    )
    fig = plot_avg_likes_comments_by_weekday(df)
    ax = fig.axes[0]
    assert len(ax.get_xticks()) == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
