import numpy as np
import pandas as pd

from social_media.src.config import Config
from social_media.src.dependencies import Dependencies
from social_media.src.metrics.content_type import community_index, new_commenter_share


def content_type_step(
    dfs: dict[str, pd.DataFrame], config: Config, deps: Dependencies
) -> dict[str, pd.DataFrame]:
    """Cria agregações de métricas por tipo de conteúdo."""
    posts = dfs["posts"].copy()
    comments = dfs["comments"]

    if posts.empty:
        dfs = dict(dfs)
        dfs["content_by_type"] = _empty_content_by_type_df()
        return dfs

    grouped = posts.groupby("type", dropna=False)

    agg = pd.DataFrame(
        {
            "posts": grouped.size(),
            "num_likes": grouped["likes_count"].sum(),
            "num_comentarios": grouped["comments_count"].sum(),
            "visualizacoes": grouped["views"].sum(),
            "avg_engagement_rate": grouped["engagement_rate"].mean(),
            "avg_comments_per_view": grouped["comments_per_view"].mean(),
            "avg_qualified_comment_rate": grouped["qualified_comment_rate"].mean(),
            "avg_discussion_index": grouped["discussion_index"].mean(),
        }
    ).reset_index()

    agg["community_index"] = community_index(posts, comments).reindex(agg["type"]).values
    agg["new_commenter_share"] = (
        new_commenter_share(posts, comments).reindex(agg["type"]).values
    )

    # Substitui NaN por None de forma explícita para colunas que podem ficar vazias
    for col in ("community_index", "new_commenter_share"):
        agg[col] = agg[col].replace({np.nan: None})

    dfs = dict(dfs)
    dfs["content_by_type"] = agg
    return dfs


def _empty_content_by_type_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "type",
            "posts",
            "num_likes",
            "num_comentarios",
            "visualizacoes",
            "avg_engagement_rate",
            "avg_comments_per_view",
            "avg_qualified_comment_rate",
            "avg_discussion_index",
            "community_index",
            "new_commenter_share",
        ]
    )
