import numpy as np
import pandas as pd

from social_media.src.config import Config
from social_media.src.dependencies import Dependencies
from social_media.src.metrics.conversation import (
    avg_reply_depth,
    discussion_index,
    max_reply_depth,
    qualified_comment_rate,
    question_comment_rate,
    sentiment_shares,
)


def post_conversation_step(
    dfs: dict[str, pd.DataFrame], config: Config, deps: Dependencies
) -> dict[str, pd.DataFrame]:
    """Adiciona métricas de conversação e qualidade do diálogo ao `posts`."""
    posts = dfs["posts"].copy()
    comments = dfs["comments"]

    if comments.empty:
        for col in [
            "discussion_index",
            "avg_reply_depth",
            "max_reply_depth",
            "qualified_comment_rate",
            "question_comment_rate",
            "sent_positivo_share",
            "sent_neutro_share",
            "sent_negativo_share",
        ]:
            posts[col] = np.nan
    else:
        conversation_metrics = pd.DataFrame(
            {
                "discussion_index": discussion_index(comments),
                "avg_reply_depth": avg_reply_depth(comments),
                "max_reply_depth": max_reply_depth(comments),
                "qualified_comment_rate": qualified_comment_rate(comments),
                "question_comment_rate": question_comment_rate(comments),
            }
        )
        conversation_metrics = conversation_metrics.join(sentiment_shares(comments))

        posts = posts.set_index("id")
        posts = posts.join(conversation_metrics)
        posts = posts.reset_index().rename(columns={"index": "id"})

    dfs = dict(dfs)
    dfs["posts"] = posts
    return dfs
