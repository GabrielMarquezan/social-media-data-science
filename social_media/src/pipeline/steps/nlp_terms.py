import logging
from typing import Any

import pandas as pd

from social_media.src.config import Config
from social_media.src.dependencies import Dependencies
from social_media.src.nlp.terms import extract_top_terms

logger = logging.getLogger(__name__)


def nlp_terms_step(
    dfs: dict[str, pd.DataFrame], config: Config, deps: Dependencies
) -> dict[str, pd.DataFrame]:
    """Gera top terms para legendas e comentários."""
    posts = dfs.get("posts")
    comments = dfs.get("comments")

    nlp = deps.get_spacy_nlp()
    embedding_model = deps.get_embedding_model()

    caption_terms = _extract_caption_terms(posts, nlp, embedding_model, config)
    comment_terms = _extract_comment_terms(comments, nlp, embedding_model, config)

    dfs = dict(dfs)
    dfs["caption_top_terms"] = caption_terms
    dfs["comment_top_terms"] = comment_terms
    return dfs


def _extract_caption_terms(
    posts: pd.DataFrame | None,
    nlp: Any,
    embedding_model: Any,
    config: Config,
) -> pd.DataFrame:
    if posts is None or posts.empty:
        return pd.DataFrame(columns=["term", "relevancia", "count"])

    texts = posts["caption"].fillna("").tolist()
    return extract_top_terms(texts, nlp, embedding_model, config.nlp_top_terms_limit)


def _extract_comment_terms(
    comments: pd.DataFrame | None,
    nlp: Any,
    embedding_model: Any,
    config: Config,
) -> pd.DataFrame:
    if comments is None or comments.empty:
        return pd.DataFrame(columns=["term", "relevancia", "count"])

    texts = comments["text"].fillna("").tolist()
    return extract_top_terms(texts, nlp, embedding_model, config.nlp_top_terms_limit)
