from typing import Any

import pandas as pd

from social_media.src.config import Config
from social_media.src.dependencies import Dependencies
from social_media.src.nlp.sentiment_terms import extract_sentiment_terms


def nlp_sentiment_terms_step(
    dfs: dict[str, pd.DataFrame], config: Config, deps: Dependencies
) -> dict[str, pd.DataFrame]:
    """Gera termos mais frequentes por sentimento."""
    comments = dfs.get("comments")

    if comments is None or comments.empty:
        dfs = dict(dfs)
        dfs["sentiment_term_comparison"] = pd.DataFrame(
            columns=["term", "sentiment", "count"]
        )
        return dfs

    nlp = deps.get_spacy_nlp()
    terms_df = extract_sentiment_terms(
        comments, nlp, config.nlp_sentiment_terms_limit
    )

    dfs = dict(dfs)
    dfs["sentiment_term_comparison"] = terms_df
    return dfs
