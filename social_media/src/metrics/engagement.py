import numpy as np
import pandas as pd


def num_likes(df: pd.DataFrame) -> pd.Series:
    return df["likes_count"]


def num_comentarios(df: pd.DataFrame) -> pd.Series:
    return df["comments_count"]


def engagement_rate(
    likes: pd.Series, comments: pd.Series, views: pd.Series
) -> pd.Series:
    """(likes + comments) / views — apenas quando views existe e é maior que zero."""
    valid = views.notna() & (views > 0)
    return pd.Series(
        np.where(valid, (likes.fillna(0) + comments.fillna(0)) / views, np.nan),
        index=likes.index,
    )


def comments_per_view(comments: pd.Series, views: pd.Series) -> pd.Series:
    """comments / views — apenas quando views existe e é maior que zero."""
    valid = views.notna() & (views > 0)
    return pd.Series(
        np.where(valid, comments.fillna(0) / views, np.nan),
        index=comments.index,
    )


def comments_per_like(comments: pd.Series, likes: pd.Series) -> pd.Series:
    """comments / likes — apenas quando likes existe e é maior que zero."""
    valid = likes.notna() & (likes > 0)
    return pd.Series(
        np.where(valid, comments.fillna(0) / likes, np.nan),
        index=comments.index,
    )
