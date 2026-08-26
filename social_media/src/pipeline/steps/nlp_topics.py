import logging

import pandas as pd

from social_media.src.config import Config
from social_media.src.dependencies import Dependencies
from social_media.src.nlp.topics import TOPIC_COLUMNS, fit_comment_topics

logger = logging.getLogger(__name__)


def nlp_topics_step(
    dfs: dict[str, pd.DataFrame], config: Config, deps: Dependencies
) -> dict[str, pd.DataFrame]:
    """Gera tópicos para comentários usando BERTopic."""
    comments = dfs.get("comments")

    if comments is None or comments.empty:
        dfs = dict(dfs)
        dfs["comment_topics"] = pd.DataFrame(columns=TOPIC_COLUMNS)
        return dfs

    texts = comments["text"].fillna("").tolist()
    embedding_model = deps.get_embedding_model()

    _, topics_df = fit_comment_topics(
        texts,
        embedding_model,
        n_topics=config.nlp_topic_count,
        top_n=config.nlp_topic_terms_limit,
    )

    dfs = dict(dfs)
    dfs["comment_topics"] = topics_df
    return dfs
