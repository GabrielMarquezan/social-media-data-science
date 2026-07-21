import numpy as np
import pandas as pd


def _as_series(ts: pd.Series | pd.DatetimeIndex) -> pd.Series:
    if isinstance(ts, pd.DatetimeIndex):
        return pd.Series(ts, index=range(len(ts)))
    return ts


def post_hour(ts: pd.Series | pd.DatetimeIndex) -> pd.Series:
    return _as_series(ts).dt.hour


def post_weekday(ts: pd.Series | pd.DatetimeIndex) -> pd.Series:
    """0=segunda, 6=domingo."""
    return _as_series(ts).dt.weekday


def post_period(ts: pd.Series | pd.DatetimeIndex) -> pd.Series:
    series = _as_series(ts)
    hour = series.dt.hour
    conditions = [
        (hour >= 0) & (hour <= 5),
        (hour >= 6) & (hour <= 11),
        (hour >= 12) & (hour <= 17),
        (hour >= 18) & (hour <= 23),
    ]
    choices = ["Madrugada", "Manhã", "Tarde", "Noite"]
    return pd.Series(np.select(conditions, choices, default="unknown"), index=series.index)


def aggregate_by_hour(posts: pd.DataFrame) -> pd.DataFrame:
    return _aggregate_by_column(posts, "post_hour")


def aggregate_by_weekday(posts: pd.DataFrame) -> pd.DataFrame:
    return _aggregate_by_column(posts, "post_weekday")


def _aggregate_by_column(posts: pd.DataFrame, column: str) -> pd.DataFrame:
    grouped = posts.groupby(column, dropna=False)

    def _mean(col: str) -> pd.Series:
        if col in posts.columns:
            return grouped[col].mean()
        return pd.Series(np.nan, index=grouped.size().index)

    return pd.DataFrame({
        "posts": grouped.size(),
        "avg_likes": grouped["likes_count"].mean(),
        "avg_comments": grouped["comments_count"].mean(),
        "avg_views": _mean("views"),
        "avg_engagement_rate": _mean("engagement_rate"),
        "avg_comments_per_like": _mean("comments_per_like"),
        "avg_qualified_comment_rate": _mean("qualified_comment_rate"),
        "avg_discussion_index": _mean("discussion_index"),
    }).reset_index()
