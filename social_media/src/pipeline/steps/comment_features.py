import logging
from typing import Callable

import pandas as pd

from social_media.src.config import Config
from social_media.src.dependencies import Dependencies
from social_media.src.domain.sentiment import SentimentResult
from social_media.src.metrics.comment import is_qualified, is_question, word_count

logger = logging.getLogger(__name__)


def comment_features_step(
    dfs: dict[str, pd.DataFrame], config: Config, deps: Dependencies
) -> dict[str, pd.DataFrame]:
    """Adiciona features de comentário e sentimento ao DataFrame `comments`."""
    comments = dfs["comments"].copy()

    comments["word_count"] = word_count(comments["text"])
    comments["is_qualified"] = is_qualified(
        comments["word_count"], config.qualified_comment_min_words
    )
    comments["is_question"] = is_question(comments["text"])

    if comments.empty:
        comments["sentiment_label"] = pd.Series(dtype="object")
        comments["sentiment_score"] = pd.Series(dtype="float64")
    else:
        analyzer = deps.get_sentiment_analyzer()
        sentiment_results = comments["text"].apply(
            lambda text: _safe_analyze(text, analyzer)
        )
        comments["sentiment_label"] = sentiment_results.apply(lambda r: r.label)
        comments["sentiment_score"] = sentiment_results.apply(lambda r: r.score)

    dfs = dict(dfs)
    dfs["comments"] = comments
    return dfs


def _safe_analyze(
    text: str, analyzer: Callable[[str], SentimentResult]
) -> SentimentResult:
    try:
        return analyzer(text)
    except Exception as exc:
        logger.exception(
            "Falha ao analisar sentimento do comentário: %s", exc, extra={"text": text}
        )
        return SentimentResult(label="neutro", score=0.5)
