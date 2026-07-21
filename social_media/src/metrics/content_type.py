import numpy as np
import pandas as pd


def community_index(posts: pd.DataFrame, comments: pd.DataFrame) -> pd.Series:
    """Comentaristas recorrentes / comentaristas únicos por post."""
    if comments.empty:
        return pd.Series(dtype="float64")

    merged = comments.merge(posts[["id", "type"]], left_on="post_id", right_on="id")
    unique_commenters = (
        merged.groupby(["type", "owner_id"])
        .size()
        .reset_index(name="posts_commented")
    )
    recurring = (
        unique_commenters[unique_commenters["posts_commented"] > 1]
        .groupby("type")
        .size()
    )
    total_unique = unique_commenters.groupby("type").size()
    index = total_unique.index
    return pd.Series(
        np.where(
            total_unique > 0,
            recurring.reindex(index).fillna(0) / total_unique,
            np.nan,
        ),
        index=index,
    )


def new_commenter_share(posts: pd.DataFrame, comments: pd.DataFrame) -> pd.Series:
    """% de comentários de usuários que aparecem em apenas um post por tipo."""
    if comments.empty:
        return pd.Series(dtype="float64")

    merged = comments.merge(posts[["id", "type"]], left_on="post_id", right_on="id")
    posts_per_commenter = (
        merged.groupby(["type", "owner_id"])
        .size()
        .reset_index(name="posts_commented")
    )
    new_commenters = posts_per_commenter[posts_per_commenter["posts_commented"] == 1][
        ["type", "owner_id"]
    ]

    merged_with_status = merged.merge(
        new_commenters, on=["type", "owner_id"], how="left", indicator="is_new"
    )
    merged_with_status["is_new"] = merged_with_status["is_new"] == "both"

    total = merged_with_status.groupby("type").size()
    new_count = merged_with_status[merged_with_status["is_new"]].groupby("type").size()
    index = total.index
    return pd.Series(
        np.where(
            total > 0,
            new_count.reindex(index).fillna(0) / total,
            np.nan,
        ),
        index=index,
    )
