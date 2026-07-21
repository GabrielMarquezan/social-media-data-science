import pandas as pd

from social_media.src.config import Config
from social_media.src.dependencies import Dependencies
from social_media.src.metrics.timing import (
    aggregate_by_hour,
    aggregate_by_weekday,
    post_hour,
    post_period,
    post_weekday,
)


def timing_step(
    dfs: dict[str, pd.DataFrame], config: Config, deps: Dependencies
) -> dict[str, pd.DataFrame]:
    """Adiciona features de timing ao `posts` e cria agregações por hora/dia."""
    posts = dfs["posts"].copy()

    posts["timestamp"] = pd.to_datetime(posts["timestamp"], errors="coerce")
    posts["post_hour"] = post_hour(posts["timestamp"])
    posts["post_weekday"] = post_weekday(posts["timestamp"])
    posts["post_period"] = post_period(posts["timestamp"])

    timing_by_hour = aggregate_by_hour(posts)
    timing_by_weekday = aggregate_by_weekday(posts)

    dfs = dict(dfs)
    dfs["posts"] = posts
    dfs["timing_by_hour"] = timing_by_hour
    dfs["timing_by_weekday"] = timing_by_weekday
    return dfs
